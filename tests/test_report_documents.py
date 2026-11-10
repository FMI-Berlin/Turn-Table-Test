"""Report navigation, citation rendering and shared assessment checks."""
from pathlib import Path
import re
import csv
import hashlib
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from report_markdown import inline_html, markdown_html, add_contents
from report_languages import historical_assessment
from build_report import inline


class ReportDocumentTests(unittest.TestCase):
    def test_html_links_and_untrusted_text_are_escaped(self):
        text=inline_html('[Paper](https://doi.org/10.3390/rs11101256) **clock** `<script>`')
        self.assertIn('<a href="https://doi.org/10.3390/rs11101256">Paper</a>',text)
        self.assertIn('<strong>clock</strong>',text)
        self.assertNotIn('<script>',text)
        self.assertNotIn('href="javascript:',inline_html('[bad](javascript:alert)'))

    def test_assessment_tables_have_headers_and_links(self):
        text=markdown_html('## Evidence\n\n| Source | Scope |\n|---|---|\n| [Paper](https://example.org/paper) | 15 s |\n')
        self.assertIn('<th>Source</th>',text)
        self.assertIn('<td>15 s</td>',text)
        self.assertEqual(text.count('<table'),1)
        self.assertIn('href="https://example.org/paper"',text)

    def test_contents_links_are_unique_and_resolve(self):
        text=add_contents('<html><body><h1>English</h1><h2>Evidence</h2><h1>中文</h1><h2>Evidence</h2></body></html>')
        anchors=re.findall(r'id="(section-[^"]+)"',text)
        links=re.findall(r'href="#(section-[^"]+)"',text)
        self.assertEqual(len(anchors),4)
        self.assertEqual(len(set(anchors)),4)
        self.assertEqual(links,anchors)
        self.assertEqual(text.count('<nav'),1)

    def test_latex_citations_are_real_links(self):
        text=inline('Evidence [R2](https://doi.org/10.3390/rs11101256), **fixed**, `dAge_s`.')
        self.assertIn(r'\hyperlink{ref-R2}{[R2]}',text)
        self.assertIn(r'\textbf{fixed}',text)
        self.assertNotIn('](https',text)

    def test_all_language_chapters_include_new_discussion_and_references(self):
        assessment=ROOT/'documentation/assessments/2026-11-07.md'
        for lang in ('de','en','zh'):
            text=historical_assessment(lang,assessment)
            self.assertIn('2005',text)
            self.assertIn('18',text)
            self.assertIn('Trimble',text)
            self.assertIn('LG290P',text)
            self.assertIn('26',text)
            self.assertIn('href="#ref-R2"',text)
            self.assertIn('href="#ref-R4"',text)
            self.assertIn('<table',text)
            self.assertNotIn('PERFORMANCE_TABLE',text)
            self.assertNotIn('](https',text)


    def test_october_source_provenance_and_quoted_current_metrics(self):
        catalog=json.loads((ROOT/'references/literature/catalog.json').read_text())
        self.assertEqual(len({entry['id'] for entry in catalog}),len(catalog))
        source=next(entry for entry in catalog if entry['id']=='R10')
        self.assertEqual(source['date'],'2026-10-18')
        self.assertEqual(hashlib.sha256((ROOT/source['local_file']).read_bytes()).hexdigest(),source['sha256'])
        self.assertEqual(hashlib.sha256((ROOT/source['related_image']).read_bytes()).hexdigest(),source['related_image_sha256'])
        assessment=ROOT/'documentation/assessments/2026-11-07.md'
        with (ROOT/'results/2026-11-07/data/horizontal_dage_hrms.csv').open() as stream:
            bins=[row for row in csv.DictReader(stream) if row['age_upper_s']=='120']
        for lang in ('de','en','zh'):
            rendered=historical_assessment(lang,assessment)
            self.assertIn('[R10]',rendered)
            self.assertIn('3 mm/s',rendered)
            for row in bins:
                value=f"{float(row['hrms_mm']):.2f}"
                if lang=='de':value=value.replace('.',',')
                self.assertIn('<td>'+value+'</td>',rendered)
                self.assertIn('<td>'+row['epochs']+'</td>',rendered)


if __name__=='__main__':
    unittest.main()
