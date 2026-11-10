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
from report_document import (assemble, metadata, english_date, source_links, FIGURE_GROUPS, automatic_report)
from report_equations import equation_latex


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
    tokens = re.split(r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\(https?://[^\s)]+\)|\[R\d+\])', text)
    result=[]
    for token in tokens:
        if token.startswith('**'):
            result.append(r'\textbf{'+inline(token[2:-2])+'}')
        elif token.startswith('`'):
            result.append(r'{\small\texttt{'+tex(token[1:-1]).replace(r'\_',r'\_\allowbreak{}')+'}}')
        elif re.fullmatch(r'\[R\d+\](?:\(https?://[^\s)]+\))?',token):
            ref=re.match(r'\[(R\d+)\]',token)[1]
            result.append(r'\hyperlink{ref-'+ref+'}{['+ref+']}')
        elif (match:=re.fullmatch(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',token)):
            url=match[2].replace('%',r'\%').replace('#',r'\#')
            result.append(r'\href{'+url+'}{'+tex(match[1])+'}')
        else:
            result.append(tex(token))
    return ''.join(result)



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


def figure(stem, results, reuse_geometry=False, inline_figure=False, language="en"):
    svg=ET.parse(results/'plots'/f'{stem}.svg').getroot()
    w,h=float(svg.attrib['width']),float(svg.attrib['height'])
    pdf=results/'report'/'figures'/f'{stem}.pdf'
    if not reuse_geometry or not pdf.is_file() or pdf.stat().st_mtime < (results/'plots'/f'{stem}.svg').stat().st_mtime:
        pdf_geometry(svg,pdf)
    path=pdf.relative_to(results/'report').as_posix()
    opening=r'\begin{center}\begin{minipage}{\linewidth}\centering' if inline_figure else r'\begin{figure}[p]\centering'
    lines=[opening,r'\resizebox{0.98\linewidth}{!}{%',
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
    caption=''.join(next(el for el in svg.iter() if el.tag.rsplit('}',1)[-1]=='text').itertext())
    lines.append(r'\end{picture}}')
    if inline_figure:
        label={'de':'Abbildung','en':'Figure','zh':'图'}[language]
        lines += [r'\par\smallskip\refstepcounter{figure}{\small '+tex(label)+r'~\thefigure. '+tex(caption)+r'\par}',r'\end{minipage}\end{center}']
    else:
        lines += [r'\caption{'+tex(caption)+'}',r'\end{figure}']
    return '\n'.join(lines)


def diagrams(language, results, reuse_geometry=False):
    suffix={'de':'','en':'_en','zh':'_zh'}[language]
    return '\n'.join(figure(stem+suffix, results, reuse_geometry) for stem in
                     ['horizontal','horizontal_detail','rotation','east_time','north_time','horizontal_time','vertical_time','vertical_time_vrms','vertical_dage_scatter','vertical_dage_vrms','horizontal_dage_scatter','horizontal_dage','historical_comparison','historical_comparison_detail']
                     if (results/'plots'/f'{stem}{suffix}.svg').is_file())+r'\clearpage'


def markdown_report(markdown, results, reuse_geometry=False):
    lines=markdown.splitlines()
    output=[];i=0;chapter=-1;language='de'
    while i<len(lines):
        line=lines[i]
        if line.startswith('# '):
            chapter+=1;language=['de','en','zh'][chapter]
            output.append(r'\clearpage\section{'+inline(line[2:])+'}')
        elif line.startswith(':::equation '):
            name=line.split(maxsplit=1)[1]
            output.append(r'\begin{equation}'+equation_latex(name)+r'\label{eq:'+language+'-'+name+r'}\end{equation}')
        elif line.startswith(':::figures '):
            group=line.split(maxsplit=1)[1]
            suffix={'de':'','en':'_en','zh':'_zh'}[language]
            output.extend(figure(stem+suffix,results,reuse_geometry,inline_figure=True,language=language)
                          for stem in FIGURE_GROUPS[group] if (results/'plots'/f'{stem}{suffix}.svg').is_file())
        elif line.startswith('### '): output.append(r'\subsubsection{'+inline(line[4:])+'}')
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
            n=len(rows[0]);output.append(r'\begin{center}\begin{lrbox}{\reporttable}\small\setlength{\tabcolsep}{4pt}\begin{tabular}{l'+('r'*(n-1))+r'}\toprule')
            for j,row in enumerate(rows):
                output.append(' & '.join(inline(c) for c in row)+r'\\'+(r'\midrule' if j==0 else ''))
            output.append(r'\bottomrule\end{tabular}\end{lrbox}\ifdim\wd\reporttable>\linewidth\resizebox{\linewidth}{!}{\usebox{\reporttable}}\else\usebox{\reporttable}\fi\end{center}')
        else: output.append(inline(line))
        i+=1
    return '\n'.join(output)





def title_page(meta):
    rows=[('Author',meta['author']),('Company',meta['company']),
          ('Report date',english_date(meta['report_date'])),
          ('Measurement date',english_date(meta['measurement_date'])),
          ('Dataset',meta['dataset_id']),('Reference receiver',meta['reference_receiver'])]
    table='\n'.join(r'\textbf{'+tex(label)+r'} & '+tex(value)+r'\\[7pt]' for label,value in rows)
    return r"""\hypersetup{pageanchor=false}
\begin{titlepage}
\centering
\vspace*{15mm}
{\Large\sffamily\color{reportblue} Feyman\par}
\vspace{22mm}
{\Huge\bfseries\color{reportblue} Turn-Table GNSS\\[5mm]Outage Analysis\par}
\vspace{8mm}
{\Large Horizontal and Vertical Accuracy\par}
\vspace{12mm}
{\color{reportblue}\rule{0.8\linewidth}{1pt}\par}
\vspace{12mm}
\begin{tabular}{rp{0.65\linewidth}}
"""+table+r"""
\end{tabular}
\vfill
\begin{minipage}{0.87\linewidth}\centering\small
Relative accuracy of retained RTK-fixed solutions under correction-data outages.
German, English and Simplified Chinese editions with one shared English bibliography.
\end{minipage}
\vspace{15mm}
\end{titlepage}
\hypersetup{pageanchor=true}
"""


def contents_page():
    return r"""\pagenumbering{roman}
\setcounter{tocdepth}{2}
\makeatletter
\renewcommand*\l@subsection{\@dottedtocline{2}{1.5em}{3.2em}}
\makeatother
\renewcommand{\contentsname}{Contents / Inhaltsverzeichnis / {\cjkfont 目录}}
{\small\tableofcontents}
\clearpage
\pagenumbering{arabic}
"""


def bibliography(entries, base):
    lines=[r'\clearpage\section{References}',
           'One shared bibliography for all three editions. Evidence scopes distinguish research, manufacturer documentation and project-owner material. Source files are linked relative to this report.', '']
    for entry in entries:
        links=source_links(entry,base)
        target=links[0][1] if links else ''
        def link(url,label):
            return r'\href{'+url.replace('%',r'\%').replace('#',r'\#')+'}{'+tex(label)+'}'
        title=link(target,entry['title']) if target else tex(entry['title'])
        lines.append(r'\begin{samepage}\noindent\hangindent=4em\hangafter=1\makebox[4em][l]{\hypertarget{ref-'+entry['id']+r'}{\textbf{['+entry['id']+']}}}'+tex(entry['authors'])+' ('+tex(entry['date'])+'). '+title+'. '+tex(entry.get('evidence_type',''))+'.')
        details=[link(url,label) for label,url in links]
        doi=entry.get('doi') or (entry.get('url','').split('doi.org/',1)[1] if 'doi.org/' in entry.get('url','') else '')
        if doi:details.append(link('https://doi.org/'+doi,'DOI: '+doi))
        if entry.get('verified_date'):details.append('Verified '+english_date(entry['verified_date']))
        lines += [r'{\small '+'; '.join(details)+r'\par}',r'\end{samepage}\medskip']
    return '\n'.join(lines)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=DEFAULT_DATASET)
    parser.add_argument('--report-date',help='Report issue date (ISO YYYY-MM-DD); measurement date remains dataset-specific')
    parser.add_argument('--reuse-figures', action='store_true',
                        help='Reuse geometry PDFs newer than their SVGs for layout-only rebuilds; omit after converter changes')
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
    markdown, references = assemble(markdown, summary)
    meta = metadata(summary, args.report_date)
    from report_document import write_html_report
    write_html_report(results, summary, dataset.assessment, meta['report_date'])
    preamble=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=23mm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}
\newfontfamily\cjkfont{Droid Sans Fallback}[BoldFont={Droid Sans Fallback}]
\usepackage{graphicx,xcolor,booktabs,amsmath}
\usepackage[unicode,hidelinks]{hyperref}
\pdfstringdefDisableCommands{\def\cjkfont{}\def\allowbreak{}}
\hypersetup{pdftitle={Turn-Table GNSS Outage Analysis — 2026-11-03},pdfauthor={REPORT_AUTHOR},pdfsubject={Feyman: horizontal and vertical RTK outage accuracy},pdfkeywords={GNSS, RTK, outage, HRMS, VRMS}}
\definecolor{reportblue}{HTML}{163B5C}
\hypersetup{colorlinks=true,linkcolor=reportblue,urlcolor=reportblue,citecolor=reportblue,filecolor=reportblue}
\newsavebox{\reporttable}
\numberwithin{equation}{section}
\numberwithin{figure}{section}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{3em}
\begin{document}
'''
    preamble=preamble.replace('2026-11-03',dataset.date).replace('REPORT_AUTHOR',tex(meta['author']))
    source=out/'turn_table_report.tex'
    source.write_text(preamble+title_page(meta)+contents_page()+markdown_report(markdown, results, args.reuse_figures)+'\n'+bibliography(references,out)+r'\end{document}'+'\n',encoding='utf-8')
    (out/'report_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
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
    # Resolve contents/page references before converting the large vector plots to PDF.
    for pass_index in range(3):
        output_mode = ['-no-pdf'] if pass_index < 2 else []
        subprocess.run(engine + output_mode + ['-interaction=nonstopmode','-halt-on-error',
                        f'-output-directory={out}',source.name],cwd=out,check=True,
                       stdout=(out/'build.log').open('w'),stderr=subprocess.STDOUT)
    print(out/'turn_table_report.pdf')

if __name__=='__main__':
    main()
