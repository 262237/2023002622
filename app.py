"""Local image-upload demonstration. Run: streamlit run app.py"""
import json
from pathlib import Path
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from predict import load_artifact, predict_image

st.set_page_config(page_title='PlantHealth | Leaf classifier', page_icon='🌿', layout='centered')
st.title('🌿 PlantHealth')
st.write('Identify patterns in pepper, potato, and tomato leaf images with a trained image classifier.')
directory = Path('artifacts/planthealth')
if not (directory / 'model.keras').exists() or not (directory / 'config.json').exists():
    st.info('A trained model is required. Follow the training steps in README.md, then restart this app.')
    st.stop()

@st.cache_resource
def cached_model(path, modified):
    return load_artifact(path)

model, config = cached_model(str(directory), (directory / 'model.keras').stat().st_mtime_ns)
metrics_path = directory / 'metrics.json'
if metrics_path.exists():
    metrics = json.loads(metrics_path.read_text())
    st.caption(f"Experiment: {len(config['classes'])} classes · {metrics['test_images']} held-out images · {metrics['test_accuracy']:.1%} test accuracy")
st.warning('Educational prototype tested on PlantVillage images. Field-photo performance is unverified; this is not a crop-treatment recommendation.')
uploaded = st.file_uploader('Upload a clear leaf photo', type=['jpg', 'jpeg', 'png'])
examples_path = directory / 'test_predictions.json'
examples = json.loads(examples_path.read_text()) if examples_path.exists() else []
available = [row for row in examples if (Path('data/plantvillage') / row['path']).is_file()]
example_choice = st.selectbox('Or try a held-out test image', ['Select an example'] + [row['path'] for row in available])
source_image = uploaded if uploaded is not None else (Path('data/plantvillage') / example_choice if example_choice != 'Select an example' else None)
if source_image is not None:
    try:
        with Image.open(source_image) as source:
            display = ImageOps.exif_transpose(source).convert('RGB')
        st.image(display, caption='Selected leaf', width=350)
        if uploaded is not None:
            uploaded.seek(0)
        else:
            truth = next(row['actual'] for row in available if row['path'] == example_choice)
            st.caption('Dataset label: ' + truth.replace('___', ' — ').replace('_', ' '))
        with st.spinner('Analyzing image…'):
            results = predict_image(source_image, model, config)
        label = results[0]['class'].replace('___', ' — ').replace('_', ' ')
        st.subheader(label)
        st.caption('Model scores rank the known classes; they do not measure diagnostic certainty. Unrelated images can still receive high scores.')
        for item in results:
            st.write(f"{item['class'].replace('___', ' — ').replace('_', ' ')}: {item['score']:.1%}")
            st.progress(min(1.0, max(0.0, item['score'])))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        st.error('This file could not be processed. Please upload a valid JPG or PNG image.')
with st.expander('How it works and limitations'):
    st.write(config['architecture'])
    st.write('Images are resized to the model input size. A pretrained CNN extracts visual features, and a trained classification head assigns scores to the known classes.')
    for limitation in config['limitations']:
        st.write('• ' + limitation)
