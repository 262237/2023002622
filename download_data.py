"""Download a deterministic 15-class subset from the original PlantVillage repo."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import time
from urllib.request import Request, urlopen
from urllib.parse import quote

REPO = 'spMohanty/PlantVillage-Dataset'

def fetch(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'PlantHealth-Portfolio/1.0'}), timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/plantvillage'))
    parser.add_argument('--max-per-class', type=int, default=200, help='0 downloads all available images in the selected classes')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.max_per_class < 0:
        parser.error('--max-per-class must be nonnegative')
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / 'source.json'
    # Pin every subsequent download to the revision recorded on the first run.
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous['max_per_class'] != args.max_per_class or previous['seed'] != args.seed:
            raise ValueError('Use a new output directory when changing the sampling configuration.')
        revision = previous['revision']
    else:
        revision = json.loads(fetch(f'https://api.github.com/repos/{REPO}/commits/master'))['sha']
    subtree = revision
    for folder in ('raw', 'color'):
        listing = json.loads(fetch(f'https://api.github.com/repos/{REPO}/git/trees/{subtree}'))
        subtree = next(item['sha'] for item in listing['tree'] if item['path'] == folder)
    listing = json.loads(fetch(f'https://api.github.com/repos/{REPO}/git/trees/{subtree}'))
    tree = {'tree': []}
    for folder in listing['tree']:
        if folder['type'] == 'tree' and folder['path'].startswith(('Pepper,_bell', 'Potato', 'Tomato')):
            print(f'Indexing {folder["path"]}', flush=True)
            class_tree = json.loads(fetch(f'https://api.github.com/repos/{REPO}/git/trees/{folder["sha"]}'))
            if class_tree.get('truncated'):
                raise RuntimeError('Class listing truncated; refusing an incomplete dataset.')
            for item in class_tree['tree']:
                item['path'] = folder['path'] + '/' + item['path']
                tree['tree'].append(item)
    classes = {}
    for item in tree['tree']:
        item['path'] = 'raw/color/' + item['path']
        parts = item['path'].split('/')
        if len(parts) == 4 and parts[:2] == ['raw', 'color'] and parts[2].startswith(('Pepper,_bell', 'Potato', 'Tomato')) and parts[3].lower().endswith(('.jpg', '.jpeg', '.png')):
            classes.setdefault(parts[2], []).append(item)
    if len(classes) != 15:
        raise RuntimeError(f'Expected 15 classes; found {sorted(classes)}')
    selected = []
    for label, items in sorted(classes.items()):
        items.sort(key=lambda x: x['path'])
        random.Random(f'{args.seed}:{label}').shuffle(items)
        selected.extend(items[:args.max_per_class] if args.max_per_class else items)
    metadata = {'repository': f'https://github.com/{REPO}', 'revision': revision,
                'max_per_class': args.max_per_class, 'seed': args.seed,
                'selected_images': len(selected), 'classes': sorted(classes),
                'status': 'downloading', 'files': selected}
    manifest_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    def download(item):
        parts = item['path'].split('/')
        target = args.output / parts[2] / parts[3]
        target.parent.mkdir(parents=True, exist_ok=True)
        def valid(blob):
            return hashlib.sha1(f'blob {len(blob)}\0'.encode() + blob).hexdigest() == item['sha']
        if target.exists() and valid(target.read_bytes()):
            return
        blob = fetch(f'https://raw.githubusercontent.com/{REPO}/{revision}/{quote(item["path"], safe="/")}')
        if not valid(blob):
            raise ValueError(f'Checksum mismatch: {target.name}')
        target.write_bytes(blob)

    print(f'Downloading {len(selected)} images across {len(classes)} classes at {revision}', flush=True)
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(download, item) for item in selected]
        for count, future in enumerate(as_completed(futures), 1):
            future.result()
            if count % 100 == 0 or count == len(futures):
                print(f'{count}/{len(futures)} verified', flush=True)
    metadata['status'] = 'complete'
    manifest_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
