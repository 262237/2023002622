"""Train a MobileNetV2 transfer classifier and evaluate the selected checkpoint once."""
import argparse
import json
import os
import textwrap
from pathlib import Path
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('KERAS_HOME', str(Path(__file__).resolve().parent / '.cache' / 'keras'))
import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.utils.class_weight import compute_class_weight
from plant_data import make_split, image_array

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/plantvillage'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/planthealth'))
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--image-size', type=int, default=160)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if args.epochs < 1 or args.image_size < 32:
        parser.error('epochs >= 1 and image-size >= 32 are required')
    source_path = args.data / 'source.json'
    if source_path.exists() and json.loads(source_path.read_text())['status'] != 'complete':
        raise ValueError('Dataset download is incomplete; rerun download_data.py first.')
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Output directory must be new or empty; preserve prior experiments.')
    args.output.mkdir(parents=True, exist_ok=True)
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()
    split = make_split(args.data, args.seed)
    (args.output / 'split.json').write_text(json.dumps(split, indent=2))
    classes = split['classes']
    print(f'Classes: {len(classes)}; split: {split["counts"]}', flush=True)
    backbone = tf.keras.applications.MobileNetV2(input_shape=(args.image_size, args.image_size, 3), include_top=False, weights='imagenet', pooling='avg')
    backbone.trainable = False
    inputs = tf.keras.Input((args.image_size, args.image_size, 3), name='rgb_pixels_0_255')
    normalized = tf.keras.layers.Rescaling(1 / 127.5, offset=-1)(inputs)
    extractor = tf.keras.Model(inputs, backbone(normalized, training=False), name='frozen_imagenet_features')
    augmentation = tf.keras.Sequential([tf.keras.layers.RandomFlip('horizontal_and_vertical', seed=args.seed), tf.keras.layers.RandomRotation(.1, seed=args.seed + 1)])

    def features_for(name, augment=False):
        rows = [r for r in split['records'] if r['split'] == name]
        features, labels = [], []
        for start in range(0, len(rows), 32):
            batch = rows[start:start + 32]
            images = np.stack([image_array(args.data / r['path'], args.image_size) for r in batch])
            features.append(extractor(images, training=False).numpy())
            labels.extend(r['label'] for r in batch)
            if augment:
                features.append(extractor(augmentation(images, training=True), training=False).numpy())
                labels.extend(r['label'] for r in batch)
            if start % 320 == 0:
                print(f'{name}: extracted {min(start + 32, len(rows))}/{len(rows)}', flush=True)
        return np.concatenate(features), np.asarray(labels, dtype=np.int32)

    x_train, y_train = features_for('train', augment=True)
    x_val, y_val = features_for('validation')
    head = tf.keras.Sequential([tf.keras.Input((1280,)), tf.keras.layers.Dense(128, activation='relu'), tf.keras.layers.Dropout(.35), tf.keras.layers.Dense(len(classes), activation='softmax')], name='classification_head')
    head.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    weights = compute_class_weight('balanced', classes=np.arange(len(classes)), y=y_train)
    history = head.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=args.epochs, batch_size=32,
                       class_weight=dict(enumerate(weights)), verbose=2,
                       callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True), tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', patience=3, factor=.5, min_lr=1e-5)])
    model = tf.keras.Model(inputs, head(extractor(inputs)), name='planthealth_mobilenetv2')
    model.save(args.output / 'model.keras')
    summary_lines = []
    model.summary(print_fn=lambda line, **kwargs: summary_lines.append(line))
    (args.output / 'model_summary.txt').write_text('\n'.join(summary_lines), encoding='utf-8')
    # The held-out test split is only used after model selection is complete.
    x_test, y_test = features_for('test')
    probabilities = head.predict(x_test, verbose=0)
    predictions = probabilities.argmax(axis=1)
    report = classification_report(y_test, predictions, labels=np.arange(len(classes)), target_names=classes, output_dict=True, zero_division=0)
    metrics = {'test_accuracy': float(np.mean(predictions == y_test)), 'macro_f1': report['macro avg']['f1-score'], 'weighted_f1': report['weighted avg']['f1-score'], 'test_images': len(y_test), 'majority_class_baseline': float(np.bincount(y_test).max() / len(y_test)), 'best_epoch': int(np.argmin(history.history['val_loss']) + 1), 'epochs_run': len(history.history['loss']), 'split_counts': split['counts'], 'classification_report': report}
    config = {'architecture': 'Frozen ImageNet MobileNetV2 + Dense(128) + Dropout(0.35) + Softmax', 'image_size': args.image_size, 'classes': classes, 'seed': args.seed, 'tensorflow': tf.__version__, 'input': 'RGB float pixels in [0,255]; preprocessing is inside saved model', 'augmentation': 'One extra random flip/rotation view per training image, cached as features; none on validation or test', 'data_source': json.loads((args.data / 'source.json').read_text()) if (args.data / 'source.json').exists() else {'local_directory': str(args.data)}, 'limitations': ['Controlled-background dataset; field performance unmeasured', 'Softmax scores are not calibrated probabilities of correctness', 'Exact duplicates removed; near-duplicate/leaf-level grouping unavailable', 'Random image-level split, not farm/plant/source-level split']}
    for filename, value in [('metrics.json', metrics), ('config.json', config), ('history.json', history.history)]:
        (args.output / filename).write_text(json.dumps(value, indent=2), encoding='utf-8')
    test_rows = [r for r in split['records'] if r['split'] == 'test']
    (args.output / 'test_predictions.json').write_text(json.dumps([{'path': r['path'], 'actual': classes[int(y)], 'predicted': classes[int(p)], 'score': float(prob.max())} for r, y, p, prob in zip(test_rows, y_test, predictions, probabilities)], indent=2))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, key in zip(axes, ['loss', 'accuracy']):
        ax.plot(np.arange(1, len(history.history[key]) + 1), history.history[key], label='Training (augmented)')
        ax.plot(np.arange(1, len(history.history[key]) + 1), history.history['val_' + key], label='Validation')
        ax.set(xlabel='Epoch', ylabel=key.title()); ax.legend()
    fig.tight_layout(); fig.savefig(args.output / 'learning_curves.png', dpi=140); plt.close(fig)
    fig, ax = plt.subplots(figsize=(15, 13))
    ConfusionMatrixDisplay(confusion_matrix(y_test, predictions, labels=np.arange(len(classes))), display_labels=classes).plot(ax=ax, xticks_rotation=90, colorbar=False, cmap='Greens')
    fig.tight_layout(); fig.savefig(args.output / 'confusion_matrix.png', dpi=130); plt.close(fig)
    fig, axes = plt.subplots(3, 3, figsize=(13, 13))
    example_indices = np.random.default_rng(args.seed).choice(len(test_rows), min(9, len(test_rows)), replace=False)
    for ax in axes.flat:
        ax.axis('off')
    for ax, index in zip(axes.flat, example_indices):
        ax.imshow(image_array(args.data / test_rows[index]['path'], args.image_size).astype('uint8'))
        actual = classes[int(y_test[index])].replace('___', ': ').replace('_', ' ')
        predicted = classes[int(predictions[index])].replace('___', ': ').replace('_', ' ')
        caption = '\n'.join(textwrap.wrap('Actual: ' + actual, 34)) + '\n' + '\n'.join(textwrap.wrap('Predicted: ' + predicted, 34))
        ax.set_title(caption, fontsize=9, color='darkgreen' if predictions[index] == y_test[index] else 'firebrick')
    fig.tight_layout(); fig.savefig(args.output / 'prediction_examples.png', dpi=130); plt.close(fig)
    # Verify the exported end-to-end model reproduces feature/head predictions.
    restored = tf.keras.models.load_model(args.output / 'model.keras', compile=False)
    sample = image_array(args.data / test_rows[0]['path'], args.image_size)[None]
    np.testing.assert_allclose(restored(sample, training=False).numpy()[0], probabilities[0], atol=1e-5)
    print(json.dumps({k: v for k, v in metrics.items() if k != 'classification_report'}, indent=2), flush=True)
    print('PASS: saved-model reload matches evaluation prediction.', flush=True)

if __name__ == '__main__':
    main()
