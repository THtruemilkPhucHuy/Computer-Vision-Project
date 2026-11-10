
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tempfile import NamedTemporaryFile
import streamlit as st
import torch
from PIL import Image, ImageOps, UnidentifiedImageError
import io
import csv
import time

from predict import predict


# =========================================================
# 1. CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Wildfire Intelligence",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

CHECKPOINT = Path("checkpoints/best_model.pth")

SUPPORTED_TYPES = [
    "jpg", "jpeg", "png", "bmp", "webp", "tif", "tiff"
]


# =========================================================
# 2. PREMIUM CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 5% 0%, rgba(249,115,22,.12), transparent 28%),
        radial-gradient(circle at 95% 5%, rgba(239,68,68,.09), transparent 25%),
        var(--background-color);
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 35px;
    border-radius: 22px;
    background: linear-gradient(
        115deg,
        #7c2d12,
        #c2410c,
        #991b1b
    );
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 12px 35px rgba(127,29,29,.2);
}

.hero h1 {
    color: white;
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 8px;
}

.hero p {
    color: #fed7aa;
    font-size: 15px;
}

.metric-card {
    padding: 20px;
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,.25);
    background: var(--secondary-background-color);
    min-height: 115px;
}

.metric-label {
    font-size: 13px;
    opacity: .7;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    margin-top: 8px;
}

.section-title {
    font-size: 23px;
    font-weight: 750;
    margin-top: 20px;
    margin-bottom: 15px;
}

div[data-testid="stFileUploader"] {
    border: 1px dashed #ea580c;
    border-radius: 15px;
    padding: 12px;
    background: rgba(249,115,22,.04);
}

.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    min-height: 45px;
}

div[data-testid="stProgressBar"] {
    border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. HEADER
# =========================================================


st.markdown(
    """
<div class="hero">
<div style="font-size:12px; letter-spacing:3px; color:#fed7aa; font-weight:700;">
COMPUTER VISION · RESNET50
</div>
<h1>🔥 Wildfire Intelligence</h1>
<p>
AI-powered wildfire detection system.
Intelligent image classification:
Fire / Neutral / Smoke.
</p>
</div>
""",
    unsafe_allow_html=True
)



# =========================================================
# 4. SIDEBAR
# =========================================================

with st.sidebar:

    st.title("⚙️ Settings")

    st.caption("Application configuration")

    workers = st.slider(
        "Parallel workers",
        min_value=1,
        max_value=8,
        value=2
    )

    show_images = st.toggle(
        "Show image previews",
        value=True
    )

    show_probabilities = st.toggle(
        "Show class probabilities",
        value=True
    )

    st.divider()

    st.subheader("🧠 Model Status")

    if CHECKPOINT.exists():

        st.success("Model available")

        st.caption(str(CHECKPOINT))

        try:
            metadata = torch.load(
                CHECKPOINT,
                map_location="cpu",
                weights_only=True
            )

            if (
                isinstance(metadata, dict)
                and metadata.get("dataset_type") == "synthetic_demo"
            ):
                st.warning(
                    "Model đang sử dụng dataset mô phỏng. "
                    "Không dùng cho cảnh báo cháy thực tế."
                )

        except Exception:
            pass

    else:

        st.error("Model not found")

        st.info(
            "Hãy train model trước bằng run_train.bat."
        )


# =========================================================
# 5. HELPER FUNCTIONS
# =========================================================

def analyze_image(uploaded_file):

    result = {
        "name": uploaded_file.name,
        "label": "Error",
        "confidence": 0.0,
        "probs": {},
        "error": None,
        "image_bytes": uploaded_file.getvalue(),
        "elapsed": 0.0
    }

    start_time = time.perf_counter()
    temp_path = None

    try:

        image = Image.open(
            io.BytesIO(result["image_bytes"])
        )

        image = ImageOps.exif_transpose(image).convert("RGB")

        with NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        ) as temp:

            temp_path = temp.name

            image.save(
                temp_path,
                format="JPEG",
                quality=95
            )

        # CALL TRAINED MODEL
        label, confidence, probs = predict(
            temp_path,
            str(CHECKPOINT)
        )

        result["label"] = str(label)

        result["confidence"] = float(confidence)

        result["probs"] = {
            str(name): float(value)
            for name, value in probs.items()
        }

    except (UnidentifiedImageError, OSError, ValueError) as e:

        result["error"] = f"Image error: {e}"

    except Exception as e:

        result["error"] = f"{type(e).__name__}: {e}"

    finally:

        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

        result["elapsed"] = (
            time.perf_counter() - start_time
        )

    return result


