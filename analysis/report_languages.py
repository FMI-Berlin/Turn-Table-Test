"""Additional English and Simplified Chinese report chapters and SVG labels."""
from pathlib import Path
import json
import datetime as dt
import html
import re

from report_markdown import add_contents, markdown_html
from vertical import vertical_markdown

# Exact report/axis phrases; numeric data and machine-readable field names stay unchanged.
TRANSLATIONS = {
'en': {
'Vertikale Abweichung [mm]':'Vertical residual [mm]',
'Vertikale Abweichung über der Zeit':'Vertical residual over time',
'Vertikale Abweichung über dAge: alle RTK-fixed-Einzelwerte':'Vertical residual versus dAge: all RTK-fixed samples',
'Vertikaler RMS VRMS [mm]':'Vertical RMS VRMS [mm]',
'VRMS über dAge: 10-s-Intervalle und linearer Fit':'VRMS versus dAge: 10-s bins and linear fit',
'VRMS über Zeit: 60-s-Intervalle und linearer Fit':'VRMS versus time: 60-s bins and linear fit',
'Diagramme':'Plots',
'Vergleich mit Abbildung 1, Seite 2 von „trimble-report.pdf“: Alte Kurven sind aus PDF-Vektorlinien rekonstruierte Näherungen, keine Rohmesswerte. Der einzelne Punkt bei 300 s und etwa 20 mm verwendet finale präzise Uhren und Bahnen. Neu: HRMS je 10-s-Intervall und lineare Fits nur im gemessenen Altersbereich. Unterschiedliche Versuchsbedingungen und Referenzen begrenzen die Vergleichbarkeit. Die Detailansicht zeigt die zwei niedrigeren alten Kurven und den präzisen Uhrenpunkt; alle alten Kurven stehen in der Gesamtansicht.':'Comparison with Figure 1, page 2 of “trimble-report.pdf”: historical curves are approximate reconstructions from PDF vector paths, not raw observations. The isolated point near 300 s and 20 mm uses final precise clocks and orbits. New results show 10-s-bin HRMS and linear fits restricted to observed ages. Different experimental conditions and references limit comparability. The detail view shows the two lower historical curves and the precise-clock point; the full view includes every historical curve.',
'Alt: ohne SV-Uhr':'Earlier: no SV clock',
'Alt: SV-Uhr + Relativität':'Earlier: SV clock + relativity',
'Alt: SV-Uhr':'Earlier: SV clock',
'Alt: + Ultra-Rapid':'Earlier: + ultra-rapid',
'Alt: + präzise Bahnen':'Earlier: + precise orbits',
'Alt: präzise Uhren (ein Punkt)':'Earlier: precise clocks (one point)',
'HRMS(dAge): frühere Untersuchung und neue Ergebnisse':'HRMS(dAge): earlier study and new results',
'HRMS(dAge): Vergleich im Detail (0–300 s, 0–150 mm)':'HRMS(dAge): comparison detail (0–300 s, 0–150 mm)',
'Horizontaler Fehler über dAge: alle RTK-fixed-Einzelwerte':'Horizontal error versus dAge: all RTK-fixed samples',
'Horizontaler Fehler [mm]':'Horizontal error [mm]',
'dAge ist das gemeldete GGA-Korrekturdatenalter [s]. HRMS = sqrt(Mittelwert(Ostfehler² + Nordfehler²)) je 10-s-Intervall (0,10], (10,20], …; dAge=0 zählt zum ersten Intervall. Punkte liegen beim mittleren dAge je Intervall. Die Geraden werden ungewichtet an die Intervall-HRMS-Werte angepasst, mit freiem Achsenabschnitt und nur im belegten Altersbereich; ihre Steigungen stehen in mm/s. Alle verwendbaren RTK-fixed-Epochen mit gültigem dAge sind enthalten, ohne Paarung der Receiver. dAge ist keine extern gemessene Outage-Dauer.':'dAge is the reported GGA correction age [s]. HRMS = sqrt(mean(east error² + north error²)) per 10-s interval (0,10], (10,20], …; age zero belongs to the first interval. Points use the mean observed age in each interval. Lines use unweighted least squares on interval HRMS values with a free intercept, restricted to the observed age range; slopes are in mm/s. All usable RTK-fixed epochs with valid dAge are included, without pairing receivers. dAge is not an externally measured outage duration.',
'HRMS über dAge: 10-s-Intervalle und linearer Fit':'HRMS versus dAge: 10-s bins and linear fit',
'Horizontaler RMS-Fehler HRMS [mm]':'Horizontal RMS error HRMS [mm]',
'Korrekturdatenalter dAge [s]':'Correction age dAge [s]',
'Horizontaler Fehler über dAge (nur RTK-fixed)':'Horizontal error versus dAge (RTK-fixed only)',
'dAge ist das gemeldete Korrekturdatenalter aus GGA in Sekunden, nicht die extern gemessene Outage-Dauer. Jeder Punkt zeigt den horizontalen Fehler einer RTK-fixed-Epoche mit gültigem dAge; fehlende oder ungültige Alterswerte werden ausgelassen. Alle drei Receiver sind enthalten, ohne Beschränkung auf gemeinsame Outage-Epochen.':'dAge is the reported GGA correction age in seconds, not an externally measured outage duration. Each point shows the horizontal error of an RTK-fixed epoch with a valid dAge; missing or invalid ages are omitted. All three receivers are included, without restricting the plot to paired outage epochs.',
'Mittlere Umdrehungsdauer:':'Mean rotation period:',
'vollständige Umdrehungen, ohne Referenzlücken':'complete revolutions, excluding reference gaps',
'Turn-Table-Test':'Turn-table test',
'Radius:':'Radius:', ' bis ':' to ', 'Datum:':'Date:',
'(aus UM980; gleicher Tag für P23A angenommen).':'(from UM980; the same date is assumed for P23A).',
'Rot: P23A_0; grün: P23A_1; blau: UM980; schwarzes Kreuz: Sollposition.':'Red: P23A_0; green: P23A_1; blue: UM980; black cross: expected position.',
'Nur RTK-fixed-Positionen (GGA-Qualität 4) sind enthalten. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360° als Anzahl der Vollkreise.':'Only RTK-fixed positions (GGA quality 4) are included. The rotation plot shows the angle divided by 360° as the number of revolutions.',
'Der Referenzwinkel wird aus P23A_0 abgeleitet. Dessen tangentialer Fehler ist damit nicht unabhängig messbar; die rote Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken. Keine nachträgliche Zeitverschiebung der Empfänger. Über Referenzlücken ist die Anzahl ganzer Umdrehungen unbekannt; der entfaltete Winkel setzt danach mit dem nächstliegenden Winkel fort (Segmentnummer in reference_angle.csv).':'The reference angle is derived from P23A_0. Its tangential error cannot be measured independently; the red trace mainly shows the radial residual. There is no extrapolation or interpolation across large reference gaps and no subsequent receiver time shift. The number of complete turns during reference gaps is unknown; the unwrapped angle resumes at the nearest equivalent angle (segment number in reference_angle.csv).',
'Ost-Abweichung [m]':'East error [m]', 'Nord-Abweichung [m]':'North error [m]',
'Horizontale Abweichungen vom zeitgleichen Sollkreis':'Horizontal errors relative to the time-aligned expected circle',
'Detail ±0,10 m (größere Abweichungen ausgeblendet)':'Detail ±0.10 m (larger errors hidden)',
'Zeit seit gemeinsamem Beginn [min]':'Time since common start [min]',
'Anzahl der Vollkreise seit erstem Referenzpunkt':'Revolutions since first reference point',
'Umdrehungen: positiv von Ost nach Nord':'Revolutions: positive from east towards north',
'Horizontal-Abweichung [m]':'Horizontal error [m]',
'Ost-Abweichung über der Zeit':'East error over time',
'Nord-Abweichung über der Zeit':'North error over time',
'Horizontal-Abweichung über der Zeit':'Horizontal error over time',
'Soll (0,0)':'Expected (0,0)',
},
'zh': {
'Vertikale Abweichung [mm]':'垂直残差 [mm]',
'Vertikale Abweichung über der Zeit':'垂直残差随时间的变化',
'Vertikale Abweichung über dAge: alle RTK-fixed-Einzelwerte':'垂直残差随 dAge 的变化：全部 RTK 固定解单点值',
'Vertikaler RMS VRMS [mm]':'垂直均方根 VRMS [mm]',
'VRMS über dAge: 10-s-Intervalle und linearer Fit':'VRMS 随 dAge 的变化：10 秒区间及线性拟合',
'VRMS über Zeit: 60-s-Intervalle und linearer Fit':'VRMS 随时间的变化：60 秒区间及线性拟合',
'Diagramme':'图表',
'Vergleich mit Abbildung 1, Seite 2 von „trimble-report.pdf“: Alte Kurven sind aus PDF-Vektorlinien rekonstruierte Näherungen, keine Rohmesswerte. Der einzelne Punkt bei 300 s und etwa 20 mm verwendet finale präzise Uhren und Bahnen. Neu: HRMS je 10-s-Intervall und lineare Fits nur im gemessenen Altersbereich. Unterschiedliche Versuchsbedingungen und Referenzen begrenzen die Vergleichbarkeit. Die Detailansicht zeigt die zwei niedrigeren alten Kurven und den präzisen Uhrenpunkt; alle alten Kurven stehen in der Gesamtansicht.':'与“trimble-report.pdf”第 2 页图 1 对比：历史曲线由 PDF 矢量线近似重建，并非原始观测数据。约 300 秒、20 mm 的孤立点使用最终精密钟差和轨道。新结果为每 10 秒区间的 HRMS 及仅限实际龄期范围的线性拟合。实验条件和参考基准不同，限制了可比性。局部图显示两条较低的历史曲线和精密钟差点；完整图包含全部历史曲线。',
'Alt: ohne SV-Uhr':'历史：无卫星钟差',
'Alt: SV-Uhr + Relativität':'历史：卫星钟差及相对论修正',
'Alt: SV-Uhr':'历史：卫星钟差',
'Alt: + Ultra-Rapid':'历史：加超快速产品',
'Alt: + präzise Bahnen':'历史：加精密轨道',
'Alt: präzise Uhren (ein Punkt)':'历史：精密钟差（单点）',
'HRMS(dAge): frühere Untersuchung und neue Ergebnisse':'HRMS(dAge)：历史研究与新结果',
'HRMS(dAge): Vergleich im Detail (0–300 s, 0–150 mm)':'HRMS(dAge)：局部对比（0–300 秒，0–150 mm）',
'Horizontaler Fehler über dAge: alle RTK-fixed-Einzelwerte':'水平误差随 dAge 的变化：全部 RTK 固定解单点值',
'Horizontaler Fehler [mm]':'水平误差 [mm]',
'dAge ist das gemeldete GGA-Korrekturdatenalter [s]. HRMS = sqrt(Mittelwert(Ostfehler² + Nordfehler²)) je 10-s-Intervall (0,10], (10,20], …; dAge=0 zählt zum ersten Intervall. Punkte liegen beim mittleren dAge je Intervall. Die Geraden werden ungewichtet an die Intervall-HRMS-Werte angepasst, mit freiem Achsenabschnitt und nur im belegten Altersbereich; ihre Steigungen stehen in mm/s. Alle verwendbaren RTK-fixed-Epochen mit gültigem dAge sind enthalten, ohne Paarung der Receiver. dAge ist keine extern gemessene Outage-Dauer.':'dAge 为 GGA 报告的改正数据龄期 [s]。每个 10 秒区间 (0,10]、(10,20] 等计算 HRMS = sqrt(平均值(东向误差² + 北向误差²))；零龄期计入首个区间。点的横坐标为各区间的平均龄期。对各区间 HRMS 采用不加权最小二乘直线拟合，截距自由，仅在实际龄期范围内绘制，斜率单位为 mm/s。包含具有有效 dAge 的全部可用 RTK 固定解历元，不要求接收机历元配对。dAge 并非外部测得的中断持续时间。',
'HRMS über dAge: 10-s-Intervalle und linearer Fit':'HRMS 随 dAge 的变化：10 秒区间及线性拟合',
'Horizontaler RMS-Fehler HRMS [mm]':'水平均方根误差 HRMS [mm]',
'Korrekturdatenalter dAge [s]':'改正数据龄期 dAge [s]',
'Horizontaler Fehler über dAge (nur RTK-fixed)':'水平误差随 dAge 的变化（仅 RTK 固定解）',
'dAge ist das gemeldete Korrekturdatenalter aus GGA in Sekunden, nicht die extern gemessene Outage-Dauer. Jeder Punkt zeigt den horizontalen Fehler einer RTK-fixed-Epoche mit gültigem dAge; fehlende oder ungültige Alterswerte werden ausgelassen. Alle drei Receiver sind enthalten, ohne Beschränkung auf gemeinsame Outage-Epochen.':'dAge 是 GGA 报告的改正数据龄期，单位为秒，并非外部测得的中断持续时间。每个点表示具有有效 dAge 的一个 RTK 固定解历元的水平误差；缺失或无效的龄期不予绘制。图中包含全部三个接收机，不限于配对的中断历元。',
'Mittlere Umdrehungsdauer:':'平均旋转周期：',
'vollständige Umdrehungen, ohne Referenzlücken':'次完整旋转，已排除参考数据缺口',
'Turn-Table-Test':'转台测试', 'Radius:':'半径：', ' bis ':' 至 ', 'Datum:':'日期：',
'(aus UM980; gleicher Tag für P23A angenommen).':'（来自 UM980；假定 P23A 的数据采集于同一天）。',
'Rot: P23A_0; grün: P23A_1; blau: UM980; schwarzes Kreuz: Sollposition.':'红色：P23A_0；绿色：P23A_1；蓝色：UM980；黑色十字：理论位置。',
'Nur RTK-fixed-Positionen (GGA-Qualität 4) sind enthalten. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360° als Anzahl der Vollkreise.':'仅包含 RTK 固定解位置（GGA 质量标识为 4）。旋转图以转角除以 360°，表示旋转圈数。',
'Der Referenzwinkel wird aus P23A_0 abgeleitet. Dessen tangentialer Fehler ist damit nicht unabhängig messbar; die rote Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken. Keine nachträgliche Zeitverschiebung der Empfänger. Über Referenzlücken ist die Anzahl ganzer Umdrehungen unbekannt; der entfaltete Winkel setzt danach mit dem nächstliegenden Winkel fort (Segmentnummer in reference_angle.csv).':'参考角由 P23A_0 推导，因此无法独立测量其切向误差；红色轨迹主要表示径向残差。不进行外推，也不跨越较大的参考数据缺口进行插值，不对接收机时间进行事后平移。参考数据缺口期间的完整旋转圈数未知；缺口后展开角采用最接近的等效角继续（分段编号见 reference_angle.csv）。',
'Ost-Abweichung [m]':'东向误差 [m]', 'Nord-Abweichung [m]':'北向误差 [m]',
'Horizontale Abweichungen vom zeitgleichen Sollkreis':'相对于同一时刻理论圆周位置的水平误差',
'Detail ±0,10 m (größere Abweichungen ausgeblendet)':'局部视图 ±0.10 m（不显示范围外的误差）',
'Zeit seit gemeinsamem Beginn [min]':'自共同起始时刻起的时间 [min]',
'Anzahl der Vollkreise seit erstem Referenzpunkt':'自首个参考点起的旋转圈数',
'Umdrehungen: positiv von Ost nach Nord':'旋转圈数：从东向北为正方向',
'Horizontal-Abweichung [m]':'水平误差 [m]',
'Ost-Abweichung über der Zeit':'东向误差随时间的变化',
'Nord-Abweichung über der Zeit':'北向误差随时间的变化',
'Horizontal-Abweichung über der Zeit':'水平误差随时间的变化',
'Soll (0,0)':'理论值 (0,0)',
}}

