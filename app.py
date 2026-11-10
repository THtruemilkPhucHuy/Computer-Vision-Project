from pathlib import Path
import streamlit as st
import torch
from PIL import Image
from predict import predict

st.set_page_config(page_title='Wildfire Detection',page_icon='🔥',layout='centered')
st.title('🔥 Wildfire Detection')
st.write('ResNet50 image classifier: Fire / Neutral / Smoke')
checkpoint=Path('checkpoints/best_model.pth')
if not checkpoint.exists():
    st.warning('Chưa có model. Hãy đặt dataset vào Wildfire-smoke/ rồi chạy run_train.bat trước.')
    st.stop()
try:
    _meta = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if _meta.get('dataset_type') == 'synthetic_demo':
        st.warning('Mô hình hiện dùng DATASET MÔ PHỎNG để kiểm tra phần mềm. Không dùng kết quả này để cảnh báo cháy rừng thực tế.')
except Exception:
    pass
file=st.file_uploader('Tải ảnh cần kiểm tra',type=['jpg','jpeg','png','bmp','webp'])
if file:
    image=Image.open(file).convert('RGB')
    st.image(image,caption='Ảnh đầu vào',use_container_width=True)
    with st.spinner('Đang phân tích...'):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg',delete=False) as f:
            image.save(f.name); tmp=f.name
        try: label,confidence,probs=predict(tmp,str(checkpoint))
        finally: Path(tmp).unlink(missing_ok=True)
    st.subheader(f'Kết quả: {label}')
    st.metric('Độ tin cậy',f'{confidence:.2%}')
    st.write('Xác suất từng lớp')
    for name,value in probs.items(): st.progress(value,text=f'{name}: {value:.2%}')
    st.caption('Đây là mô hình phân loại ảnh học thuật, không thay thế hệ thống cảnh báo cháy chuyên dụng.')
