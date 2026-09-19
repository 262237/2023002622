# PlantHealth — Plant Leaf Disease Classification

A reproducible, local image-classification project for 15 pepper, potato, and tomato leaf classes. This extends the supplied PlantDiseaseDetectionEnhanced notebook with a corrected evaluation pipeline, transfer learning, saved model, and Streamlit demonstration.

**Verified result:** 91.53% held-out test accuracy and 0.9160 macro F1 on 295 test images from a 2,952-image sample. The saved model's independent evaluation and all four software/integration tests passed. See [RESULTS.md](RESULTS.md) for the experiment scope, error analysis, and resume wording, and [INTERVIEW_PREP.md](INTERVIEW_PREP.md) for the DS/ML interview guide.

## Dataset and provenance

Dataset: **PlantVillage**, original repository: https://github.com/spMohanty/PlantVillage-Dataset

Color images: https://github.com/spMohanty/PlantVillage-Dataset/tree/master/raw/color

The downloader selects the 15 pepper, potato, and tomato classes corresponding to the original notebook. Its default is **up to 200 images per class**, a reproducible sample suitable for a CPU experiment. This is not the full 20,638-image dataset used in the original notebook. A fixed seed determines the selected files; the source commit and original Git blob checksums are stored in `data/plantvillage/source.json`. Existing downloads are checksum-verified when resumed. `--max-per-class 0` downloads all images in these 15 classes into a separate directory. Consult the upstream repository for data terms and attribution before redistributing images.

## Quick start (Windows PowerShell)

Use Python 3.11–3.13 with the pinned dependencies. The verified local environment uses Python 3.13.7. Run commands from this folder.

`requirements-lock.txt` captures every installed package version for the local Windows/Python 3.13 run. Use it instead of `requirements.txt` when reproducing that exact environment; packages in the full lock may have narrower Python/platform support.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-compile -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

The repository includes the verified trained model and its class mapping, so retraining is not required to use the demo. Visit http://localhost:8501 and upload a JPG or PNG. The app runs locally; no public deployment or account is required. To enable the held-out example selector or reproduce evaluation, download the sampled dataset with `python download_data.py --max-per-class 200` using the project's virtual environment.

You can also run `launch_demo.ps1` from PowerShell. To use `PlantDiseaseDetection_Completed.ipynb` in a notebook editor, install `requirements-notebook.txt` and select the project's `.venv` kernel. The notebook calls the same modules, avoiding a second divergent implementation.

Command-line prediction:

```powershell
.\.venv\Scripts\python.exe predict.py "path/to/leaf.jpg"
```

Linux/macOS: use `python3 -m venv .venv`, then `.venv/bin/python` instead of the Windows executable. Internet is required for the public dataset and the first ImageNet-weight download when training. The verified `artifacts/planthealth/model.keras` checkpoint is included in Git; downloaded images, environments, caches, and other model checkpoints are excluded.

## Method

1. Validate images, apply EXIF orientation, and remove duplicates using a SHA-256 hash of decoded RGB pixels and dimensions. Conflicting labels for identical pixels fail loudly.
2. Split each class approximately 80% training, 10% validation, and 10% test with seed 42. Save every file assignment in `split.json`. Invalid images and duplicates are recorded.
3. Resize images to 160×160 and preprocess inside the exported model from RGB values [0,255] to [-1,1].
4. Extract frozen ImageNet MobileNetV2 features with global average pooling. For training only, extract one additional randomly flipped/rotated view per image. Cache feature vectors in memory to avoid repeated backbone computation.
5. Train Dense(128, ReLU), Dropout(0.35), and a 15-class softmax head with Adam and sparse categorical cross-entropy. Apply class weighting, reduce the learning rate when validation loss stalls, and restore the best validation-loss weights.
6. Evaluate the held-out test split once after model selection. Save test accuracy, macro/weighted F1, per-class precision/recall/F1, confusion matrix, learning curves, and per-image predictions.
7. Export the complete model as `model.keras`; verify that reloading it reproduces the evaluation prediction.

No test image is used to train the head or select its epoch. This image-level evaluation cannot exclude related leaves or near-duplicates; farm/plant-level generalization remains unmeasured. Fixed seeds improve reproducibility, but numerical behavior can vary by hardware/library version.

## Outputs

`artifacts/planthealth/` contains:

- `model.keras`: preprocessing, frozen CNN, and trained head.
- `metrics.json`: measured held-out test metrics and per-class report.
- `config.json`: class order, preprocessing, source provenance, and limitations.
- `split.json`: stable split membership and duplicate/invalid-file audit.
- `history.json`, `learning_curves.png`: training and validation history.
- `confusion_matrix.png`, `test_predictions.json`: detailed test evaluation.
- `prediction_examples.png`: nine randomly selected test images with matched labels/predictions.
- `model_summary.txt`: exported architecture and parameter counts.

`RESULTS.md` records the verified run once execution finishes. Do not reuse the original notebook's 94.95% number: it was generated by a different pipeline with potential split leakage.

## Reproduction and larger experiments

The trainer requires a new or empty output directory to preserve prior results. To train again, choose `--output artifacts/reproduction`. To use a larger dataset, create a separate dataset directory:

To reproduce the sampled experiment:

```powershell
.\.venv\Scripts\python.exe download_data.py --max-per-class 200
.\.venv\Scripts\python.exe train.py --data data/plantvillage --output artifacts/reproduction
```

To run a separate full-dataset experiment:

```powershell
.\.venv\Scripts\python.exe download_data.py --max-per-class 0 --output data/plantvillage_full
.\.venv\Scripts\python.exe train.py --data data/plantvillage_full --output artifacts/full_run
```

The app defaults to `artifacts/planthealth`; change its `directory` setting to review another run. Do not repeatedly tune against test metrics; tune using validation, then evaluate a final selected model.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evaluate.py
.\.venv\Scripts\python.exe -B verify_project.py
```

Tests check deterministic/disjoint split membership, duplicate removal, and inference preprocessing. Training additionally checks saved-model reload consistency. A tiny synthetic fixture in tests is only for software verification, never a source of reported disease-classification accuracy.

## Scope and limitations

This is an educational prototype, not a field-validated plant diagnosis system. PlantVillage has controlled backgrounds; lighting, clutter, unknown diseases, and unrelated images can produce incorrect predictions. Softmax scores are not calibrated diagnostic certainty. There is no out-of-distribution detector, treatment recommendation, field benchmark, or public deployment.

The project began from a supplied group notebook. Credit that starting point and describe your actual contributions accurately; do not claim sole authorship of inherited work. See `INTERVIEW_PREP.md` for explanations and resume wording.

Technical references: https://www.tensorflow.org/api_docs/python/tf/keras/applications/MobileNetV2 and https://www.tensorflow.org/tutorials/images/transfer_learning