def translate(text, language):
    for source, target in sorted(TRANSLATIONS[language].items(), key=lambda item: -len(item[0])):
        text = text.replace(source, target)
    return text


def report_intro(summary, language):
    """Dataset-derived metadata and legend; no assumed receiver count or names."""
    reference=html.escape(summary.get('reference_receiver', next(iter(summary['files']))))
    colors=summary.get('receiver_colors', {})
    legend='; '.join(f'<span style="color:{colors.get(name,"black")}">{html.escape(name)}</span>' for name in summary['files'])
    values=(summary['radius_m'],summary['mean_rotation_period_s'],summary['rotation_period_count'],
            str(dt.timedelta(seconds=summary['common_start_utc_seconds'])),
            str(dt.timedelta(seconds=summary['common_end_utc_seconds'])),summary['date'])
    metadata={
        'de': 'Radius: {:.6f} m. Mittlere Umdrehungsdauer: {:.3f} s ({} vollständige Umdrehungen). UTC: {} bis {}. Datum: {} (Konfiguration, mit vorhandenen RMC-Daten abgeglichen).',
        'en': 'Radius: {:.6f} m. Mean rotation period: {:.3f} s ({} complete revolutions). UTC: {} to {}. Date: {} (configuration, checked against available RMC dates).',
        'zh': '半径：{:.6f} m。平均旋转周期：{:.3f} s（{} 次完整旋转）。UTC：{} 至 {}。日期：{}（配置日期，已与可用 RMC 日期核对）。',
    }
    notes={
        'de': 'Nur RTK-fixed-Positionen (GGA-Qualität 4) werden verwendet. Das schwarze Kreuz markiert den Ursprung. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360°. Referenz: {}. Ihr tangentialer Eigenfehler ist nicht unabhängig messbar; ihre Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken und keine nachträgliche Zeitverschiebung. Ganze Umdrehungen über Referenzlücken bleiben unbekannt (reference_angle.csv).',
        'en': 'Only RTK-fixed positions (GGA quality 4) are included. The black cross marks the origin. The rotation plot shows angle divided by 360°. Reference: {}. Its tangential error is not independently observable; its trace mainly represents radial residuals. No extrapolation or interpolation across large reference gaps and no subsequent time shift. Complete turns across reference gaps remain unknown (reference_angle.csv).',
        'zh': '仅采用 RTK 固定解（GGA 质量 4）。黑色十字标出原点。旋转图表示转角除以 360°。参考接收机：{}。其切向误差无法独立观测，其轨迹主要反映径向残差。不进行外推、不跨越较大参考缺口插值，也不事后平移时间。参考缺口期间完整旋转圈数未知（reference_angle.csv）。',
    }
    return '<p>'+metadata[language].format(*values)+'</p><p>'+legend+'</p><p>'+notes[language].format(reference)+'</p>'

