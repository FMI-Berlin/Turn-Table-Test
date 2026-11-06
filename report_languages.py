"""Additional English and Simplified Chinese report chapters and SVG labels."""
from pathlib import Path
import json

# Exact report/axis phrases; numeric data and machine-readable field names stay unchanged.
TRANSLATIONS = {
'en': {
'Mittlere Umdrehungsdauer:':'Mean rotation period:',
'vollständige Umdrehungen, ohne Referenzlücken':'complete revolutions, excluding reference gaps',
'Turn-Table-Test':'Turn-table test',
'Radius:':'Radius:', ' bis ':' to ', 'Datum:':'Date:',
'(aus UM980; gleicher Tag für P23A angenommen).':'(from UM980; the same date is assumed for P23A).',
'Rot: P23A_0; grün: P23A_1; blau: UM980; schwarzes Kreuz: Sollposition.':'Red: P23A_0; green: P23A_1; blue: UM980; black cross: expected position.',
'Nur RTK-fixed-Positionen (GGA-Qualität 4) sind enthalten. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360° als Anzahl der Vollkreise.':'Only RTK-fixed positions (GGA quality 4) are included. The rotation plot shows the angle divided by 360° as the number of revolutions.',
'Der Referenzwinkel wird aus P23A_0 abgeleitet. Dessen tangentialer Fehler ist damit nicht unabhängig messbar; die rote Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken. Keine nachträgliche Zeitverschiebung der Empfänger. Über Referenzlücken ist die Anzahl ganzer Umdrehungen unbekannt; der entfaltete Winkel setzt danach mit dem nächstliegenden Winkel fort (Segmentnummer in referenz_winkel.csv).':'The reference angle is derived from P23A_0. Its tangential error cannot be measured independently; the red trace mainly shows the radial residual. There is no extrapolation or interpolation across large reference gaps and no subsequent receiver time shift. The number of complete turns during reference gaps is unknown; the unwrapped angle resumes at the nearest equivalent angle (segment number in referenz_winkel.csv).',
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
'Mittlere Umdrehungsdauer:':'平均旋转周期：',
'vollständige Umdrehungen, ohne Referenzlücken':'次完整旋转，已排除参考数据缺口',
'Turn-Table-Test':'转台测试', 'Radius:':'半径：', ' bis ':' 至 ', 'Datum:':'日期：',
'(aus UM980; gleicher Tag für P23A angenommen).':'（来自 UM980；假定 P23A 的数据采集于同一天）。',
'Rot: P23A_0; grün: P23A_1; blau: UM980; schwarzes Kreuz: Sollposition.':'红色：P23A_0；绿色：P23A_1；蓝色：UM980；黑色十字：理论位置。',
'Nur RTK-fixed-Positionen (GGA-Qualität 4) sind enthalten. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360° als Anzahl der Vollkreise.':'仅包含 RTK 固定解位置（GGA 质量标识为 4）。旋转图以转角除以 360°，表示旋转圈数。',
'Der Referenzwinkel wird aus P23A_0 abgeleitet. Dessen tangentialer Fehler ist damit nicht unabhängig messbar; die rote Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken. Keine nachträgliche Zeitverschiebung der Empfänger. Über Referenzlücken ist die Anzahl ganzer Umdrehungen unbekannt; der entfaltete Winkel setzt danach mit dem nächstliegenden Winkel fort (Segmentnummer in referenz_winkel.csv).':'参考角由 P23A_0 推导，因此无法独立测量其切向误差；红色轨迹主要表示径向残差。不进行外推，也不跨越较大的参考数据缺口进行插值，不对接收机时间进行事后平移。参考数据缺口期间的完整旋转圈数未知；缺口后展开角采用最接近的等效角继续（分段编号见 referenz_winkel.csv）。',
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

def append_report_chapters(output):
    output = Path(output)
    index = output / 'index.html'
    original = index.read_text()
    summary = json.loads((output / 'auswertung.json').read_text())
    date = summary['date'] or 'Unknown date'
    original = original.replace('<title>Turn-Table-Test</title>', f'<title>Turn-Table-Test — {date}</title>')
    original = original.replace('<h1>Turn-Table-Test</h1>', f'<h1>Turn-Table-Test — {date}</h1>')
    body = original.split(f'<h1>Turn-Table-Test — {date}</h1>', 1)[1].split('</body>', 1)[0]
    original = original.replace('</body>', conclusion(summary, 'de')+'</body>')
    chapters = []
    for language, label, tag in [('en', 'English', 'en'), ('zh', '中文（简体）', 'zh-Hans')]:
        translated = translate(body, language)
        for svg in sorted(output.glob('*.svg')):
            if svg.stem.endswith(('_en', '_zh')):
                continue
            destination = svg.with_name(f'{svg.stem}_{language}.svg')
            destination.write_text(translate(svg.read_text(), language), encoding='utf-8')
            translated = translated.replace(f'src="{svg.name}"', f'src="{destination.name}"')
        chapters.append(f'<section lang="{tag}"><h1>{label} — {date}</h1>{translated}{conclusion(summary, language)}</section>')
    index.write_text(original.replace('</body>', ''.join(chapters)+'</body>'), encoding='utf-8')

def conclusion(summary, language):
    """Comparison text and table, based on paired stale-correction epochs."""
    texts = {
        'de': ('Ergebnis und Fazit',
               'P23A_1 kommt in diesem Test bei den typischen horizontalen Abweichungen besser mit Referenzdaten-Outages zurecht als UM980 (kleinerer RMS, Median und 95%-Quantil). UM980 hat dagegen den kleineren maximalen Einzelfehler. P23A_0 dient mit kontinuierlichen Referenzdaten als Referenz und ist kein Outage-Vergleichskandidat.',
               'Verglichen werden ausschließlich identische UTC-Epochen, an denen beide Empfänger RTK-fixed sind und beide ein Korrekturdatenalter über 10 s melden. Dies kennzeichnet veraltete Korrekturdaten, nicht extern protokollierte Schaltzeiten. Nicht-fixed-Positionen und Referenzlücken sind ausgeschlossen; das Fazit bewertet daher die Genauigkeit der verbleibenden Fixed-Lösungen, nicht die vollständige Verfügbarkeit während aller Outages.',
               ['Receiver', 'Epochen', 'RMS [cm]', 'Median [cm]', '95%-Quantil [cm]', 'Maximum [cm]']),
        'en': ('Results and conclusion',
               'In this test, P23A_1 handles reference-data outages better than UM980 in terms of typical horizontal errors (lower RMS, median and 95th percentile). UM980 has the smaller maximum individual error. P23A_0 has continuous reference data and serves as the reference, rather than as an outage comparison candidate.',
               'The comparison uses only identical UTC epochs where both receivers are RTK-fixed and both report a correction age greater than 10 s. This indicates stale corrections, rather than externally logged switching times. Non-fixed positions and reference gaps are excluded; the conclusion therefore assesses the accuracy of the remaining fixed solutions, not overall availability throughout all outages.',
               ['Receiver', 'Epochs', 'RMS [cm]', 'Median [cm]', '95th percentile [cm]', 'Maximum [cm]']),
        'zh': ('结果与结论',
               '在本次测试中，按典型水平误差衡量，P23A_1 应对参考数据中断的表现优于 UM980（均方根、误差中位数和第 95 百分位数均更小）。但 UM980 的最大单次误差更小。P23A_0 持续接收参考数据，仅作为参考基准，不参与中断性能排名。',
               '比较仅采用相同 UTC 历元，并要求两个接收机均为 RTK 固定解，且均报告超过 10 秒的改正数据龄期。该条件表示改正数据已过时，而非外部日志记录的实际中断切换时刻。非固定解位置及参考数据缺口均被排除，因此本结论评价的是保留的固定解精度，而非整个中断期间的完整可用性。',
               ['接收机', '历元数', '均方根 [cm]', '中位数 [cm]', '第95百分位数 [cm]', '最大值 [cm]']),
    }
    title, result, method, headers = texts[language]
    stats = summary['outage_comparison']['statistics']
    table = '<table border="1" cellpadding="6"><tr>'+''.join(f'<th>{h}</th>' for h in headers)+'</tr>'
    for name, values in stats.items():
        cells = [name, str(values['epochs'])]+[f"{100*values[k]:.2f}" for k in ['rms_m','median_m','p95_m','max_m']]
        table += '<tr>'+''.join(f'<td>{v}</td>' for v in cells)+'</tr>'
    return f'<h2>{title}</h2><p>{result}</p><p>{method}</p>{table}</table>'
