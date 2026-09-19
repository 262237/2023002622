"""Independently evaluate the exported model on its recorded test split."""
import argparse
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report
from plant_data import image_array
from predict import load_artifact

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/plantvillage'))
    parser.add_argument('--model-dir', type=Path, default=Path('artifacts/planthealth'))
    args = parser.parse_args()
    model, config = load_artifact(args.model_dir)
    split = json.loads((args.model_dir / 'split.json').read_text())
    rows = [r for r in split['records'] if r['split'] == 'test']
    predicted = []
    for start in range(0, len(rows), 32):
        images = np.stack([image_array(args.data / r['path'], config['image_size']) for r in rows[start:start + 32]])
        predicted.extend(model(images, training=False).numpy().argmax(axis=1).tolist())
    actual = [r['label'] for r in rows]
    report = classification_report(actual, predicted, labels=np.arange(len(config['classes'])), target_names=config['classes'], output_dict=True, zero_division=0)
    measured = float(np.mean(np.asarray(actual) == predicted))
    recorded = json.loads((args.model_dir / 'metrics.json').read_text())
    np.testing.assert_allclose(measured, recorded['test_accuracy'], atol=1e-12)
    print(json.dumps({'test_accuracy': measured, 'macro_f1': report['macro avg']['f1-score'], 'test_images': len(rows), 'recorded_accuracy_matches': True}, indent=2))

if __name__ == '__main__':
    main()
