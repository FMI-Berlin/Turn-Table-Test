"""Relative vertical accuracy for receivers sharing one moving antenna."""
import bisect
import csv
import math
import statistics as st


def gga_height(fields):
    """Ellipsoidal height H+N; reject incomplete/non-metric/nonfinite values."""
    try:
        if fields[10] != 'M' or fields[12] != 'M':
            return None
        value = float(fields[9]) + float(fields[11])
        return value if math.isfinite(value) else None
    except (ValueError, IndexError):
        return None


def height_at(reference, t, max_gap):
    times, heights = reference
    j = bisect.bisect_left(times, t)
    if j < len(times) and times[j] == t:
        return heights[j]
    if j == 0 or j == len(times) or times[j] - times[j-1] > max_gap:
        return None
    fraction = (t - times[j-1]) / (times[j] - times[j-1])
    return heights[j-1] + fraction * (heights[j] - heights[j-1])


def vertical_analysis(output, data, residuals, max_gap, svg_plot, age_hrms):
    fixed = [r for r in data[0] if r['q'] == 4 and r['height_m'] is not None]
    reference = ([r['t'] for r in fixed], [r['height_m'] for r in fixed])
    summary = dict(reference_receiver=residuals[0][0], height_definition='GGA altitude + geoid separation (ellipsoidal height)',
                   residual_definition='receiver ellipsoidal height minus time-aligned fixed reference height; no offset removal',
                   reference_self_residual='zero by construction; not an independent accuracy measurement',
                   max_interpolation_gap_s=max_gap, statistics={}, paired_outage_statistics={}, fits={})
    series = []
    for (name, color, horizontal), raw in zip(residuals, data):
        heights = {r['t']: r['height_m'] for r in raw}
        rows = []
        for r in horizontal:
            h = heights[r['utc_seconds']]
            expected = height_at(reference, r['utc_seconds'], max_gap)
            if h is None or expected is None:
                continue
            rows.append(dict(utc_seconds=r['utc_seconds'], seconds_since_start=r['seconds_since_start'],
                             correction_age_s=r['correction_age_s'], ellipsoidal_height_m=h,
                             reference_height_m=expected, error_up_m=h-expected))
        with (output/'data'/f'{name}_vertical.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['utc_seconds','seconds_since_start','correction_age_s',
                                                   'ellipsoidal_height_m','reference_height_m','error_up_m'])
            writer.writeheader(); writer.writerows(rows)
        summary['statistics'][name] = vertical_stats(rows)
        series.append((name, color, rows))
    # Exclude the identically zero reference from plots and fits.
    outages = series[1:]
    by_time = [{r['utc_seconds']: r for r in rows} for _, _, rows in outages]
    common = set.intersection(*(set(rows) for rows in by_time))
    common = sorted(t for t in common if all(rows[t]['correction_age_s'] is not None
                    and math.isfinite(rows[t]['correction_age_s']) and rows[t]['correction_age_s'] > 10
                    for rows in by_time))
    for (name, _, _), rows in zip(outages, by_time):
        summary['paired_outage_statistics'][name] = vertical_stats([rows[t] for t in common])
    plot_dir = output/'plots'
    svg_plot(plot_dir/'vertical_time.svg', [(name, color, [(r['seconds_since_start']/60, r['error_up_m']*1000)
             for r in rows]) for name, color, rows in outages], 'Zeit seit gemeinsamem Beginn [min]',
             'Vertikale Abweichung [mm]', 'Vertikale Abweichung über der Zeit')
    for axis, width in [('dage', 10), ('time', 60)]:
        binned, rms_series, fit_lines, fits = [], [], [], {}
        points_by_receiver = []
        for name, color, rows in outages:
            points = [(r['correction_age_s'] if axis == 'dage' else r['seconds_since_start'], r['error_up_m'])
                      for r in rows]
            points = [(x, y) for x, y in points if x is not None and math.isfinite(x) and x >= 0]
            points_by_receiver.append((name, color, points))
            bins, fit = age_hrms(points, width)
            binned.extend(dict(receiver=name, lower_s=b['age_lower_s'], upper_s=b['age_upper_s'],
                               epochs=b['epochs'], mean_s=b['mean_age_s'], vrms_mm=b['hrms_mm']) for b in bins)
            scale = 60 if axis == 'time' else 1
            rms_series.append((name, color, [(b['mean_age_s']/scale, b['hrms_mm']) for b in bins]))
            if fit:
                fits[name] = fit
                fit_lines.append((f"{name}: {fit['slope_mm_per_s']:+.4f} mm/s", color,
                                  [(x/scale, fit['intercept_mm']+fit['slope_mm_per_s']*x)
                                   for x in [fit['min_age_s'], fit['max_age_s']]]))
        summary['fits'][axis] = dict(bin_width_s=width, method='unweighted OLS of bin VRMS versus mean seconds, free intercept', receivers=fits)
        with (output/'data'/f'vertical_{axis}_vrms.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['receiver','lower_s','upper_s','epochs','mean_s','vrms_mm'])
            writer.writeheader(); writer.writerows(binned)
        xlabel = 'Korrekturdatenalter dAge [s]' if axis == 'dage' else 'Zeit seit gemeinsamem Beginn [min]'
        if axis == 'dage':
            svg_plot(plot_dir/'vertical_dage_scatter.svg', [(name, color, [(x, y*1000) for x, y in points])
                     for name, color, points in points_by_receiver], xlabel, 'Vertikale Abweichung [mm]',
                     'Vertikale Abweichung über dAge: alle RTK-fixed-Einzelwerte')
        svg_plot(plot_dir/f'vertical_{axis}_vrms.svg', rms_series, xlabel, 'Vertikaler RMS VRMS [mm]',
                 'VRMS über dAge: 10-s-Intervalle und linearer Fit' if axis == 'dage'
                 else 'VRMS über Zeit: 60-s-Intervalle und linearer Fit', lines=fit_lines)
    return summary


def vertical_stats(rows):
    errors = [r['error_up_m'] for r in rows]
    absolute = sorted(abs(x) for x in errors)
    if not errors:
        return dict(epochs=0)
    return dict(epochs=len(errors), bias_m=st.mean(errors), vrms_m=math.sqrt(st.mean(x*x for x in errors)),
                std_m=st.pstdev(errors), p95_abs_m=absolute[math.ceil(.95*len(errors))-1], max_abs_m=max(absolute))


def vertical_markdown(summary, language):
    if 'vertical' not in summary:
        return ''
    v = summary['vertical']
    titles = {'de': 'Vertikale Genauigkeit und VRMS', 'en': 'Vertical accuracy and VRMS', 'zh': '垂直精度与 VRMS'}
    notes = {
        'de': 'Ellipsoidische Höhe h = GGA-Höhe + Geoidundulation. Die Empfänger melden unterschiedliche Geoidundulationen; GGA-Höhen allein sind daher nicht vergleichbar. Abweichung = h des Outage-Empfängers minus zeitgleiche RTK-fixed-Referenzhöhe ({ref}), linear interpoliert nur zwischen Fixed-Werten mit maximal {gap:g} s Abstand. Keine Entfernung eines Höhenoffsets. Dies misst relative Höhenübereinstimmung der gemeinsamen Antenne, keine absolute Höhenrichtigkeit; gemeinsame Fehler bleiben unsichtbar. Die Referenz hätte konstruktionsbedingt VRMS = 0 und wird nicht als Genauigkeitsmessung geplottet. Verwendet werden die horizontal zugelassenen Fixed-Epochen mit zusätzlich gültigen Höhen und vertikaler Referenz.',
        'en': 'Ellipsoidal height h = GGA altitude + geoid separation. Receivers report different geoid separations, so GGA altitudes alone are not comparable. Residual = outage receiver h minus simultaneous RTK-fixed reference height ({ref}), linearly interpolated only between fixed heights separated by at most {gap:g} s. No height offset is removed. This measures relative height agreement of the shared antenna, not absolute accuracy; common errors remain invisible. The reference has VRMS = 0 by construction and is excluded from accuracy plots. Samples must pass the horizontal fixed-epoch selection and additionally have valid heights and a vertical reference.',
        'zh': '椭球高 h = GGA 高程 + 大地水准面差距。接收机报告的大地水准面差距不同，因此不能直接比较 GGA 高程。残差为中断接收机 h 减去同时刻 RTK 固定解参考高程（{ref}）；仅在间隔不超过 {gap:g} 秒的固定解之间线性插值。不扣除高程偏差。此结果衡量共用天线的相对高程一致性，并非绝对精度；共同误差不可见。参考接收机自身的 VRMS 按定义为零，不作为精度曲线绘制。采用通过水平固定解筛选且具有有效高程和垂直参考的历元。'}
    methods = {
        'de': 'VRMS = sqrt(Mittelwert(Δh²)), einschließlich Bias; STD wird zusätzlich getrennt ausgewiesen. Einzelwerte werden vor den RMS-/Fitplots gezeigt. VRMS(dAge): 10-s-Intervalle; VRMS(Zeit): 60-s-Intervalle ab gemeinsamem Beginn. Intervalle (untere, obere Grenze], Null im ersten Intervall; Punkte beim mittleren beobachteten x. Ungewichteter linearer Fit mit freiem Achsenabschnitt nur im belegten Bereich, Steigungen in mm/s. Alle gültigen Einzelreceiver-Epochen fließen in die Bins ein. Der Zeitfit beschreibt den Verlauf der gesamten Messung einschließlich wiederholter Outages und ist keine Outage-Driftrate. dAge ist gemeldetes Korrekturdatenalter, keine extern gemessene Outage-Zeit. Die folgende Tabelle verwendet dagegen identische UTC-Epochen aller Outage-Empfänger mit jeweils dAge > 10 s und gültiger Höhe.',
        'en': 'VRMS = sqrt(mean(Δh²)), including bias; STD is reported separately. Raw samples precede RMS/fit plots. VRMS(dAge) uses 10-s bins; VRMS(time) uses 60-s bins since common start. Bins are (lower, upper], with zero in the first bin; points use mean observed x. Fits use unweighted OLS with a free intercept over the observed range only, slopes in mm/s. Bins include all valid individual receiver epochs. The time fit describes the full recording including repeated outages, not an outage drift rate. dAge is reported correction age, not externally measured outage duration. The following table instead uses identical UTC epochs across all outage receivers, each with dAge > 10 s and a valid height.',
        'zh': 'VRMS = sqrt(平均值(Δh²))，包含偏差；另外列出 STD。先显示原始散点，再显示 RMS 和拟合。dAge 使用 10 秒区间，时间使用自共同起点起的 60 秒区间；区间为 (下界,上界]，零计入首区间，点位于观测横坐标均值。采用不加权、截距自由的线性拟合，仅限观测范围，斜率为 mm/s。各接收机的全部有效历元均参与分箱。时间拟合描述包括多次中断的整段测量，并非单次中断漂移率。dAge 是报告的改正龄期，不是外部测得的中断时间。下表则仅采用所有中断接收机相同 UTC、各自 dAge > 10 秒且高程有效的历元。'}
    headers = {'de': 'Receiver | Epochen | Bias [mm] | VRMS [mm] | STD [mm]',
               'en': 'Receiver | Epochs | Bias [mm] | VRMS [mm] | STD [mm]',
               'zh': '接收机 | 历元数 | 偏差 [mm] | VRMS [mm] | STD [mm]'}
    lines = ['## '+titles[language], '', notes[language].format(ref=v['reference_receiver'], gap=v['max_interpolation_gap_s']),
             '', methods[language], '', '| '+headers[language]+' |', '|---|---:|---:|---:|---:|']
    for name, stats in v['paired_outage_statistics'].items():
        if not stats['epochs']:
            lines.append(f'| {name} | 0 | — | — | — |')
            continue
        lines.append('| '+ ' | '.join([name, str(stats['epochs'])]+[f"{stats[k]*1000:.3f}" for k in ('bias_m','vrms_m','std_m')])+' |')
    fit_headers = {'de': 'Receiver | dAge-Fit [mm/s] | Zeit-Fit [mm/s]',
                   'en': 'Receiver | dAge fit [mm/s] | Time fit [mm/s]',
                   'zh': '接收机 | dAge 斜率 [mm/s] | 时间斜率 [mm/s]'}
    lines.extend(['', '| '+fit_headers[language]+' |', '|---|---:|---:|'])
    for name in v['paired_outage_statistics']:
        slopes = [v['fits'][axis]['receivers'].get(name, {}).get('slope_mm_per_s') for axis in ('dage','time')]
        lines.append('| '+' | '.join([name]+[f'{x:+.4f}' if x is not None else '—' for x in slopes])+' |')
    return '\n'.join(lines)+'\n'
