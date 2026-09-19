# Interview preparation

## A 45-second explanation

“I extended a plant-leaf classification notebook into a reproducible 15-class application. During review, I found that splitting a shuffled dataset by batches could contaminate the evaluation. I replaced that with a deterministic, stratified file-level split and exact-image duplicate checks. I then used a frozen ImageNet MobileNetV2 backbone with a small trained classification head, evaluated the selected model on held-out images, and built a local Streamlit interface. The current results are from a sampled PlantVillage dataset; real field-photo performance has not been measured.”

Use this only after you understand and can demonstrate the work. Explain that the starting notebook was group/coursework and that you used coding assistance for the extension if asked. Describe what you personally reviewed, changed, and validated.

## Questions you should be able to answer

**What does the model predict?** One of 15 known plant-health classes for pepper, potato, or tomato. Healthy leaves are separate classes. This is image classification, not bounding-box object detection or lesion segmentation.

**Why transfer learning?** ImageNet pretraining supplies useful visual features when labeled data and training time are limited. MobileNetV2 is relatively compact. Only the classification head is trained here; the backbone is frozen.

**Why 160×160?** It reduces CPU computation and memory, with a possible loss of fine lesion detail. It is a practical trade-off, not a proven optimal resolution.

**What is data leakage?** Information from evaluation data influences training or selection. Here, splits are made once from individual file records before loading or augmentation. Exact pixel duplicates are removed first. Similar images of the same leaf may remain because leaf identities are unavailable.

**Why three splits?** Training updates weights; validation selects the best epoch and guides learning-rate changes; test estimates performance after selection. Repeatedly tuning against test results would make that estimate optimistic.

**How does augmentation work?** An extra randomly flipped/rotated view is generated for each training image and converted into frozen features. It increases variation seen by the head. Validation and test images are not augmented.

**What are logits and softmax?** Logits are unnormalized class scores. Softmax converts them into scores summing to one. This model outputs softmax and uses sparse cross-entropy with its default `from_logits=False`, a matching pairing.

**Why macro F1?** It averages F1 across classes equally, exposing weaknesses hidden by accuracy on imbalanced data. Precision measures how often a class prediction is correct; recall measures how many actual members of that class are found.

**How is overfitting controlled?** A frozen backbone, dropout, training augmentation, class weighting, validation monitoring, and early stopping. The confusion matrix and validation history help diagnose weaknesses.

**Does 90% model score mean 90% chance of being correct?** No. These scores are not calibrated. The classifier may be confident on an unknown disease or an unrelated image.

**What would you do next?** Evaluate real field images from different farms; group splits by leaf/plant/source; examine near-duplicates; compare with the original CNN under the same split; consider fine-tuning, calibration, and unknown-image rejection. These are future work, not implemented claims.

## Two-day study plan

Day 1: run the demo; read `plant_data.py`, `train.py`, and `RESULTS.md`; understand the split, transfer learning, and confusion matrix. Practice explaining three incorrect predictions from `test_predictions.json` if available.

Day 2: reproduce a command-line prediction; rehearse the 45-second explanation and questions above; practice drawing input → preprocessing → frozen CNN → dense head → class scores. Be prepared to explain the dataset sample size and limitations without exaggerating the metric.

## Data science / ML interview focus

Be ready to defend the experiment, not just describe the library calls:

- **Sampling:** up to 200 images per class makes this a relatively balanced sample. It does not match the natural frequency of diseases on farms. Report the sample size alongside the score.
- **Baseline:** `metrics.json` includes the test majority-class baseline. It is a simple context check, not a competitive learned baseline. A same-split custom CNN or linear classifier comparison is future work.
- **Bias and variance:** a frozen backbone lowers training cost and limits overfitting, but may miss task-specific lesion features. Fine-tuning could help, but must be selected on validation data.
- **Error analysis:** read the confusion matrix by row (actual class) and column (predicted class). Find the class with lowest recall, inspect false negatives, and compare visually similar disease pairs. Do not use these test errors to repeatedly tune this test benchmark.
- **Small test set:** 295 images give a limited estimate. One changed prediction shifts overall accuracy by about 0.34 percentage points. Real-world performance needs an independent field dataset.
- **Class imbalance:** class weights are computed from training labels only. Macro F1 treats each class equally; weighted F1 reflects this test sample's class frequencies.
- **Deployment:** the demo reuses the saved preprocessing and class order. A local Streamlit app is a demonstration, not a production service. Monitoring, security hardening, field validation, and model drift checks are future work.
- **MobileNetV2:** it uses depthwise and pointwise convolutions with inverted residual blocks to reduce computation. Here those pretrained weights stay fixed; the dense classification head learns the PlantVillage labels.

A good answer to “What was your main contribution?” is a precise account of the evaluation repair, reproducible data handling, trained artifact, and inference integration you actually understand. Do not say you invented MobileNetV2 or built the original group notebook alone.

## Resume wording

**Plant Leaf Disease Classification | Python, TensorFlow/Keras, Streamlit**

- Extended a plant-disease notebook into a reproducible 15-class transfer-learning pipeline with deterministic data splits and exact-image duplicate checks.
- Built a MobileNetV2 classifier and evaluated held-out performance using accuracy, macro F1, and a per-class confusion matrix.
- Developed a local image-upload application with top-three class scores and saved-model inference.

Use only measured figures from `RESULTS.md` when adding accuracy or sample counts. Say “sampled PlantVillage data,” and do not claim training on the full original dataset or production deployment.
