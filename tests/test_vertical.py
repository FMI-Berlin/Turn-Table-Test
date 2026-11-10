"""Known-height, interpolation and RMS cases for vertical residuals."""
import math
from pathlib import Path
import sys
import tempfile
import os
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'analysis'))
from vertical import gga_height, height_at, vertical_stats, vertical_analysis, vertical_markdown
from turn_table import age_hrms, parse, svg_plot
from build_report import figure


class VerticalTests(unittest.TestCase):
    def test_ellipsoidal_height_removes_different_geoid_offsets(self):
        def fields(h, n):
            return ['']*9+[h, 'M', n, 'M']
        self.assertAlmostEqual(gga_height(fields('47.580','0.000')),
                               gga_height(fields('56.099','-8.519')))
        for h, n in [('', '0'), ('1', ''), ('nan', '0'), ('1', 'inf')]:
            self.assertIsNone(gga_height(fields(h,n)))
        invalid = fields('1','0'); invalid[10]='F'
        self.assertIsNone(gga_height(invalid))

    def test_reference_interpolation_rejects_gaps_and_extrapolation(self):
        reference = ([0,1,5], [10,12,16])
        self.assertEqual(height_at(reference,.5,3),11)
        self.assertEqual(height_at(reference,5,3),16)
        for t in (-1,3,6):
            self.assertIsNone(height_at(reference,t,3))
        self.assertIsNone(height_at(([],[]),0,3))

    def test_vrms_includes_bias_and_signed_errors(self):
        stats = vertical_stats([{'error_up_m':x} for x in (-.003,.003,.003)])
        self.assertAlmostEqual(stats['vrms_m'],.003)
        self.assertAlmostEqual(stats['bias_m'],.001)
        self.assertAlmostEqual(stats['vrms_m']**2,stats['bias_m']**2+stats['std_m']**2)
        self.assertEqual(vertical_stats([]),{'epochs':0})

    def test_bins_signed_rms_boundaries_and_slope_in_mm_per_second(self):
        bins, fit = age_hrms([(0,-.003),(10,.003),(20,-.007),(30,.011)])
        self.assertEqual([b['epochs'] for b in bins],[2,1,1])
        self.assertEqual([b['hrms_mm'] for b in bins],[3,7,11])
        _, fit = age_hrms([(30,-.003),(90,.009)],60)
        self.assertAlmostEqual(fit['slope_mm_per_s'],.1)
        self.assertAlmostEqual(fit['intercept_mm'],0)

    def test_parser_keeps_horizontal_position_when_height_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'height.nmea'
            path.write_text('$GNGGA,010000,5200.0,N,01300.0,E,4,20,1.0,,M,0,M,12,0001\n')
            rows, _, bad, _ = parse(path)
            self.assertEqual(len(rows),1)
            self.assertIsNone(rows[0]['height_m'])
            self.assertEqual(bad,0)

    def test_vertical_pipeline_uses_fixed_reference_and_common_outage_epochs(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary); (output/'data').mkdir(); (output/'plots').mkdir()
            data=[[dict(t=0,q=4,height_m=10),dict(t=1,q=5,height_m=999),dict(t=2,q=4,height_m=12)],
                  [dict(t=0,q=4,height_m=10.003),dict(t=1,q=4,height_m=11.003),dict(t=2,q=4,height_m=None)],
                  [dict(t=0,q=4,height_m=9.996),dict(t=1,q=4,height_m=10.996),dict(t=2,q=4,height_m=11.996)]]
            rows=[dict(utc_seconds=t,seconds_since_start=t,correction_age_s=12) for t in range(3)]
            residuals=[('REF','red',rows),('A','green',rows),('B','blue',rows)]
            plots=[]
            summary=vertical_analysis(output,data,residuals,3,lambda *a,**k:plots.append(a),age_hrms)
            self.assertEqual(summary['statistics']['A']['epochs'],2)
            for name,error in [('A',.003),('B',.004)]:
                self.assertEqual(summary['paired_outage_statistics'][name]['epochs'],2)
                self.assertAlmostEqual(summary['paired_outage_statistics'][name]['vrms_m'],error)
            self.assertEqual(len(plots),4)
            for plot in plots:
                self.assertNotIn('REF',[name for name,_,_ in plot[1]])
            for language in ('de','en','zh'):
                rendered=vertical_markdown({'vertical':summary},language)
                self.assertIn('VRMS',rendered)
                self.assertIn('3.000',rendered)

    def test_layout_rebuild_reuses_only_geometry_newer_than_svg(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary); (output/'plots').mkdir(); (output/'report/figures').mkdir(parents=True)
            svg=output/'plots/example.svg'
            svg_plot(svg,[('A','green',[(0,0),(1,1)])],'x','y','Known points')
            figure('example',output)
            pdf=output/'report/figures/example.pdf'
            os.utime(pdf,(svg.stat().st_mtime+2,svg.stat().st_mtime+2))
            with patch('build_report.pdf_geometry') as render:
                figure('example',output,reuse_geometry=True)
                render.assert_not_called()
                os.utime(svg,(pdf.stat().st_mtime+2,pdf.stat().st_mtime+2))
                figure('example',output,reuse_geometry=True)
                render.assert_called_once()
            with patch('build_report.pdf_geometry') as render:
                figure('example',output)
                render.assert_called_once()


if __name__ == '__main__':
    unittest.main()
