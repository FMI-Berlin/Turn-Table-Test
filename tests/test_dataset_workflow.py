"""Dataset isolation and report routing regression tests; no external dependencies."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ANALYSIS = Path(__file__).resolve().parents[1] / 'analysis'
sys.path.insert(0, str(ANALYSIS))
from dataset import load_dataset
from build_report import automatic_report, markdown_report
from report_languages import conclusion, historical_assessment


class DatasetWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config = {
            'id': '2026-11-03_run-02', 'date': '2026-11-03',
            'reference_receiver': 'REF',
            'receivers': [
                {'name': 'OUT_A', 'file': 'raw/a.nmea', 'color': 'green'},
                {'name': 'REF', 'file': 'raw/ref.nmea', 'color': 'red'},
                {'name': 'OUT_B', 'file': 'raw/b.nmea', 'color': 'blue'}],
            'analysis': {'max_gap_s': 2}, 'assessment': None}
        (self.directory/'raw').mkdir()
        for receiver in self.config['receivers']:
            (self.directory/receiver['file']).write_text('fixture')

    def save(self):
        path = self.directory/'dataset.json'
        path.write_text(json.dumps(self.config))
        return path

    def test_paths_and_reference_order(self):
        dataset = load_dataset(self.save())
        self.assertEqual(dataset.receivers[0][0], 'REF')
        self.assertEqual(dataset.receivers[0][1], self.directory/'raw/ref.nmea')
        self.assertEqual(dataset.max_gap_s, 2)
        self.assertEqual(load_dataset(self.directory), dataset)

    def test_distinct_identifiers_keep_results_separate(self):
        first = load_dataset(self.save())
        self.config['id'] = '2026-11-03_run-03'
        second = load_dataset(self.save())
        self.assertNotEqual(first.results, second.results)
        self.assertIsNone(second.assessment)

    def test_rejects_unsafe_identifier_and_receiver_name(self):
        self.config['id'] = '../overwrite'
        with self.assertRaises(ValueError):
            load_dataset(self.save())
        self.config['id'] = 'valid'
        self.config['receivers'][0]['name'] = '../unsafe'
        with self.assertRaises(ValueError):
            load_dataset(self.save())

    def test_rejects_missing_input_and_unknown_reference(self):
        self.config['reference_receiver'] = 'missing'
        with self.assertRaises(ValueError):
            load_dataset(self.save())
        self.config['reference_receiver'] = 'REF'
        (self.directory/'raw/a.nmea').unlink()
        with self.assertRaises(FileNotFoundError):
            load_dataset(self.save())

    def test_rejects_invalid_gap(self):
        self.config['analysis']['max_gap_s'] = float('nan')
        with self.assertRaises(ValueError):
            load_dataset(self.save())

    def test_new_dataset_does_not_inherit_historical_assessment(self):
        for language in ('de', 'en', 'zh'):
            self.assertEqual(historical_assessment(language), '')

    def test_verdict_follows_current_measurements(self):
        def values(error):
            return dict(epochs=3, rms_m=error, median_m=error, p95_m=error, max_m=error)
        summary = {'outage_comparison': {'statistics': {'OUT_A': values(.02), 'OUT_B': values(.01)}}}
        self.assertIn('Lowest RMS: OUT_B', conclusion(summary, 'en'))
        summary['outage_comparison']['statistics']['OUT_A'] = values(.005)
        self.assertIn('Lowest RMS: OUT_A', conclusion(summary, 'en'))

    def test_automatic_report_has_three_chapters_and_numerical_table(self):
        summary = dict(date='2026-11-03', radius_m=.33, mean_rotation_period_s=170,
                       statistics={'REF': dict(epochs=5, rms_m=.001, max_m=.002)})
        markdown = automatic_report(summary)
        self.assertEqual(sum(line.startswith('# ') for line in markdown.splitlines()), 3)
        with patch('build_report.diagrams', return_value=''):
            latex = markdown_report(markdown, self.directory)
        self.assertEqual(latex.count(r'\begin{tabular}'), 3)
        self.assertIn('1.000', latex)

    def test_builder_rejects_other_dataset_results(self):
        config_path = self.save()
        (self.directory/'data').mkdir()
        (self.directory/'data/summary.json').write_text(json.dumps(
            {'dataset_id': 'different-dataset', 'date': '2026-11-03'}))
        result = subprocess.run([sys.executable, str(ANALYSIS/'build_report.py'),
                                 '--dataset', str(config_path), '--results-dir', str(self.directory)],
                                cwd='/tmp', text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Results do not match', result.stderr)
        self.assertFalse((self.directory/'report').exists())


if __name__ == '__main__':
    unittest.main()
