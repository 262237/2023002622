"""Integration check uses real trained artifacts when available."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

@unittest.skipUnless(Path('artifacts/planthealth/config.json').exists(), 'Requires completed training artifacts')
class AppTests(unittest.TestCase):
    def test_load_and_held_out_prediction(self):
        app = AppTest.from_file('app.py', default_timeout=120).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, '🌿 PlantHealth')
        options = app.selectbox[0].options
        if len(options) > 1:
            app.selectbox[0].select(options[1]).run(timeout=120)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.subheader), 1)
            self.assertEqual(len(app.error), 0)

if __name__ == '__main__':
    unittest.main()
