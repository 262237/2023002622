"""Verify saved-model evaluation and software tests in one Python process."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import unittest
from evaluate import main as evaluate_saved_model

def main():
    output = Path('artifacts/planthealth')
    if not (output / 'metrics.json').exists():
        raise SystemExit('Train the model first; there are no completed metrics to verify.')
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        evaluate_saved_model()
    evaluation = json.loads(capture.getvalue())
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit('Verification incomplete: tests failed or were skipped.')
    notebook = json.loads(Path('PlantDiseaseDetection_Completed.ipynb').read_text(encoding='utf-8'))
    for index, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'notebook_cell_{index}', 'exec')
    report = {'status': 'passed', 'tests_run': result.testsRun,
              'saved_model_evaluation': evaluation, 'notebook_code_syntax': 'passed',
              'model_sha256': hashlib.sha256((output / 'model.keras').read_bytes()).hexdigest()}
    (output / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