def append_report_chapters(output, assessment=None):
    output = Path(output)
    index = output / 'index.html'
    original = index.read_text()
    summary = json.loads((output / 'data' / 'summary.json').read_text())
    date = summary['date'] or 'Unknown date'
    original = original.replace('<title>Turn-Table-Test</title>', f'<title>Turn-Table-Test — {date}</title>')
    original = original.replace('<h1>Turn-Table-Test</h1>', f'<h1>Turn-Table-Test — {date}</h1>')
    body = original.split(f'<h1>Turn-Table-Test — {date}</h1>', 1)[1].split('</body>', 1)[0]
    original = original.replace('REPORT_INTRO_TOKEN', report_intro(summary, 'de'))
    original = original.replace('</body>', conclusion(summary, 'de', assessment)+'</body>')
    chapters = []
    for language, label, tag in [('en', 'English', 'en'), ('zh', '中文（简体）', 'zh-Hans')]:
        translated = translate(body, language).replace('REPORT_INTRO_TOKEN', report_intro(summary, language))
        for svg in sorted((output/'plots').glob('*.svg')):
            if svg.stem.endswith(('_en', '_zh')):
                continue
            destination = svg.with_name(f'{svg.stem}_{language}.svg')
            translated_svg = translate(svg.read_text(), language)
            if not destination.exists() or destination.read_text() != translated_svg:
                destination.write_text(translated_svg, encoding='utf-8')
            translated = translated.replace(f'src="plots/{svg.name}"', f'src="plots/{destination.name}"')
        chapters.append(f'<section lang="{tag}"><h1>{label} — {date}</h1>{translated}{conclusion(summary, language, assessment)}</section>')
    final=original.replace('</body>', ''.join(chapters)+'</body>')
    index.write_text(add_contents(final), encoding='utf-8')

