"""Shared report assembly: three editions, adjacent results and one bibliography."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from dataset import ROOT
from vertical import vertical_markdown

LANGUAGES = ('de','en','zh')
HRMS_TITLES = dict(de='HRMS über dAge und lineare Fits', en='HRMS versus dAge and linear fits', zh='HRMS 随 dAge 的变化及线性拟合')
VERTICAL_TITLES = dict(de='Vertikale Genauigkeit und VRMS', en='Vertical accuracy and VRMS', zh='垂直精度与 VRMS')
FIGURE_GROUPS = {
    'rotation': ['rotation'],
    'horizontal': ['horizontal','horizontal_detail','east_time','north_time','horizontal_time'],
    'hrms': ['horizontal_dage_scatter','horizontal_dage'],
    'vertical': ['vertical_time','vertical_time_vrms','vertical_dage_scatter','vertical_dage_vrms'],
    'historical': ['historical_comparison','historical_comparison_detail'],
}
SECTION_GROUPS = {
    'Kreis und Rotation':'rotation', 'Circle and rotation':'rotation','圆周与旋转':'rotation',
    'Fehlerstatistik aller verwendeten Fixed-Epochen':'horizontal',
    'Errors across all retained fixed epochs':'horizontal','全部保留固定解历元的误差':'horizontal',
    'Bewertung anhand der früheren Untersuchung (Punkte 1–6)':'historical',
    'Assessment against the earlier study (steps 1–6)':'historical','对照历史研究的评价（步骤 1–6）':'historical',
    **{title:'hrms' for title in HRMS_TITLES.values()},
    **{title:'vertical' for title in VERTICAL_TITLES.values()},
}


def metadata(summary, report_date=None):
    report_date=report_date or dt.date.today().isoformat()
    dt.date.fromisoformat(report_date)
    return dict(title='Turn-Table GNSS Outage Analysis', subtitle='Horizontal and Vertical Accuracy',
                author='GPT-6.1-Sol + sok', company='Feyman', report_date=report_date,
                measurement_date=summary['date'], dataset_id=summary.get('dataset_id',summary['date']),
                reference_receiver=summary.get('reference_receiver',''))


def english_date(value):
    date=dt.date.fromisoformat(value)
    months=('January','February','March','April','May','June','July','August','September','October','November','December')
    return f'{date.day} {months[date.month-1]} {date.year}'


def catalog():
    return json.loads((ROOT/'references/literature/catalog.json').read_text())


def split_chapters(markdown):
    chapters=re.findall(r'^# ([^\n]+)\n(.*?)(?=^# |\Z)',markdown,flags=re.MULTILINE|re.DOTALL)
    if len(chapters)!=3:
        raise ValueError('Report requires exactly three editions: German, English and Chinese')
    return chapters


def automatic_report(summary):
    parts=[]
    for lang,title,method,rotation,errors in [
        ('de','Deutsche Fassung','Verfahren und zeitliche Zuordnung','Kreis und Rotation','Fehlerstatistik aller verwendeten Fixed-Epochen'),
        ('en','English edition','Setup and method','Circle and rotation','Errors across all retained fixed epochs'),
        ('zh','简体中文版','测试设置与方法','圆周与旋转','全部保留固定解历元的误差')]:
        parts += [f'# {title}',f'## {method}',
                  dict(de='Ausgewertet werden erhaltene RTK-fixed-Lösungen relativ zur kontinuierlichen Referenz. Gemeinsame Fehler und deren tangentialer Eigenfehler sind nicht unabhängig beobachtbar.',
                       en='Retained RTK-fixed solutions are evaluated relative to the continuous reference. Common errors and its tangential error are not independently observable.',
                       zh='保留的 RTK 固定解相对于连续参考接收机进行评价。共同误差及参考接收机的切向误差无法独立观测。')[lang],
                  f'## {rotation}',f"Radius: {summary['radius_m']:.6f} m. T: {summary['mean_rotation_period_s']:.3f} s.",
                  f'## {errors}','| Receiver | Epochs | HRMS [mm] | Maximum [mm] |','|---|---:|---:|---:|']
        for name,v in summary['statistics'].items():
            parts.append(f"| {name} | {v['epochs']} | {1000*v['rms_m']:.3f} | {1000*v['max_m']:.3f} |")
        if 'dage_hrms' in summary:
            parts += ['## '+HRMS_TITLES[lang],dict(de='10-s-Intervalle, ungewichteter Fit mit freiem Achsenabschnitt. dAge ist das gemeldete Korrekturdatenalter.',en='10-s bins, unweighted fit with a free intercept. dAge is reported correction age.',zh='采用10秒分箱及截距自由的不加权拟合。dAge为报告的改正龄期。')[lang]]
    return '\n'.join(parts)+'\n'


def assemble(markdown, summary):
    """Place each group once and inject VRMS immediately after the HRMS section."""
    output=[]
    for lang,(_,body) in zip(LANGUAGES,split_chapters(markdown)):
        # Accept legacy assessments, but their repeated bibliographies never enter a report.
        body=re.split(r'^## (?:Referenzen und Quellenstatus|References and evidence status|参考文献与证据类型)\s*$',body,flags=re.MULTILINE)[0]
        first=re.search(r'^## ',body,flags=re.MULTILINE)
        intro=body[:first.start()].strip() if first else body.strip()
        content=body[first.start():] if first else ''
        sections=re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)',content,flags=re.MULTILINE|re.DOTALL)
        if 'vertical' in summary and HRMS_TITLES[lang] not in [title for title,_ in sections]:
            raise ValueError(f'Missing HRMS section before vertical results ({lang})')
        assembled=[]
        for title,text in sections:
            if title==VERTICAL_TITLES[lang]:
                continue # The data-derived section is inserted exactly once below.
            assembled.append((title,text))
            if title==HRMS_TITLES[lang] and 'vertical' in summary:
                vertical=vertical_markdown(summary,lang)
                _,vbody=vertical.split('\n',1)
                assembled.append((VERTICAL_TITLES[lang],vbody))
        edition={'de':'Deutsche Fassung','en':'English edition','zh':'简体中文版'}[lang]
        chapter=[f'# {edition} — {summary["date"]}','']
        for title,text in assembled:
            chapter += ['## '+title,'',text.strip(),'']
            if title in ('Verfahren und zeitliche Zuordnung','Method and time alignment','Messaufbau und Methode','Setup and method','方法与时间对齐','测试设置与方法') and ':::equation circle' not in text:
                chapter += [':::equation circle','']
            group=SECTION_GROUPS.get(title)
            if group=='hrms':
                chapter += [dict(de='Für ein Intervall enthält B_j die n_j verwendeten Epochen. Alle Fehler werden vor der Statistik in dieselbe Längeneinheit umgerechnet. Im Fit sind y_j die Intervall-RMS-Werte in mm und x_j das mittlere beobachtete Alter in s; jeder Bin erhält dasselbe Gewicht.',
                                 en='For each bin, B_j contains its n_j eligible epochs. Errors use one consistent length unit before statistics are computed. In the fit, y_j denotes bin RMS in mm and x_j the mean observed age in s; bins have equal weight.',
                                 zh='B_j为该区间的n_j个有效历元。统计前将误差换算到一致的长度单位。拟合中y_j为毫米单位的区间RMS，x_j为秒单位的平均观测龄期；各区间权重相同。')[lang],
                            '', ':::equation hrms','',':::equation fit','']
            elif group=='vertical':
                chapter += [':::equation height','',':::equation vrms','',':::equation bias','']
            if group:
                chapter += [':::figures '+group,'']
        if intro:
            chapter += ['## '+{'de':'Reproduzierbarkeit und Datenausgabe','en':'Reproducibility and data outputs','zh':'可复现性与数据输出'}[lang],'',intro,'']
        output.append('\n'.join(chapter))
    document='\n'.join(output)
    used=set(re.findall(r'\[(R\d+)\]',document))
    records=catalog()
    missing=used-{r['id'] for r in records}
    if missing:
        raise ValueError('Unknown reference IDs: '+', '.join(sorted(missing)))
    return document,records


def source_links(entry, base):
    """Portable source links; local sources must remain inside the repository."""
    links=[]
    if entry.get('url'):
        if not entry['url'].startswith(('http://','https://')):
            raise ValueError('Unsupported bibliography URL')
        links.append(('Publisher',entry['url']))
    for key,label in [('local_file','Source PDF'),('editable_file','Source DOCX'),('related_image','Companion image')]:
        if entry.get(key):
            source=(ROOT/entry[key]).resolve()
            source.relative_to(ROOT.resolve())
            if not source.is_file():raise ValueError(f'Missing source: {source}')
            links.append((label,Path(os.path.relpath(source,base)).as_posix()))
    if entry.get('full_text_url'):
        if not entry['full_text_url'].startswith(('http://','https://')):
            raise ValueError('Unsupported full-text URL')
        links.append(('Full text',entry['full_text_url']))
    return links


def bibliography_html(entries, base):
    parts=['<section class="references" lang="en"><h1>References</h1>',
           '<p>One shared bibliography for all three editions. Source records identify research, manufacturer documentation and project-owner material. Local files are linked relative to this report.</p>']
    for entry in entries:
        links=source_links(entry,base)
        target=links[0][1] if links else None
        title=html.escape(entry['title'])
        if target:title=f'<a href="{html.escape(target,quote=True)}">{title}</a>'
        parts += [f'<article class="reference" id="ref-{entry["id"]}"><p><strong>[{entry["id"]}]</strong> '+html.escape(entry['authors'])+' ('+html.escape(entry['date'])+'). '+title+'. '+html.escape(entry.get('evidence_type',''))+'.</p>']
        extra=[]
        for label,url in links:
            extra.append(f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>')
        doi=entry.get('doi') or (entry.get('url','').split('doi.org/',1)[1] if 'doi.org/' in entry.get('url','') else '')
        if doi:extra.append(f'<a href="https://doi.org/{html.escape(doi,quote=True)}">DOI: {html.escape(doi)}</a>')
        if entry.get('verified_date'):extra.append('Verified '+english_date(entry['verified_date']))
        parts += ['<p class="source-links">'+' · '.join(extra)+'</p></article>']
    parts.append('</section>')
    return ''.join(parts)


def write_html_report(output, summary, assessment=None, report_date=None):
    from report_languages import translate
    from report_markdown import add_contents, markdown_html
    output=Path(output)
    raw=Path(assessment).read_text() if assessment else automatic_report(summary)
    markdown,entries=assemble(raw,summary)
    meta=metadata(summary,report_date)
    for language in ('en','zh'):
        for source in sorted((output/'plots').glob('*.svg')):
            if source.stem.endswith(('_en','_zh')):continue
            destination=source.with_name(f'{source.stem}_{language}.svg')
            translated=translate(source.read_text(),language)
            if not destination.exists() or destination.read_text()!=translated:
                destination.write_text(translated)
    parts=[]
    for lang,(title,body) in zip(LANGUAGES,split_chapters(markdown)):
        count=[0]
        def figures(group):
            result=[]
            for stem in FIGURE_GROUPS[group]:
                suffix={'de':'','en':'_en','zh':'_zh'}[lang]
                svg=output/'plots'/f'{stem}{suffix}.svg'
                if not svg.is_file():continue
                count[0]+=1
                root=ET.parse(svg).getroot()
                caption=''.join(next(el for el in root.iter() if el.tag.rsplit('}',1)[-1]=='text').itertext())
                number=f'{LANGUAGES.index(lang)+1}.{count[0]}'
                label={'de':'Abbildung','en':'Figure','zh':'图'}[lang]
                result.append(f'<figure id="fig-{lang}-{stem}"><a href="plots/{svg.name}"><img src="plots/{svg.name}" alt="{html.escape(caption,quote=True)}"></a><figcaption>{label} {number}. {html.escape(caption)}</figcaption></figure>')
            return ''.join(result)
        tag='zh-Hans' if lang=='zh' else lang
        parts.append(f'<section class="language-edition" lang="{tag}">'+markdown_html('# '+title+'\n'+body,figures=figures)+'</section>')
    cover='<header class="title-page" lang="en"><p class="brand">Feyman</p><h1 data-no-toc="true">'+meta['title']+'</h1><p class="subtitle">'+meta['subtitle']+'</p><dl>'+''.join('<dt>'+label+'</dt><dd>'+html.escape(value)+'</dd>' for label,value in [
        ('Author',meta['author']),('Company',meta['company']),('Report date',english_date(meta['report_date'])),
        ('Measurement date',english_date(meta['measurement_date'])),('Dataset',meta['dataset_id']),('Reference receiver',meta['reference_receiver'])])+'</dl><p class="scope">Relative accuracy of retained RTK-fixed solutions under correction-data outages. German, English and Simplified Chinese editions with a shared English bibliography.</p></header>'
    style='''body{font-family:system-ui,sans-serif;max-width:1080px;margin:auto;padding:2rem;color:#18212b;line-height:1.6}h1,h2,h3{line-height:1.25;color:#163b5c}h2{margin-top:2.5rem;border-bottom:1px solid #ccd4dd;padding-bottom:.4rem}.title-page{text-align:center;padding:4rem 1rem;min-height:65vh}.brand{font-size:1.5rem;letter-spacing:.2em}.title-page h1{font-size:2.6rem}.subtitle{font-size:1.4rem}.title-page dl{display:grid;grid-template-columns:1fr 1fr;max-width:560px;margin:3rem auto;gap:.5rem 1.5rem;text-align:left}.title-page dt{text-align:right;font-weight:bold}.title-page dd{margin:0}.scope{max-width:700px;margin:2rem auto;color:#4c5a68}nav{border-block:1px solid #ccd4dd;padding:1rem 0}nav ul{list-style:none;padding:0}.language-edition{margin-top:4rem}table{border-collapse:collapse;max-width:100%;font-size:.94rem;margin:1.4rem auto}td,th{padding:.45rem .7rem;border-bottom:1px solid #d5dce3}th{background:#f0f4f7}figure{margin:2rem 0;break-inside:avoid}figure img{display:block;width:auto;max-width:100%;max-height:780px;margin:auto}figcaption{font-size:.9rem;color:#4c5a68;margin:.5rem 0;text-align:center}.equation{margin:1.5rem 0;overflow:auto}math{font-size:1.15rem}pre{overflow:auto;background:#f3f5f7;padding:1rem}a{color:#155c98}.reference{padding:.5rem 0;border-bottom:1px solid #e3e7eb}.source-links{font-size:.88rem}p{overflow-wrap:break-word}@media print{.title-page{break-after:page}nav{break-after:page}.language-edition,.references{break-before:page}body{max-width:none;padding:0}a{color:inherit}}'''
    document='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="author" content="'+html.escape(meta['author'],quote=True)+'"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+meta['title']+' — '+meta['measurement_date']+'</title><style>'+style+'</style></head><body>'+cover+'<!--CONTENTS-->'+''.join(parts)+bibliography_html(entries,output)+'</body></html>'
    (output/'index.html').write_text(add_contents(document))
    return meta
