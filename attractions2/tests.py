# Create your tests here.
from pathlib import Path
from unittest import TestCase
from attractions2.trail import analyze_trail

BASE_DIR = Path(__file__).resolve().parent.parent


class TrailAnalysisTest(TestCase):
    def test_analyze_file(self):
        with open(BASE_DIR / "test_resources/73e6266f-39b4-479f-a644-8409cd695d06.csv.gz", "rb") as fh:
            analysis = analyze_trail(fh)

        self.assertEqual(int(analysis.elevation_gain), 107)
        self.assertAlmostEqual(analysis.center_latitude, 31.81994832796412)
        self.assertAlmostEqual(analysis.center_longitude, 35.25593624223869)
        self.assertEqual(int(analysis.distance), 3281)