def unique_files(files):

    output = []
    seen = set()

    for file in files:

        content = file.getvalue()

        signature = (
            file.name,
            len(content),
            hash(content)
        )

        if signature not in seen:

            seen.add(signature)
            output.append(file)

    return output


def percentage(value):

    return f"{value:.2%}"


# =========================================================
# 6. IMAGE UPLOAD
# =========================================================

st.markdown(
    '<div class="section-title">📂 Image Upload Center</div>',
    unsafe_allow_html=True
)

st.caption(
    "Upload multiple images or select an entire folder."
)

col1, col2 = st.columns(2, gap="large")

with col1:

    st.markdown("### 🖼️ Multiple Images")

    uploaded_images = st.file_uploader(
        "Select image files",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        key="multiple_images"
    )

with col2:

    st.markdown("### 📁 Image Folder")

    try:

        folder_images = st.file_uploader(
            "Select an entire folder",
            type=SUPPORTED_TYPES,
            accept_multiple_files="directory",
            key="folder_images"
        )

        if not isinstance(folder_images, list):
            folder_images = []

    except Exception:

        folder_images = []

        st.warning(
            "Không hỗ trợ chọn thư mục. "
            "Hãy cập nhật Streamlit bằng pip install -U streamlit."
        )


all_files = unique_files(
    list(uploaded_images or [])
    + list(folder_images or [])
)

total_images = len(all_files)


# =========================================================
# 7. DASHBOARD METRICS
# =========================================================

st.markdown("---")

m1, m2, m3 = st.columns(3)

with m1:

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TOTAL IMAGES</div>
        <div class="metric-value">{total_images}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PARALLEL WORKERS</div>
        <div class="metric-value">{workers}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:

    status = "READY" if CHECKPOINT.exists() else "NO MODEL"

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">MODEL STATUS</div>
        <div class="metric-value" style="font-size:23px">
            {status}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# 8. ANALYSIS BUTTON
# =========================================================

st.markdown(
    '<div class="section-title">⚡ Batch Image Analysis</div>',
    unsafe_allow_html=True
)

if total_images:

    with st.expander(
        f"View selected images ({total_images})",
        expanded=False
    ):

        for i, file in enumerate(all_files, 1):

            st.write(
                f"{i}. {file.name} "
                f"({len(file.getvalue()) / 1024:.1f} KB)"
            )


if not CHECKPOINT.exists():

    st.warning(
        "Không tìm thấy best_model.pth. "
        "Vui lòng train model trước."
    )

elif total_images == 0:

    st.info(
        "Hãy tải ảnh hoặc chọn thư mục ảnh để bắt đầu."
    )

else:

    if st.button(
        f"🔥 ANALYZE {total_images} IMAGES",
        type="primary",
        use_container_width=True
    ):

        results = [None] * total_images

        progress = st.progress(0)

        status_text = st.empty()

        completed = 0

        # PARALLEL IMAGE PROCESSING
        with ThreadPoolExecutor(
            max_workers=min(workers, total_images)
        ) as executor:

            futures = {
                executor.submit(
                    analyze_image,
                    file
                ): index

                for index, file in enumerate(all_files)
            }

            for future in as_completed(futures):

                index = futures[future]

                try:

                    results[index] = future.result()

                except Exception as e:

                    results[index] = {
                        "name": all_files[index].name,
                        "label": "Error",
                        "confidence": 0,
                        "probs": {},
                        "error": str(e),
                        "image_bytes": all_files[index].getvalue(),
                        "elapsed": 0
                    }

                completed += 1

                progress.progress(
                    completed / total_images
                )

                status_text.write(
                    f"Processing {completed}/{total_images}"
                )

        st.session_state["wildfire_results"] = results

        progress.empty()
        status_text.empty()

        st.success("Analysis completed successfully!")


