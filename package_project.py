"""Create a portable project bundle after successful verification."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
verification = root / 'artifacts/planthealth/verification.json'
if not verification.exists() or json.loads(verification.read_text())['status'] != 'passed':
    raise SystemExit('Run verify_project.py successfully before packaging.')
destination = root / 'PlantHealth_Interview_Project.zip'
if destination.exists():
    raise SystemExit('Bundle already exists; rename it before creating a new bundle.')
with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=3) as bundle:
    for path in sorted(root.iterdir()):
        if path.is_file() and (path.suffix in {'.py', '.md', '.txt', '.ipynb', '.ps1'} or path.name == '.gitignore'):
            bundle.write(path, path.relative_to(root))
    for folder in ('tests', '.streamlit', 'artifacts/planthealth', 'data/plantvillage'):
        for path in sorted((root / folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                bundle.write(path, path.relative_to(root))
print(f'Created {destination} ({destination.stat().st_size / 1024**2:.1f} MB)')
