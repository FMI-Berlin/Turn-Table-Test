#!/usr/bin/env python3
"""Create a dataset-specific trilingual LaTeX/PDF report from generated SVG plots.
Run from any directory; XeLaTeX and fonts are needed only for PDF compilation.
"""
import argparse
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from dataset import DEFAULT_DATASET, load_dataset


def tex(text):
    """Escape text and give CJK characters a font plus legal line-break points."""
    escapes = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
               '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
               '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
               '/': r'/\allowbreak{}'}
    result = []
    for c in text:
        if ord(c) >= 0x2e80:
            result.append(r'{\cjkfont '+c+r'}\allowbreak{}')
        else:
            result.append(escapes.get(c, {'−':'-', '≈':r'\ensuremath{\approx}'}.get(c,c)))
    return ''.join(result)


def inline(text):
    tokens = re.split(r'(\*\*.*?\*\*|`[^`]+`)', text)
    return ''.join(r'\textbf{'+tex(t[2:-2])+'}' if t.startswith('**') else
                   r'{\small\texttt{'+tex(t[1:-1]).replace(r'\_',r'\_\allowbreak{}')+'}}' if t.startswith('`') else tex(t)
                   for t in tokens)


def pdf_geometry(svg, destination):
    """Preserve the SVG's vector paths in a small PDF; labels are typeset by LaTeX."""
    w,h = float(svg.attrib['width']),float(svg.attrib['height'])
    commands = [f'q 1 0 0 -1 0 {h} cm', '1 1 1 rg', f'0 0 {w} {h} re f']
    colors = {'red':(1,0,0),'green':(0,.5,0),'blue':(0,0,1),'black':(0,0,0),'#ddd':(.867,)*3}
    for el in svg.iter():
        if el.tag.rsplit('}',1)[-1] != 'path': continue
        stroke = el.attrib['stroke']
        color = tuple(int(stroke[i:i+2],16)/255 for i in (1,3,5)) if stroke.startswith('#') and len(stroke)==7 else colors[stroke]
        commands += [' '.join(map(str,color))+' RG',
                     el.attrib.get('stroke-width','1')+' w', '1 J',
                     '/GS gs' if 'opacity' in el.attrib else '/Solid gs']
        tokens = re.findall(r'[MLhv]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',el.attrib['d'])
        i=0; x=y=0
        while i < len(tokens):
            mode=tokens[i]; i+=1
            if mode in ('M','L'):
                x,y=map(float,tokens[i:i+2]);i+=2
                commands.append(f'{x} {y} '+('m' if mode=='M' else 'l'))
            elif mode=='h':
                x+=float(tokens[i]);i+=1;commands.append(f'{x} {y} l')
            elif mode=='v':
                y+=float(tokens[i]);i+=1;commands.append(f'{x} {y} l')
            else: raise ValueError(mode)
        commands.append('S')
    commands.append('Q')
    content=zlib.compress('\n'.join(commands).encode())
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',
             b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
             f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Contents 4 0 R /Resources << /ExtGState << /GS 5 0 R /Solid 6 0 R >> >> >>'.encode(),
             f'<< /Length {len(content)} /Filter /FlateDecode >>\nstream\n'.encode()+content+b'\nendstream',
             b'<< /Type /ExtGState /CA 0.55 >>', b'<< /Type /ExtGState /CA 1 >>']
    result=bytearray(b'%PDF-1.4\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(result)); result.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(result); result.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]: result.extend(f'{offset:010d} 00000 n \n'.encode())
    result.extend(f'trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    destination.write_bytes(result)


def figure(stem, results):
    svg=ET.parse(results/'plots'/f'{stem}.svg').getroot()
    w,h=float(svg.attrib['width']),float(svg.attrib['height'])
    pdf=results/'report'/'figures'/f'{stem}.pdf';pdf_geometry(svg,pdf)
    path=pdf.relative_to(results/'report').as_posix()
    lines=[r'\begin{figure}[p]\centering',r'\resizebox{0.98\linewidth}{!}{%',
           rf'\setlength{{\unitlength}}{{1bp}}\begin{{picture}}({w},{h})',
           rf'\put(0,0){{\includegraphics[width={w}bp,height={h}bp]{{{path}}}}}']
    for el in svg.iter():
        if el.tag.rsplit('}',1)[-1]!='text': continue
        text=tex(''.join(el.itertext()))
        size=el.attrib.get('font-size','12');color=el.attrib.get('fill','black')
        color_command = rf'\color[HTML]{{{color[1:]}}}' if color.startswith('#') else rf'\color{{{color}}}'
        style=color_command+rf'\sffamily\fontsize{{{size}}}{{{size}}}\selectfont '
        anchor={'middle':'c','end':'r'}.get(el.attrib.get('text-anchor'),'l')
        if 'transform' in el.attrib:
            x,y=map(float,re.search(r'translate\(([^,]+),([^\)]+)\)',el.attrib['transform']).groups())
            label=r'\rotatebox{90}{\makebox(0,0)[b]{'+style+text+'}}'
        else:
            x,y=float(el.attrib['x']),float(el.attrib['y'])
            label=rf'\makebox(0,0)[{anchor}b]{{{style}{text}}}'
        lines.append(rf'\put({x},{h-y}){{{label}}}')
    lines += [r'\end{picture}}',r'\end{figure}']
    return '\n'.join(lines)


def diagrams(language, results):
    suffix={'de':'','en':'_en','zh':'_zh'}[language]
    return '\n'.join(figure(stem+suffix, results) for stem in
                     ['horizontal','horizontal_detail','rotation','east_time','north_time','horizontal_time','horizontal_dage_scatter','horizontal_dage','historical_comparison','historical_comparison_detail']
                     if (results/'plots'/f'{stem}{suffix}.svg').is_file())+r'\clearpage'


def markdown_report(markdown, results):
    lines=markdown.splitlines()
    output=[];i=0;chapter=-1;language='de'
    while i<len(lines):
        line=lines[i]
        if line.startswith('# '):
            if chapter>=0: output.append(diagrams(language, results))
            chapter+=1;language=['de','en','zh'][chapter]
            output.append(r'\clearpage\section{'+inline(line[2:])+'}')
        elif line.startswith('## '): output.append(r'\subsection{'+inline(line[3:])+'}')
        elif line.startswith('```'):
            block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]);i+=1
            # Escaped text instead of verbatim so Chinese formulas also render.
            output.append(r'\begin{quote}\ttfamily\footnotesize '+r'\\'.join(tex(x) for x in block)+r'\end{quote}')
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[v.strip() for v in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',v) for v in cells): rows.append(cells)
                i+=1
            i-=1
            n=len(rows[0]);output.append(r'\begin{center}\small\begin{tabular}{l'+('r'*(n-1))+r'}\toprule')
            for j,row in enumerate(rows):
                output.append(' & '.join(inline(c) for c in row)+r'\\'+(r'\midrule' if j==0 else ''))
            output.append(r'\bottomrule\end{tabular}\end{center}')
        else: output.append(inline(line))
        i+=1
    output.append(diagrams(language, results))
    return '\n'.join(output)



def automatic_report(summary):
    """Numerical report for datasets without a manually written assessment."""
    labels=[('Turn-Table-Test','Ergebnisse','Receiver | Epochen | HRMS [mm] | Maximum [mm]',
             'Nur erhaltene RTK-fixed-Positionen werden relativ zum Sollkreis bewertet. Das Korrekturdatenalter ist keine extern protokollierte Outage-Dauer. Eine datensatzspezifische historische Bewertung liegt noch nicht vor.'),
            ('Turn-table test — English','Results','Receiver | Epochs | HRMS [mm] | Maximum [mm]',
             'The reference angle is derived from the reference receiver. Common errors and its tangential error are not independently observable. Fixed-solution availability requires a separate assessment.'),
            ('转台测试','结果','接收机 | 历元数 | HRMS [mm] | 最大值 [mm]',
             '仅评价相对于参考圆周的保留 RTK 固定解。改正龄期并非外部记录的中断时长。尚无本次数据的历史比较评价。')]
    parts=[]
    for title,heading,columns,note in labels:
        parts.extend([f"# {title} — {summary['date']}", '',
                      f"Radius: {summary['radius_m']:.6f} m. Rotation period: {summary['mean_rotation_period_s']:.3f} s.", '',
                      f'## {heading}', '', '| '+columns+' |', '|---|---:|---:|---:|'])
        for name,values in summary['statistics'].items():
            parts.append(f"| {name} | {values['epochs']} | {1000*values['rms_m']:.3f} | {1000*values['max_m']:.3f} |")
        parts.extend(['',note,''])
    return '\n'.join(parts)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=DEFAULT_DATASET)
    parser.add_argument('--results-dir','--output-dir',dest='results_dir',type=Path,
                        help='Analysis results directory, default results/<dataset-id>')
    args=parser.parse_args()
    dataset=load_dataset(args.dataset)
    results=(args.results_dir or dataset.results).resolve()
    summary=json.loads((results/'data'/'summary.json').read_text())
    if summary.get('dataset_id') != dataset.identifier or summary['date'] != dataset.date:
        parser.error('Results do not match the selected dataset; run its analysis first')
    out=results/'report'
    out.mkdir(exist_ok=True);(out/'figures').mkdir(exist_ok=True)
    markdown=dataset.assessment.read_text() if dataset.assessment else automatic_report(summary)
    preamble=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=23mm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}
