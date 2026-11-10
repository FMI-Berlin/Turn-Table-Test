#!/usr/bin/env python3
"""Extract Figure 1 vector coordinates; requires Poppler's pdftocairo."""
import argparse
import csv
import hashlib
import json
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


def path_points(element):
    """Apply each straight-line PDF path's affine transform into SVG coordinates."""
    path = element.attrib['d']
    if any(command not in ('M','L') for command in re.findall(r'[A-Za-z]',re.sub(NUMBER,'',path))):
        raise ValueError('Only M/L straight-line paths are supported')
    values = list(map(float, re.findall(NUMBER, path)))
    if len(values) % 2:
        raise ValueError('Unpaired path coordinates')
    transform = element.attrib.get('transform', 'matrix(1,0,0,1,0,0)')
    a,b,c,d,e,f = map(float, re.findall(NUMBER, transform))
    return [(a*x+c*y+e, b*x+d*y+f) for x,y in zip(values[::2],values[1::2])]


def extract_curves(root):
    """Calibrate from the chart frame, independent of its location on the page."""
    paths = [el for el in root.iter() if el.tag.rsplit('}',1)[-1] == 'path']
    frames = []
    for el in paths:
        if 'stroke:rgb(0%,0%,0%)' not in el.attrib.get('style',''):
            continue
        if len(re.findall(NUMBER,el.attrib.get('d',''))) != 10:
            continue
        points = path_points(el)
        if points[0] != points[-1]:
            continue
        xs,ys = sorted({x for x,_ in points}), sorted({y for _,y in points})
        if len(xs)==2 and len(ys)==2 and xs[1]-xs[0]>100 and ys[1]-ys[0]>100:
            frames.append((xs[0],xs[1],ys[0],ys[1]))
    if not frames:
        raise ValueError('No rectangular Figure 1 frame found')
    left,right,top,bottom = max(frames,key=lambda b:(b[1]-b[0])*(b[3]-b[2]))
    found = {key: [] for key in COLORS.values()}
    for el in paths:
        color = re.search(r'stroke:rgb\(([^)]+)\)',el.attrib.get('style',''))
        if not color or color[1] not in COLORS:
            continue
        key = COLORS[color[1]]
        count = len(re.findall(NUMBER,el.attrib['d']))
        # Curves have >=10 vertices. The precise-clock marker's centre is a
        # two-vertex tiny stroke near the documented 300 s age; its legend
        # counterpart is rejected even if the legend is inside the frame.
        if key=='precise_clocks_300s':
            if count != 4:
                continue
        elif count < 20:
            continue
        points = path_points(el)
        if key=='precise_clocks_300s':
            points = points[:1]
            if abs((points[0][0]-left)/(right-left)*500-300)>1:
                continue
        if not all(left-.02<=x<=right+.02 and top-.02<=y<=bottom+.02 for x,y in points):
            continue
        for x,y in points:
            age = (x-left)/(right-left)*500
            hrms = (bottom-y)/(bottom-top)*1400
            found[key].append((max(0,age),max(0,hrms)))
    if not all(found.values()) or len(found['precise_clocks_300s']) != 1:
        raise ValueError(f'Missing or ambiguous historical series: { {k:len(v) for k,v in found.items()} }')
    return found, dict(left=left,right=right,top=top,bottom=bottom)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',type=Path,default=ROOT/'trimble-report.pdf')
    parser.add_argument('--output',type=Path,default=ROOT/'hrms.csv')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        svg = Path(temporary)/'page2.svg'
        subprocess.run(['pdftocairo','-f','2','-l','2','-svg',str(args.pdf),str(svg)],check=True)
        found,bounds = extract_curves(ET.parse(svg).getroot())
    with args.output.open('w',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n')
        writer.writerow(['variant','dage_s','hrms_mm'])
        for key,points in found.items():
            for age,hrms in sorted(points):
                writer.writerow([key,f'{age:.3f}',f'{hrms:.3f}'])
    provenance=dict(source_pdf=args.pdf.name,source_pdf_sha256=hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
                    figure=1,page=2,axis_ranges=dict(dage_s=[0,500],hrms_mm=[0,1400]),
                    svg_axis_bounds=bounds,method='affine-transformed vector paths calibrated to detected chart frame',
                    series_points={key:len(points) for key,points in found.items()},
                    csv_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                    precision_note='Reconstructed plot coordinates, not original observations; PDF export rounding applies')
    args.output.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':
    main()