# =========================================================
# 9. RESULT DASHBOARD
# =========================================================

results = st.session_state.get(
    "wildfire_results",
    []
)

if results:

    st.markdown("---")

    st.markdown(
        '<div class="section-title">📊 Analysis Dashboard</div>',
        unsafe_allow_html=True
    )

    valid_results = [
        r for r in results
        if not r["error"]
    ]

    error_results = [
        r for r in results
        if r["error"]
    ]

    fire_count = sum(
        "fire" in r["label"].lower()
        for r in valid_results
    )

    smoke_count = sum(
        "smoke" in r["label"].lower()
        for r in valid_results
    )

    neutral_count = sum(
        "neutral" in r["label"].lower()
        for r in valid_results
    )

    avg_confidence = (
        sum(r["confidence"] for r in valid_results)
        / len(valid_results)
        if valid_results else 0
    )

    # SUMMARY
    c1, c2, c3, c4 = st.columns(4)

    summary = [
        ("SUCCESS", len(valid_results)),
        ("🔥 FIRE", fire_count),
        ("🌫️ SMOKE", smoke_count),
        ("🌿 NEUTRAL", neutral_count)
    ]

    for col, (name, value) in zip(
        [c1, c2, c3, c4],
        summary
    ):

        with col:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{name}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.metric(
        "Average Confidence",
        percentage(avg_confidence)
    )

    if error_results:

        with st.expander(
            f"⚠️ {len(error_results)} images failed"
        ):

            for item in error_results:

                st.error(
                    f"{item['name']}: {item['error']}"
                )

    # FILTER
    labels = sorted({
        r["label"] for r in valid_results
    })

    selected_label = st.selectbox(
        "Filter prediction",
        ["All"] + labels
    )

    visible_results = [
        r for r in valid_results
        if selected_label == "All"
        or r["label"] == selected_label
    ]

    # IMAGE RESULT CARDS
    st.markdown("### 🖼️ Individual Image Results")

    for start in range(
        0,
        len(visible_results),
        2
    ):

        cols = st.columns(2)

        for col, item in zip(
            cols,
            visible_results[start:start + 2]
        ):

            with col:

                with st.container(border=True):

                    if show_images:

                        st.image(
                            item["image_bytes"],
                            use_container_width=True
                        )

                    label = item["label"]

                    if "fire" in label.lower():

                        st.error(f"🔥 {label}")

                    elif "smoke" in label.lower():

                        st.warning(f"🌫️ {label}")

                    else:

                        st.success(f"🌿 {label}")

                    st.metric(
                        "Confidence",
                        percentage(item["confidence"])
                    )

                    st.caption(
                        f"File: {item['name']}"
                    )

                    st.caption(
                        f"Processing time: {item['elapsed']:.2f}s"
                    )

                    if (
                        show_probabilities
                        and item["probs"]
                    ):

                        with st.expander(
                            "View class probabilities"
                        ):

                            for name, value in item["probs"].items():

                                st.progress(
                                    max(0, min(1, value)),
                                    text=f"{name}: {percentage(value)}"
                                )


    # =====================================================
    # 10. EXPORT CSV
    # =====================================================

    st.markdown("---")

    st.markdown("### 📥 Export Analysis Report")

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Filename",
        "Prediction",
        "Confidence",
        "Processing_Time",
        "Error"
    ])

    for item in results:

        writer.writerow([
            item["name"],
            item["label"],
            item["confidence"],
            item["elapsed"],
            item["error"] or ""
        ])

    st.download_button(
        "⬇️ Download CSV Report",
        data=output.getvalue().encode("utf-8-sig"),
        file_name="wildfire_analysis_report.csv",
        mime="text/csv",
        use_container_width=True
    )

    if st.button(
        "🧹 Clear Results",
        use_container_width=True
    ):

        st.session_state.pop(
            "wildfire_results",
            None
        )

        st.rerun()


# =========================================================
# 11. FOOTER
# =========================================================

st.markdown("---")

st.caption("""
🔥 Wildfire Intelligence | ResNet50 Deep Learning

Academic image classification system.
Not a replacement for professional wildfire monitoring
or emergency warning systems.
""")
