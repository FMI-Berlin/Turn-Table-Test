#!/usr/bin/env python3
"""Extract Figure 1 vector coordinates; requires Poppler's pdftocairo."""
import csv
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
COLORS = {
    '100%,0%,0%': 'no_sv_clock',
    '0%,100%,0%': 'sv_clock',
    '0%,0%,100%': 'sv_clock_rel',
    '100%,0%,100%': 'sv_clock_rel_ultra',
    '0%,0%,50.195312%': 'sv_clock_rel_precise',
    '50.195312%,0%,0%': 'precise_clocks_300s',
}
NUMBER = r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?'


def main():
    with tempfile.TemporaryDirectory() as temporary:
        svg = Path(temporary) / 'page2.svg'
        subprocess.run(['pdftocairo', '-f', '2', '-l', '2', '-svg',
                        str(ROOT / 'original.pdf'), str(svg)], check=True)
        root = ET.parse(svg).getroot()
    # Figure 1 axis corners in the PDF's pre-transform coordinate system.
    left, right, bottom, top = 179.350458, 673.429790, 765.671863, 432.729502
    scale, offset = .749144, .440345
    found = {key: [] for key in COLORS.values()}
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] != 'path':
            continue
        color = re.search(r'stroke:rgb\(([^)]+)\)', element.attrib.get('style', ''))
        if not color or color[1] not in COLORS:
            continue
        key = COLORS[color[1]]
        values = list(map(float, re.findall(NUMBER, element.attrib['d'])))
        # Ignore legend samples; the precise-clock point has a tiny centre stroke.
        if key == 'precise_clocks_300s':
            if len(values) != 4 or abs(values[0] - 475.787629) > .01:
                continue
            values = values[:2]
        elif len(values) < 20:
            continue
        a,b,c,d,e,f = map(float, re.findall(NUMBER, element.attrib['transform']))
        for x,y in zip(values[::2], values[1::2]):
            px,py = a*x+c*y+e, b*x+d*y+f
            age = (px/scale-left)/(right-left)*500
            hrms = (bottom-(py-offset)/scale)/(bottom-top)*1400
            found[key].append((max(0, age), max(0, hrms)))
    assert all(found.values()), 'Missing historical series'
    destination = ROOT / 'hrms.csv'
    with destination.open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['variant', 'dage_s', 'hrms_mm'])
        for key, points in found.items():
            for age, hrms in sorted(points):
                writer.writerow([key, f'{age:.3f}', f'{hrms:.3f}'])
    print(destination)


if __name__ == '__main__':
    main()
