"""Historical source provenance and layout-independent vector calibration."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'references/historical-outage-results'
spec=importlib.util.spec_from_file_location('extract_pdf_curves',SOURCE/'extract_pdf_curves.py')
extractor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


def chart(transform):
    root=ET.Element('svg')
    def path(color,points):
        ET.SubElement(root,'path',style=f'fill:none;stroke:rgb({color});',transform=transform,
                      d=' '.join(f'{"M" if i==0 else "L"} {x} {y}' for i,(x,y) in enumerate(points)))
    path('0%,0%,0%',[(100,500),(600,500),(600,100),(100,100),(100,500)])
    for color in list(extractor.COLORS)[:-1]:
        path(color,[(100+i*500/9,500-i*100/9) for i in range(10)])
        path(color,[(520,150),(540,150)]) # Curve legend, not data.
    path('50.195312%,0%,0%',[(400,500-20/1400*400),(400,494.3)])
    path('50.195312%,0%,0%',[(550,200),(550,200.02)]) # Marker legend inside frame.
    return root


class HistoricalReferenceTests(unittest.TestCase):
    def test_calibration_survives_chart_translation_and_scaling(self):
        original,bounds=extractor.extract_curves(chart('matrix(1,0,0,1,0,0)'))
        moved,new_bounds=extractor.extract_curves(chart('matrix(0.75,0,0,0.75,33,77)'))
        self.assertNotEqual(bounds,new_bounds)
        self.assertEqual(set(original),set(extractor.COLORS.values()))
        for key in original:
            self.assertEqual(len(original[key]),len(moved[key]))
            for first,second in zip(original[key],moved[key]):
                self.assertAlmostEqual(first[0],second[0])
                self.assertAlmostEqual(first[1],second[1])
        precise=original['precise_clocks_300s']
        self.assertEqual(len(precise),1)
        self.assertAlmostEqual(precise[0][0],300)
        self.assertAlmostEqual(precise[0][1],20)
        self.assertEqual(len(original['no_sv_clock']),10)
        self.assertAlmostEqual(original['no_sv_clock'][-1][1],350)

    def test_missing_frame_or_series_fails_instead_of_writing_wrong_data(self):
        with self.assertRaisesRegex(ValueError,'frame'):
            extractor.extract_curves(ET.Element('svg'))
        root=chart('matrix(1,0,0,1,0,0)')
        root.remove(list(root)[1])
        with self.assertRaisesRegex(ValueError,'series'):
            extractor.extract_curves(root)
        with self.assertRaisesRegex(ValueError,'straight-line'):
            extractor.path_points(ET.Element('path',d='M 0 0 C 1 2 3 4 5 6'))

    def test_current_source_paths_and_checksums_match_catalog_and_csv(self):
        catalog=json.loads((ROOT/'references/literature/catalog.json').read_text())
        source=next(entry for entry in catalog if entry['id']=='R1')
        self.assertEqual(source['date'],'2005-07-18')
        self.assertEqual(source['revision_date'],'2026-11-10')
        self.assertIn('Vollath',source['authors'])
        for file_key,hash_key in [('local_file','sha256'),('editable_file','editable_file_sha256')]:
            self.assertEqual(hashlib.sha256((ROOT/source[file_key]).read_bytes()).hexdigest(),source[hash_key])
        provenance=json.loads((SOURCE/'hrms.provenance.json').read_text())
        self.assertEqual(provenance['source_pdf'],'trimble-report.pdf')
        self.assertEqual(provenance['source_pdf_sha256'],source['sha256'])
        self.assertEqual(provenance['csv_sha256'],hashlib.sha256((SOURCE/'hrms.csv').read_bytes()).hexdigest())
        with (SOURCE/'hrms.csv').open() as stream:
            rows=list(csv.DictReader(stream))
        for name,count in provenance['series_points'].items():
            self.assertEqual(sum(r['variant']==name for r in rows),count)
        precise=[r for r in rows if r['variant']=='precise_clocks_300s']
        self.assertEqual(len(precise),1)
        self.assertAlmostEqual(float(precise[0]['dage_s']),300,delta=.05)
        self.assertAlmostEqual(float(precise[0]['hrms_mm']),20,delta=1)
        for assessment in (ROOT/'documentation/assessments').glob('*.md'):
            text=assessment.read_text()
            self.assertNotIn('original.pdf',text)
            self.assertNotIn('original.docx',text)
            self.assertEqual(text.count('Files: `trimble-report.docx`, `trimble-report.pdf`'),3)


if __name__=='__main__':
    unittest.main()