def conclusion(summary, language, assessment=None):
    """Comparison text and table, based on paired stale-correction epochs."""
    texts = {
        'de': ('Ergebnis und Fazit',
               '',
               'Verglichen werden ausschließlich identische UTC-Epochen, an denen alle Outage-Empfänger RTK-fixed sind und alle ein Korrekturdatenalter über 10 s melden. Dies kennzeichnet veraltete Korrekturdaten, nicht extern protokollierte Schaltzeiten. Nicht-fixed-Positionen und Referenzlücken sind ausgeschlossen; das Fazit bewertet daher die Genauigkeit der verbleibenden Fixed-Lösungen, nicht die vollständige Verfügbarkeit während aller Outages.',
               ['Receiver', 'Epochen', 'RMS [cm]', 'Median [cm]', '95%-Quantil [cm]', 'Maximum [cm]']),
        'en': ('Results and conclusion',
               '',
               'The comparison uses only identical UTC epochs where all outage receivers are RTK-fixed and all report a correction age greater than 10 s. This indicates stale corrections, rather than externally logged switching times. Non-fixed positions and reference gaps are excluded; the conclusion therefore assesses the accuracy of the remaining fixed solutions, not overall availability throughout all outages.',
               ['Receiver', 'Epochs', 'RMS [cm]', 'Median [cm]', '95th percentile [cm]', 'Maximum [cm]']),
        'zh': ('结果与结论',
               '',
               '比较仅采用相同 UTC 历元，并要求全部中断接收机均为 RTK 固定解，且均报告超过 10 秒的改正数据龄期。该条件表示改正数据已过时，而非外部日志记录的实际中断切换时刻。非固定解位置及参考数据缺口均被排除，因此本结论评价的是保留的固定解精度，而非整个中断期间的完整可用性。',
               ['接收机', '历元数', '均方根 [cm]', '中位数 [cm]', '第95百分位数 [cm]', '最大值 [cm]']),
    }
    title, result, method, headers = texts[language]
    stats = summary['outage_comparison']['statistics']
    winners=[]
    for metric in ('rms_m', 'median_m', 'p95_m', 'max_m'):
        if not stats:
            winners.append('—')
            continue
        best=min(values[metric] for values in stats.values())
        winners.append(' / '.join(name for name,values in stats.items() if values[metric]==best))
    templates={
        'de': 'Kleinster RMS: {}; kleinster Median: {}; kleinstes 95%-Quantil: {}; kleinster Maximalfehler: {}. Bewertet werden nur die gepaarten Fixed-Lösungen.',
        'en': 'Lowest RMS: {}; lowest median: {}; lowest 95th percentile: {}; lowest maximum error: {}. Only paired fixed solutions are assessed.',
        'zh': '最低均方根：{}；最低中位数：{}；最低第95百分位数：{}；最低最大误差：{}。仅评价配对的固定解。',
    }
    result=html.escape(templates[language].format(*winners))
    table = '<table border="1" cellpadding="6"><tr>'+''.join(f'<th>{h}</th>' for h in headers)+'</tr>'
    for name, values in stats.items():
        cells = [name, str(values['epochs'])]+[f"{100*values[k]:.2f}" for k in ['rms_m','median_m','p95_m','max_m']]
        table += '<tr>'+''.join(f'<td>{v}</td>' for v in cells)+'</tr>'
    return f'<h2>{title}</h2><p>{result}</p><p>{method}</p>{table}</table>'+markdown_html(vertical_markdown(summary, language))+historical_assessment(language, assessment)


def historical_assessment(language, assessment=None):
    """Render the complete language chapter, including references and discussion."""
    if assessment is None:
        return ''
    document=Path(assessment).read_text()
    chapters=re.split(r'^# [^\n]*\n',document,flags=re.MULTILINE)[1:]
    if len(chapters)!=3:
        raise ValueError('Assessment must contain German, English and Chinese top-level chapters')
    return markdown_html(chapters[{'de':0,'en':1,'zh':2}[language]])
