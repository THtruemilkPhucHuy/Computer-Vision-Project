from collections import deque
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
import csv
import io
import time

import av
import cv2
import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import VideoProcessorBase, webrtc_streamer

from predict import predict


# =========================================================
# 1. CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Wildfire Intelligence | Live Camera",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT = BASE_DIR / "checkpoints" / "best_model.pth"
HISTORY_LIMIT = 500

# The class names are expected to be returned by predict.py.
# Examples: Fire, Smoke, Neutral (case-insensitive matching is used).


# =========================================================
# 2. STYLE
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
.stApp {
    background:
      radial-gradient(circle at 5% 0%, rgba(249,115,22,.12), transparent 28%),
      radial-gradient(circle at 95% 5%, rgba(239,68,68,.09), transparent 25%),
      var(--background-color);
}
.block-container { max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem; }
.hero {
    padding: 30px; border-radius: 22px; color: white; margin-bottom: 22px;
    background: linear-gradient(115deg, #7c2d12, #c2410c, #991b1b);
    box-shadow: 0 12px 35px rgba(127,29,29,.20);
}
.hero h1 { color: white; font-size: 36px; font-weight: 800; margin: 5px 0; }
.hero p { color: #fed7aa; margin-bottom: 0; }
.metric-card {
    padding: 17px; border-radius: 16px;
    border: 1px solid rgba(148,163,184,.25);
    background: var(--secondary-background-color); min-height: 105px;
}
.metric-label { font-size: 12px; opacity: .72; letter-spacing: .5px; }
.metric-value { font-size: 29px; font-weight: 800; margin-top: 7px; }
.section-title { font-size: 22px; font-weight: 800; margin: 22px 0 12px; }
div[data-testid="stMetric"] { background: var(--secondary-background-color);
    border: 1px solid rgba(148,163,184,.2); padding: 12px; border-radius: 14px; }
.stButton > button { border-radius: 11px; min-height: 42px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. SHARED CAMERA PROCESSOR
# =========================================================
class WildfireCameraProcessor(VideoProcessorBase):
    """Receives browser webcam frames and annotates them with model results."""

    def __init__(self):
        self.lock = Lock()
        self.last_inference = 0.0
        self.interval = 0.75
        self.label = "Waiting for camera"
        self.confidence = 0.0
        self.probs = {}
        self.error = None
        self.last_latency = 0.0
        self.total_predictions = 0
        self.counts = {"Fire": 0, "Smoke": 0, "Neutral": 0, "Other": 0}
        self.history = deque(maxlen=HISTORY_LIMIT)
        self.enabled = True

    def configure(self, interval):
        with self.lock:
            self.interval = max(0.2, float(interval))

    def snapshot(self):
        with self.lock:
            return {
                "label": self.label,
                "confidence": self.confidence,
                "probs": dict(self.probs),
                "error": self.error,
                "latency": self.last_latency,
                "total": self.total_predictions,
                "counts": dict(self.counts),
                "history": list(self.history),
            }

    @staticmethod
    def _class_bucket(label):
        value = str(label).strip().lower()
        if "fire" in value or "flame" in value:
            return "Fire"
        if "smoke" in value:
            return "Smoke"
        if "neutral" in value or "normal" in value or "no_fire" in value:
            return "Neutral"
        return "Other"

    def _infer(self, rgb_frame):
        temp_path = None
        started = time.perf_counter()
        try:
            image = Image.fromarray(rgb_frame).convert("RGB")
            with NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                temp_path = tmp.name
            image.save(temp_path, format="JPEG", quality=88)

            # Uses the same prediction function and checkpoint as app.py.
            label, confidence, probs = predict(str(temp_path), str(CHECKPOINT))

            label = str(label)
            confidence = float(confidence)
            probs = {str(k): float(v) for k, v in (probs or {}).items()}
            elapsed = time.perf_counter() - started
            bucket = self._class_bucket(label)

            with self.lock:
                self.label = label
                self.confidence = confidence
                self.probs = probs
                self.error = None
                self.last_latency = elapsed
                self.total_predictions += 1
                self.counts[bucket] = self.counts.get(bucket, 0) + 1
                self.history.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "label": label,
                    "bucket": bucket,
                    "confidence": confidence,
                    "latency": elapsed,
                })
        except Exception as exc:
            with self.lock:
                self.error = f"{type(exc).__name__}: {exc}"
                self.last_latency = time.perf_counter() - started
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        now = time.monotonic()

        should_infer = False
        with self.lock:
            if self.enabled and (now - self.last_inference >= self.interval):
                self.last_inference = now
                should_infer = True

        if should_infer and CHECKPOINT.exists():
            # Inference is performed on a copy so the camera frame can be annotated.
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._infer(rgb)

        state = self.snapshot()
        label = state["label"]
        bucket = self._class_bucket(label)

        if bucket == "Fire":
            color = (40, 40, 235)
            tag = "FIRE DETECTED"
        elif bucket == "Smoke":
            color = (0, 165, 255)
            tag = "SMOKE DETECTED"
        elif bucket == "Neutral":
            color = (70, 180, 70)
            tag = "NEUTRAL"
        else:
            color = (220, 220, 220)
            tag = "ANALYZING"

        # Readable overlay with a dark background.
        cv2.rectangle(image, (12, 12), (min(image.shape[1] - 12, 570), 105), (18, 24, 34), -1)
        cv2.putText(image, tag, (25, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2, cv2.LINE_AA)
        cv2.putText(
            image,
            f"{label} | Confidence: {state['confidence']:.1%}",
            (25, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (245, 245, 245), 2, cv2.LINE_AA
        )
        cv2.putText(
            image,
            f"Inference: {state['latency']:.2f}s",
            (25, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (190, 200, 210), 1, cv2.LINE_AA
        )

        return av.VideoFrame.from_ndarray(image, format="bgr24")


# =========================================================
# 4. HEADER + SIDEBAR
# =========================================================
st.markdown("""
<div class="hero">
  <div style="font-size:12px;letter-spacing:3px;color:#fed7aa;font-weight:700">
    COMPUTER VISION · RESNET50 · LIVE INFERENCE
  </div>
  <h1>🔥 Wildfire Intelligence — Realtime Camera</h1>
  <p>Phân tích trực tiếp hình ảnh từ camera laptop: Fire / Smoke / Neutral.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Camera Settings")
    inference_interval = st.slider(
        "Inference interval (seconds)", 0.2, 3.0, 0.75, 0.05,
        help="Giảm interval để phân tích thường xuyên hơn; tăng interval để giảm tải CPU/GPU."
    )
    show_probabilities = st.toggle("Show class probabilities", True)
    show_history = st.toggle("Show recent prediction log", True)
    st.divider()
    st.subheader("🧠 Model Status")
    if CHECKPOINT.exists():
        st.success("Checkpoint available")
        st.caption(str(CHECKPOINT))
    else:
        st.error("Không tìm thấy checkpoints/best_model.pth")
        st.caption("Hãy đặt checkpoint đúng vị trí trước khi chạy.")


# =========================================================
# 5. CAMERA STREAM
# =========================================================
st.markdown('<div class="section-title">📷 Live Laptop Camera</div>', unsafe_allow_html=True)

if not CHECKPOINT.exists():
    st.error("Không thể chạy nhận diện vì thiếu checkpoint.")
    st.stop()

st.info(
    "Nhấn START để cấp quyền camera cho trình duyệt. "
    "Nếu được hỏi, hãy chọn camera laptop và cho phép truy cập."
)

ctx = webrtc_streamer(
    key="wildfire-live-camera",
    video_processor_factory=WildfireCameraProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
    rtc_configuration={"iceServers": []},
)

processor = ctx.video_processor

if processor is not None:
    processor.configure(inference_interval)

# Refresh dashboard values periodically; the video itself is streamed independently.
st_autorefresh(interval=1000, key="wildfire_live_refresh")

if processor is None or not ctx.state.playing:
    st.caption("Camera đang dừng. Nhấn START để bắt đầu.")
    st.stop()

state = processor.snapshot()


# =========================================================
# 6. LIVE METRICS
# =========================================================
st.markdown('<div class="section-title">📊 Realtime Analysis Dashboard</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
metrics = [
    (m1, "TOTAL PREDICTIONS", state["total"]),
    (m2, "🔥 FIRE", state["counts"].get("Fire", 0)),
    (m3, "🌫️ SMOKE", state["counts"].get("Smoke", 0)),
    (m4, "🌿 NEUTRAL", state["counts"].get("Neutral", 0)),
]
for col, title, value in metrics:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{title}</div>'
            f'<div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True
        )

left, right = st.columns([1.3, 1])
with left:
    st.subheader("Current prediction")
    bucket = processor._class_bucket(state["label"])
    if bucket == "Fire":
        st.error(f"🔥 FIRE — {state['label']}")
    elif bucket == "Smoke":
        st.warning(f"🌫️ SMOKE — {state['label']}")
    elif bucket == "Neutral":
        st.success(f"🌿 NEUTRAL — {state['label']}")
    else:
        st.info(state["label"])
    st.metric("Confidence", f"{state['confidence']:.2%}")
    st.metric("Inference time", f"{state['latency']:.3f} s")
with right:
    st.subheader("Model probabilities")
    if show_probabilities and state["probs"]:
        for name, value in state["probs"].items():
            st.progress(max(0.0, min(1.0, value)), text=f"{name}: {value:.2%}")
    elif show_probabilities:
        st.caption("Đang chờ kết quả dự đoán đầu tiên.")
    if state["error"]:
        st.error(f"Inference error: {state['error']}")


# =========================================================
# 7. HISTORY + CSV EXPORT
# =========================================================
st.markdown("---")
st.markdown('<div class="section-title">🧾 Prediction History</div>', unsafe_allow_html=True)

history = state["history"]
if show_history and history:
    st.dataframe(
        [
            {
                "Time": row["time"],
                "Prediction": row["label"],
                "Class": row["bucket"],
                "Confidence": f"{row['confidence']:.2%}",
                "Inference (s)": round(row["latency"], 3),
            }
            for row in reversed(history[-30:])
        ],
        use_container_width=True,
        hide_index=True,
    )
elif show_history:
    st.caption("Chưa có bản ghi. Hãy đợi camera phân tích frame đầu tiên.")

if history:
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=["time", "label", "bucket", "confidence", "latency"]
    )
    writer.writeheader()
    writer.writerows(history)
    st.download_button(
        "⬇️ Download realtime CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="wildfire_realtime_camera_log.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("---")
st.caption(
    "🔥 Wildfire Intelligence | ResNet50 | Realtime webcam classification. "
    "Đây là công cụ phân loại học thuật, không thay thế hệ thống cảnh báo cháy chuyên nghiệp."
)
