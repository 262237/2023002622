"""Generate the measured-results report and resume sentence from verified artifacts."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
directory = root / 'artifacts/planthealth'
metrics = json.loads((directory / 'metrics.json').read_text())
config = json.loads((directory / 'config.json').read_text())
verification = json.loads((directory / 'verification.json').read_text())
if verification['status'] != 'passed':
    raise SystemExit('Verification must pass before publishing local results.')
counts = metrics['split_counts']
report = metrics['classification_report']
weakest = sorted(config['classes'], key=lambda name: report[name]['recall'])[:3]
errors = [row for row in json.loads((directory / 'test_predictions.json').read_text()) if row['actual'] != row['predicted']]
weak_rows = '\n'.join(f"| {name} | {report[name]['precision']:.1%} | {report[name]['recall']:.1%} | {report[name]['f1-score']:.3f} | {int(report[name]['support'])} |" for name in weakest)
error_rows = '\n'.join(f"- `{row['path']}`: actual **{row['actual']}**, predicted **{row['predicted']}** (model score {row['score']:.1%})." for row in errors[:5])
resume = f"Built a 15-class plant-leaf classifier using MobileNetV2 transfer learning and Streamlit, achieving {metrics['test_accuracy']:.2%} accuracy and {metrics['macro_f1']:.3f} macro F1 on {metrics['test_images']} held-out images from a {sum(counts.values()):,}-image PlantVillage sample."
text = f'''# Verified experiment results

## Scope

This is a completed local educational prototype: downloaded dataset, trained/exported model, independent saved-model evaluation, and tested Streamlit demonstration. It is not a field-validated diagnostic system or a public deployment.

Source: https://github.com/spMohanty/PlantVillage-Dataset

Pinned revision: `{config['data_source']['revision']}`. Sampling: up to 200 images per class, seed 42. All images in this run were valid and no exact decoded-pixel duplicates were found in the audit.

## Measured results

| Measure | Result |
|---|---:|
| Classes | {len(config['classes'])} |
| Original sampled images | {sum(counts.values()):,} |
| Training images | {counts['train']:,} |
| Validation images | {counts['validation']:,} |
| Held-out test images | {counts['test']:,} |
| Test accuracy | {metrics['test_accuracy']:.2%} |
| Macro F1 | {metrics['macro_f1']:.4f} |
| Weighted F1 | {metrics['weighted_f1']:.4f} |
| Majority-class test baseline | {metrics['majority_class_baseline']:.2%} |
| Best epoch (validation loss) | {metrics['best_epoch']} |
| Epochs run | {metrics['epochs_run']} |
| Misclassified test images | {len(errors)} |

Each training image also produced one augmented feature vector; augmentation did not increase the number of independent source images. The ImageNet backbone was frozen, and only the dense head was trained. Test data was used after validation-based epoch selection.

## Error analysis

The three lowest-recall classes in this test sample:

| Class | Precision | Recall | F1 | Test images |
|---|---:|---:|---:|---:|
{weak_rows}

Examples to inspect before the interview (first errors in the recorded deterministic test order):

{error_rows or 'No misclassified test images in this run.'}

![Learning curves](artifacts/planthealth/learning_curves.png)

![Confusion matrix](artifacts/planthealth/confusion_matrix.png)

![Prediction examples](artifacts/planthealth/prediction_examples.png)

## Verification

- Independent evaluation of the exported model reproduced the recorded test accuracy.
- All {verification['tests_run']} software/integration tests passed with none skipped, including the Streamlit held-out-image prediction flow.
- Saved-model reload matched the training pipeline's probability vector on a test example.
- Notebook code syntax passed. The notebook is a runnable interface to the maintained modules; it was not separately retrained.
- The environment dependency check passed.

Full machine-readable evidence: `metrics.json`, `verification.json`, `split.json`, and `test_predictions.json` under `artifacts/planthealth`. Model SHA-256: `{verification['model_sha256']}`.

## Resume sentence

{resume}

Use the sentence only if you can explain and demonstrate the work. Describe the supplied notebook as the starting point and your own contributions accurately. The old 94.95% notebook result is not used or claimed here.

The sample is relatively balanced and has controlled backgrounds. This small image-level test is not evidence of farm-level generalization; related leaves and near-duplicates may remain. Model scores are not calibrated diagnostic confidence.
'''
(root / 'RESULTS.md').write_text(text, encoding='utf-8')
print(resume)