\newfontfamily\cjkfont{Droid Sans Fallback}[BoldFont={Droid Sans Fallback}]
\usepackage{graphicx,xcolor,booktabs}
\usepackage[unicode,hidelinks]{hyperref}
\pdfstringdefDisableCommands{\def\cjkfont{}\def\allowbreak{}}
\hypersetup{pdftitle={Turn-table test — 2026-11-03},pdfsubject={Deutsch / English / 简体中文}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{3em}
\begin{document}
'''
    preamble=preamble.replace('2026-11-03',dataset.date)
    source=out/'turn_table_report.tex'
    source.write_text(preamble+markdown_report(markdown, results)+'\n'+r'\end{document}'+'\n',encoding='utf-8')
    if shutil.which('xelatex'):
        engine = ['xelatex']
    else:
        cache = out/'tex-cache'
        cache.mkdir(exist_ok=True)
        fmt = cache/'xelatex.fmt'
        if not fmt.exists():
            with (cache/'format-build.log').open('w') as log:
                subprocess.run(['xetex','-ini','-etex','-jobname=xelatex',
                    f'-output-directory={cache}','-progname=xelatex',
                    '-interaction=nonstopmode','-halt-on-error','xelatex.ini'],
                    cwd=out,check=True,stdout=log,stderr=subprocess.STDOUT)
        engine = ['xetex',f'-fmt={fmt}','-progname=xelatex']
    for _ in range(2):
        subprocess.run(engine + ['-interaction=nonstopmode','-halt-on-error',
                        f'-output-directory={out}',source.name],cwd=out,check=True,
                       stdout=(out/'build.log').open('w'),stderr=subprocess.STDOUT)
    print(out/'turn_table_report.pdf')

if __name__=='__main__':
    main()
