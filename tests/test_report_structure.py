"""Document-level ordering, shared references, portable links and equations."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from report_document import (assemble, split_chapters, HRMS_TITLES, VERTICAL_TITLES,
                             bibliography_html, metadata, write_html_report, source_links)
from report_equations import EQUATIONS, equation_html, equation_latex
from build_report import markdown_report, bibliography, title_page
from report_markdown import inline_html


class ReportStructureTests(unittest.TestCase):
    def load(self,date):
        results=ROOT/'results'/date
        summary=json.loads((results/'data/summary.json').read_text())
        source=(ROOT/'documentation/assessments'/f'{date}.md').read_text()
        return results,summary,source

    def test_vertical_is_next_section_after_hrms_in_each_edition(self):
        for date in ['2026-11-03','2026-11-07']:
            _,summary,source=self.load(date)
            document,records=assemble(source,summary)
            self.assertEqual(len(records),13)
            for lang,(_,body) in zip(['de','en','zh'],split_chapters(document)):
                headings=re.findall(r'^## (.*)',body,re.MULTILINE)
                self.assertEqual(headings[headings.index(HRMS_TITLES[lang])+1],VERTICAL_TITLES[lang])
                self.assertEqual(headings.count(VERTICAL_TITLES[lang]),1)
                for group in ['rotation','horizontal','hrms','vertical','historical']:
                    self.assertEqual(body.count(':::figures '+group),1)
                self.assertNotIn('**[R1]**',body)
                self.assertNotIn('## References',body)
                self.assertIn(':::equation vrms',body)

    def test_one_bibliography_with_resolvable_in_text_and_source_links(self):
        results,summary,source=self.load('2026-11-07')
        document,records=assemble(source,summary)
        html=bibliography_html(records,results)
        self.assertEqual(html.count('<h1>References</h1>'),1)
        ids=re.findall(r'id="(ref-R\d+)"',html)
        self.assertEqual(len(ids),13)
        self.assertEqual(len(set(ids)),13)
        for ref in set(re.findall(r'\[(R\d+)\]',document)):
            self.assertIn('ref-'+ref,ids)
            self.assertIn(f'href="#ref-{ref}"',inline_html('['+ref+']'))
        latex=bibliography(records,results/'report')
        for ref in records:
            self.assertEqual(latex.count(r'\hypertarget{ref-'+ref['id']+'}'),1)
            for _,target in source_links(ref,results):
                if not target.startswith(('http://','https://')):
                    self.assertTrue((results/target).resolve().is_file())
        self.assertIn('https://doi.org/10.3390/rs11101256',html)
        self.assertIn('Source DOCX',html)
        self.assertIn(r'\href{../../../references/historical-outage-results/trimble-report.pdf}',latex)

    def test_cover_uses_distinct_report_and_measurement_dates(self):
        _,summary,_=self.load('2026-11-07')
        meta=metadata(summary,'2026-11-10')
        cover=title_page(meta)
        for text in ['GPT-6.1-Sol + sok','Feyman','10 November 2026','7 November 2026','Measurement date','Report date']:
            self.assertIn(text,cover)
        with self.assertRaises(ValueError):metadata(summary,'not-a-date')

    def test_display_equations_are_native_math_and_unknown_ids_fail(self):
        for name in EQUATIONS:
            root=ET.fromstring(equation_html(name))
            self.assertIsNotNone(root.find('{http://www.w3.org/1998/Math/MathML}math'))
            self.assertNotIn('<script',equation_html(name))
            self.assertTrue(equation_latex(name))
        with self.assertRaises(KeyError):equation_html('not-a-formula')

    def test_pdf_structure_keeps_plots_near_their_sections(self):
        results,summary,source=self.load('2026-11-07')
        document,_=assemble(source,summary)
        def marker(stem,*args,**kwargs):return '%FIGURE '+stem
        with patch('build_report.figure',side_effect=marker):
            latex=markdown_report(document,results,True)
        self.assertLess(latex.index('%FIGURE horizontal_dage_scatter'),latex.index('%FIGURE horizontal_dage\n'))
        self.assertLess(latex.index('%FIGURE horizontal_dage\n'),latex.index(r'\subsection{Vertikale Genauigkeit und VRMS}'))
        self.assertLess(latex.index('%FIGURE vertical_dage_scatter'),latex.index('%FIGURE vertical_dage_vrms'))
        self.assertIn(r'\begin{equation}',latex)
        self.assertIn(r'\hyperlink{ref-R1}{[R1]}',latex)

    def test_html_cover_precedes_contents_and_references_are_last(self):
        _,summary,source=self.load('2026-11-07')
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            (output/'plots').mkdir()
            assessment=output/'assessment.md';assessment.write_text(source)
            write_html_report(output,summary,assessment,'2026-11-10')
            text=(output/'index.html').read_text()
            self.assertLess(text.index('class="title-page"'),text.index('<nav'))
            self.assertEqual(text.count('<h1 id='),4) # Three editions and the shared bibliography.
            self.assertEqual(text.count('class="references"'),1)
            self.assertGreater(text.index('class="references"'),text.index('lang="zh-Hans"'))
            anchors=re.findall(r'id="(section-[^"]+)"',text)
            links=re.findall(r'href="#(section-[^"]+)"',text)
            self.assertEqual(anchors,links)
            self.assertEqual(len(anchors),len(set(anchors)))
            for ref in re.findall(r'href="#(ref-R\d+)"',text):
                self.assertEqual(text.count('id="'+ref+'"'),1)


if __name__=='__main__':
    unittest.main()
