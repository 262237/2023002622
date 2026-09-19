"""Image validation, decoded-pixel deduplication, and stable stratified splits."""
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np

EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def image_array(source, size):
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        return np.asarray(image.resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)

def make_split(root, seed=42):
    root = Path(root).resolve()
    groups, hashes, duplicates, invalid = defaultdict(list), {}, [], []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        relative = path.relative_to(root)
        if len(relative.parts) != 2:
            raise ValueError(f'Expected data/class/image layout: {relative}')
        label = relative.parts[0]
        try:
            with Image.open(path) as image:
                rgb = ImageOps.exif_transpose(image).convert('RGB')
                digest = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        except (OSError, ValueError) as exc:
            invalid.append({'path': relative.as_posix(), 'error': str(exc)})
            continue
        if digest in hashes:
            if hashes[digest]['class'] != label:
                raise ValueError(f'Identical pixels with conflicting labels: {relative}')
            duplicates.append(relative.as_posix())
            continue
        record = {'path': relative.as_posix(), 'class': label, 'sha256_pixels': digest}
        hashes[digest] = record
        groups[label].append(record)
    if len(groups) < 2:
        raise ValueError('At least two class directories containing valid images are required.')
    classes = sorted(groups)
    records = []
    for label, rows in sorted(groups.items()):
        if len(rows) < 10:
            raise ValueError(f'{label}: need at least 10 distinct images, found {len(rows)}')
        random.Random(f'{seed}:{label}').shuffle(rows)
        n_test = max(1, round(len(rows) * .1))
        n_val = max(1, round(len(rows) * .1))
        for index, row in enumerate(rows):
            row['split'] = 'test' if index < n_test else 'validation' if index < n_test + n_val else 'train'
            row['label'] = classes.index(label)
            records.append(row)
    return {'seed': seed, 'classes': classes, 'records': records,
            'counts': dict(Counter(r['split'] for r in records)),
            'duplicates_removed': duplicates, 'invalid_images': invalid,
            'limitation': 'Exact decoded-pixel duplicates removed; related leaves and near-duplicates may remain.'}
