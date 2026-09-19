"""Use the same preprocessing and class order for CLI and web inference."""
import argparse
import json
from pathlib import Path
import numpy as np
from plant_data import image_array

def load_artifact(directory):
    import tensorflow as tf
    directory = Path(directory)
    config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
    model = tf.keras.models.load_model(directory / 'model.keras', compile=False)
    if model.output_shape[-1] != len(config['classes']):
        raise ValueError('Model output and class mapping do not match.')
    return model, config

def predict_image(source, model, config, top_k=3):
    pixels = image_array(source, config['image_size'])[None]
    scores = model(pixels, training=False).numpy()[0]
    return [{'class': config['classes'][int(index)], 'score': float(scores[index])} for index in np.argsort(scores)[::-1][:top_k]]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--model-dir', type=Path, default=Path('artifacts/planthealth'))
    args = parser.parse_args()
    model, config = load_artifact(args.model_dir)
    print(json.dumps(predict_image(args.image, model, config), indent=2))
