#!/usr/bin/env python3
"""Turn-table-Auswertung, Python >=3.10, ohne externe Abhängigkeiten."""
import argparse
import bisect
import csv
import datetime as dt
import html
import json
import math
from pathlib import Path
import re
import statistics as st

from dataset import DEFAULT_DATASET, ROOT, load_dataset

DAGE_NOTE = ('dAge ist das gemeldete GGA-Korrekturdatenalter [s]. HRMS = sqrt(Mittelwert(Ostfehler² + Nordfehler²)) je 10-s-Intervall (0,10], (10,20], …; dAge=0 zählt zum ersten Intervall. Punkte liegen beim mittleren dAge je Intervall. Die Geraden werden ungewichtet an die Intervall-HRMS-Werte angepasst, mit freiem Achsenabschnitt und nur im belegten Altersbereich; ihre Steigungen stehen in mm/s. Alle verwendbaren RTK-fixed-Epochen mit gültigem dAge sind enthalten, ohne Paarung der Receiver. dAge ist keine extern gemessene Outage-Dauer.')


def parse(path):
    # Auch Dateien mit wörtlichen \\r\\n statt echten Zeilenumbrüchen lesen.
    sentences = re.findall(r'\$[^$\r\n\\]*', path.read_text(errors='replace'))
    rows, dates, bad = [], set(), 0
    day, previous = 0, None
    for sentence in sentences:
        body, sep, checksum = sentence[1:].partition('*')
        if sep:
            check = 0
            for char in body:
                check ^= ord(char)
            if checksum[:2].upper() != f'{check:02X}':
                bad += 1
                continue
        f = body.split(',')
        if f[0].endswith('RMC') and len(f) > 9 and f[9]:
            dates.add(dt.datetime.strptime(f[9], '%d%m%y').date().isoformat())
        if not f[0].endswith('GGA') or len(f) < 15 or not f[1]:
            continue
        try:
            utc = float(f[1][:2])*3600 + float(f[1][2:4])*60 + float(f[1][4:])
            if previous is not None and utc < previous - 43200:
                day += 86400
            previous = utc
            quality = int(f[6])
            if quality == 0 or not f[2] or not f[4]:
                continue
            def deg(value, sign):
                v = float(value)
                return (int(v/100) + (v % 100)/60) * (-1 if sign in ('S','W') else 1)
            rows.append(dict(t=utc+day, lat=deg(f[2],f[3]), lon=deg(f[4],f[5]),
                             q=quality, age=float(f[13]) if f[13] else None))
        except (ValueError, IndexError):
            bad += 1
    # Ein Positionswert je UTC-Epoche; keine Verschiebung anhand von Positionen.
    unique = {r['t']: r for r in rows}
    return sorted(unique.values(), key=lambda r:r['t']), sorted(dates), bad, len(rows)-len(unique)

def solve(a, b):
    m = [list(row)+[v] for row,v in zip(a,b)]
    for i in range(3):
        pivot = max(range(i,3), key=lambda j:abs(m[j][i]))
        m[i],m[pivot] = m[pivot],m[i]
        if abs(m[i][i]) < 1e-15:
            raise ValueError('Kreisfit singulär: Winkelabdeckung prüfen.')
        scale = m[i][i]
        m[i] = [v/scale for v in m[i]]
        for j in range(3):
            if j != i:
                scale = m[j][i]
                m[j] = [x-scale*y for x,y in zip(m[j],m[i])]
    return [row[3] for row in m]

def fit_circle(points):
    # Algebraischer Startwert; anschließend robuster geometrischer Huber-Fit.
    a = [[0.]*3 for _ in range(3)]; b = [0.]*3
    for x,y in points:
        v = [2*x,2*y,1]; z=x*x+y*y
        for i in range(3):
            b[i] += v[i]*z
            for j in range(3): a[i][j] += v[i]*v[j]
    cx,cy,c = solve(a,b); radius=math.sqrt(c+cx*cx+cy*cy)
    for _ in range(40):
        residual = [math.hypot(x-cx,y-cy)-radius for x,y in points]
        median=st.median(residual)
        scale=max(1e-5,1.4826*st.median(abs(v-median) for v in residual))
        a = [[0.]*3 for _ in range(3)]; b=[0.]*3
        for (x,y),error in zip(points,residual):
            d=math.hypot(x-cx,y-cy)
            if d < 1e-12: continue
            v=[(cx-x)/d,(cy-y)/d,-1.]
            w=min(1.,1.5*scale/max(abs(error),1e-15))
            for i in range(3):
                b[i] -= w*v[i]*error
                for j in range(3): a[i][j] += w*v[i]*v[j]
        step=solve(a,b); cx+=step[0]; cy+=step[1]; radius+=step[2]
        if max(map(abs,step)) < 1e-10: break
    return cx,cy,radius,scale

def rotation_periods(times, angles, segments):
    """Full-turn first-passage times; never span reference segment boundaries."""
    periods = []
    for segment in sorted(set(segments)):
        points = [(t, a) for t, a, seg in zip(times, angles, segments) if seg == segment]
        if len(points) < 2:
            continue
        direction = 1 if points[-1][1] >= points[0][1] else -1
        target = points[0][1] + direction*2*math.pi
        last_crossing = points[0][0]
        for (t0, a0), (t1, a1) in zip(points, points[1:]):
            while direction*(a0-target) < 0 <= direction*(a1-target):
                crossing = t0 + (target-a0)/(a1-a0)*(t1-t0)
                periods.append(dict(segment=segment, start_utc_seconds=last_crossing,
                                    end_utc_seconds=crossing, duration_s=crossing-last_crossing))
                last_crossing = crossing
                target += direction*2*math.pi
    return periods


def nice_step(span, intervals=6):
    raw = max(span, 1e-9) / intervals
    magnitude = 10 ** math.floor(math.log10(raw))
    return next(v * magnitude for v in (1, 2, 2.5, 5, 10) if v * magnitude >= raw)


def axis_range(low, high, step=None):
    low, high = min(low, 0), max(high, 0)
    step = step or nice_step(high - low)
    first = math.floor(low / step + 1e-10)
    last = math.ceil(high / step - 1e-10)
    if first == last:
        last += 1
    return first * step, last * step, [i * step for i in range(first, last + 1)]


def age_hrms(points, bin_width=10):
    """HRMS per age bin; unweighted OLS across bins, with a free intercept.

    Bins are (0, 10], (10, 20], ...; age zero is included in the first bin.
    Each bin's x coordinate is its mean observed age.
    """
    groups = {}
    for age, error in points:
        k = max(0, math.ceil(age / bin_width) - 1)
        groups.setdefault(k, []).append((age, error))
    bins = [dict(age_lower_s=k * bin_width, age_upper_s=(k + 1) * bin_width,
                 epochs=len(values), mean_age_s=st.mean(x for x, _ in values),
                 hrms_mm=1000 * math.sqrt(st.mean(y*y for _, y in values)))
            for k, values in sorted(groups.items())]
    if len(bins) < 2:
        return bins, None
    mx = st.mean(b['mean_age_s'] for b in bins)
    my = st.mean(b['hrms_mm'] for b in bins)
    slope = sum((b['mean_age_s']-mx)*(b['hrms_mm']-my) for b in bins) / sum(
        (b['mean_age_s']-mx)**2 for b in bins)
    intercept = my - slope*mx
    fit = dict(slope_mm_per_s=slope, intercept_mm=intercept, bins=len(bins),
               min_age_s=min(b['mean_age_s'] for b in bins),
               max_age_s=max(b['mean_age_s'] for b in bins))
    return bins, fit


def svg_plot(path, series, xlabel, ylabel, title, equal=False, zero=False, extent_m=None,
             lines=(), legend_columns=None, bounds=None):
    if legend_columns is None and len(series)>3:
        legend_columns=2
    allpoints=[p for _,_,pts in list(series)+list(lines) for p in pts if p is not None]
    allpoints.append((0,0))
    xmin,xmax=min(p[0] for p in allpoints),max(p[0] for p in allpoints)
    ymin,ymax=min(p[1] for p in allpoints),max(p[1] for p in allpoints)
    if equal:
        extent=extent_m or max(abs(xmin),abs(xmax),abs(ymin),abs(ymax),.001)
        step=nice_step(2*extent)
        extent=math.ceil(extent/step-1e-10)*step
        xmin,xmax,xticks=axis_range(-extent,extent,step)
        ymin,ymax,yticks=axis_range(-extent,extent,step)
        w,h=680,680
    else:
        xmin,xmax,xticks=axis_range(xmin,xmax)
        ymin,ymax,yticks=axis_range(ymin,ymax)
        w,h=1000,430
    if bounds is not None:
        xmin,xmax,ymin,ymax=bounds
        _,_,xticks=axis_range(xmin,xmax,nice_step(xmax-xmin,7))
        _,_,yticks=axis_range(ymin,ymax,nice_step(ymax-ymin,7))
        xticks=[x for x in xticks if xmin<=x<=xmax]
        yticks=[y for y in yticks if ymin<=y<=ymax]
    left,top,pw,ph=95,90 if lines else 65,w-130,h-(160 if lines else 135)
    if legend_columns:
        series_rows=math.ceil(len(series)/legend_columns)
        line_rows=math.ceil(len(lines)/legend_columns)
        top=45+(series_rows+line_rows)*22+6
        ph=pw if equal else 270; h=top+ph+70
    def xy(x,y): return left+(x-xmin)/(xmax-xmin)*pw,top+ph-(y-ymin)/(ymax-ymin)*ph
    def tick_label(value): return '0' if abs(value)<1e-12 else f'{value:.8g}'
    elements=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>',
              '<g font-family="sans-serif" font-size="12">',f'<text x="{left}" y="23" font-size="16">{html.escape(title)}</text>']
    for x in xticks:
        px,_=xy(x,0)
        elements += [f'<path d="M{px},{top}v{ph}" stroke="#ddd" fill="none"/>',f'<text x="{px}" y="{top+ph+20}" text-anchor="middle">{tick_label(x)}</text>']
    for y in yticks:
        _,py=xy(0,y)
        elements += [f'<path d="M{left},{py}h{pw}" stroke="#ddd" fill="none"/>',f'<text x="{left-8}" y="{py+4}" text-anchor="end">{tick_label(y)}</text>']
    zx,zy=xy(0,0)
    elements.append(f'<path d="M{zx},{top}v{ph} M{left},{zy}h{pw}" stroke="black" stroke-width="1.2" fill="none"/>')
    for k,(label,color,points) in enumerate(series):
        lx=left+(k%legend_columns)*pw/legend_columns if legend_columns else left+k*pw/max(len(series),1)
        ly=45+(k//legend_columns)*22 if legend_columns else 45
        elements.append(f'<text x="{lx}" y="{ly}" fill="{color}">{html.escape(label)}</text>')
        d=' '.join(f'M{px:.2f},{py:.2f}h0.1' for x,y in points if xmin<=x<=xmax and ymin<=y<=ymax if (px_py:=xy(x,y)) for px,py in [px_py])
        elements.append(f'<path d="{d}" stroke="{color}" stroke-width="{4 if lines else 2}" stroke-linecap="round" opacity="0.55"/>')
    for k,(label,color,points) in enumerate(lines):
        lx=left+(k%legend_columns)*pw/legend_columns if legend_columns else left+k*pw/max(len(lines),1)
        ly=45+(series_rows+k//legend_columns)*22 if legend_columns else 67
        elements.append(f'<text x="{lx}" y="{ly}" fill="{color}">{html.escape(label)}</text>')
        d=' '.join(f'{"M" if i==0 else "L"}{xy(x,y)[0]:.2f},{xy(x,y)[1]:.2f}' for i,(x,y) in enumerate(points))
        elements.append(f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none"/>')
    origin_label='Soll (0,0)' if zero else '(0,0)'
    elements.append(f'<path d="M{zx-5},{zy}h10 M{zx},{zy-5}v10" stroke="black" stroke-width="2"/><text x="{zx+8}" y="{zy-8}">{origin_label}</text>')
    elements += [f'<text x="{left+pw/2}" y="{h-12}" text-anchor="middle">{html.escape(xlabel)}</text>',f'<text transform="translate(19,{top+ph/2}) rotate(-90)" text-anchor="middle">{html.escape(ylabel)}</text>','</g></svg>']
    path.write_text('\n'.join(elements))


COMPARISON_NOTE = ('Vergleich mit Abbildung 1, Seite 2 von „Frühere Outage Results.pdf“: Alte Kurven sind aus PDF-Vektorlinien rekonstruierte Näherungen, keine Rohmesswerte. Der einzelne Punkt bei 300 s und etwa 20 mm verwendet finale präzise Uhren und Bahnen. Neu: HRMS je 10-s-Intervall und lineare Fits nur im gemessenen Altersbereich. Unterschiedliche Versuchsbedingungen und Referenzen begrenzen die Vergleichbarkeit. Die Detailansicht zeigt die zwei niedrigeren alten Kurven und den präzisen Uhrenpunkt; alle alten Kurven stehen in der Gesamtansicht.')


def historical_comparison(output, rms_series, fit_lines):
    source=ROOT/'references'/'historical-outage-results'/'hrms.csv'
    groups={}
    with source.open() as stream:
        for row in csv.DictReader(stream):
            groups.setdefault(row['variant'], []).append((float(row['dage_s']),float(row['hrms_mm'])))
    labels=[('no_sv_clock','Alt: ohne SV-Uhr','#666666'),
            ('sv_clock','Alt: SV-Uhr','#a65e00'),
            ('sv_clock_rel','Alt: SV-Uhr + Relativität','#800080'),
            ('sv_clock_rel_ultra','Alt: + Ultra-Rapid','#c000c0'),
            ('sv_clock_rel_precise','Alt: + präzise Bahnen','#000080')]
    old_lines=[(label,color,groups[key]) for key,label,color in labels]
    precise=('Alt: präzise Uhren (ein Punkt)','#800000',groups['precise_clocks_300s'])
    # Match the source chart's endpoint despite subpixel vector rounding.
    old_lines=[(label,color,[(min(500,x),y) for x,y in pts]) for label,color,pts in old_lines]
    def through_age(points, limit):
        result=[(x,y) for x,y in points if x<=limit]
        for (x0,y0),(x1,y1) in zip(points,points[1:]):
            if x0<limit<x1:
                result.append((limit,y0+(y1-y0)*(limit-x0)/(x1-x0)))
                break
        return result
    svg_plot(output/'historical_comparison.svg',rms_series+[precise],
             'Korrekturdatenalter dAge [s]','Horizontaler RMS-Fehler HRMS [mm]',
             'HRMS(dAge): frühere Untersuchung und neue Ergebnisse',
             lines=old_lines+fit_lines,legend_columns=2,bounds=(0,500,0,1400))
    detail=[(label,color,through_age(pts,300)) for label,color,pts in old_lines[-2:]]
    svg_plot(output/'historical_comparison_detail.svg',rms_series+[precise],
             'Korrekturdatenalter dAge [s]','Horizontaler RMS-Fehler HRMS [mm]',
             'HRMS(dAge): Vergleich im Detail (0–300 s, 0–150 mm)',
             lines=detail+fit_lines,legend_columns=2,bounds=(0,300,0,150))


def common_outage_epochs(receivers, threshold=10):
    """Identical fixed epochs with stale corrections at every outage receiver."""
    paired=[{r['utc_seconds']:r for r in rows} for _,_,rows in receivers]
    if not paired:
        return paired, []
    common=set.intersection(*(set(points) for points in paired))
    times=sorted(t for t in common if all(
        p[t]['correction_age_s'] is not None and math.isfinite(p[t]['correction_age_s'])
        and p[t]['correction_age_s']>threshold for p in paired))
    return paired, times


def write_html_report(output, summary, assessment=None, has_age=True):
    age_plot = ('<div><img src="plots/horizontal_dage_scatter.svg" style="max-width:100%"></div><p>'+DAGE_NOTE+'</p><div><img src="plots/horizontal_dage.svg" style="max-width:100%"></div><p>'+COMPARISON_NOTE+'</p><div><img src="plots/historical_comparison.svg" style="max-width:100%"></div><div><img src="plots/historical_comparison_detail.svg" style="max-width:100%"></div>') if has_age else ''
    (output/'index.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>Turn-Table-Test</title><body style="font-family:sans-serif"><h1>Turn-Table-Test</h1>REPORT_INTRO_TOKEN<h2>Diagramme</h2>'+''.join(f'<div><img src="plots/{file}" style="max-width:100%"></div>' for file in ['horizontal.svg','horizontal_detail.svg','rotation.svg','east_time.svg','north_time.svg','horizontal_time.svg'])+age_plot+'</body></html>')
    from report_languages import append_report_chapters
    append_report_chapters(output, assessment)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET, help='Dataset directory or dataset.json')
    parser.add_argument('--input-dir',type=Path,help='Optional raw-input directory override')
    parser.add_argument('--output-dir',type=Path,help='Override results/<dataset-id>')
    parser.add_argument('--max-gap',type=float,help='Override maximum reference interpolation gap [s]')
    args=parser.parse_args()
    dataset=load_dataset(args.dataset)
    files=dataset.receivers
    args.max_gap=dataset.max_gap_s if args.max_gap is None else args.max_gap
    if not math.isfinite(args.max_gap) or args.max_gap <= 0:
        parser.error('--max-gap must be finite and positive')
    output=(args.output_dir or dataset.results).resolve()
    plots=output/'plots'; data_dir=output/'data'
    plots.mkdir(parents=True,exist_ok=True); data_dir.mkdir(parents=True,exist_ok=True)
    data=[]; info={}; dates=set()
    for name,file,_ in files:
        rows,ds,bad,duplicates=parse(args.input_dir/file.name if args.input_dir else file)
        if not rows: raise ValueError(f'Keine gültigen Positionen: {file}')
        data.append(rows); dates.update(ds)
        info[name]=dict(positions=len(rows),invalid_checksums_or_fields=bad,duplicate_epochs=duplicates,dates=ds,
                        quality_counts={str(q):sum(r['q']==q for r in rows) for q in sorted({r['q'] for r in rows})})
    if dates and dates != {dataset.date}:
        raise ValueError('RMC date does not match dataset.json; check day assignment')
    if len(dates)>1: raise ValueError('Mehrere RMC-Daten: Tageszuordnung vor Auswertung prüfen.')
    ref=[r for r in data[0] if r['q']==4]
    if len(ref)<10: raise ValueError('Zu wenige RTK-fixed-Referenzpositionen.')
    lat0=st.median(r['lat'] for r in ref); lon0=st.median(r['lon'] for r in ref)
    # Lokale WGS84-Tangentialkoordinaten mit Krümmungsradien (Meter).
    phi=math.radians(lat0); a=6378137.; e2=6.6943799901413165e-3
    n=a/math.sqrt(1-e2*math.sin(phi)**2); m=a*(1-e2)/(1-e2*math.sin(phi)**2)**1.5
    for rows in data:
        for r in rows:
            r['e']=math.radians(r['lon']-lon0)*n*math.cos(phi)
            r['n']=math.radians(r['lat']-lat0)*m
    cx,cy,radius,scale=fit_circle([(r['e'],r['n']) for r in ref])
    limit=max(.02,6*scale)
    good=[r for r in ref if abs(math.hypot(r['e']-cx,r['n']-cy)-radius)<=limit]
    # Winkel nur innerhalb zusammenhängender, zuverlässiger Referenzsegmente entfalten.
    times=[]; angles=[]; segments=[]; last=None; segment=0
    for r in good:
        angle=math.atan2(r['n']-cy,r['e']-cx)
        if last is not None:
            if r['t']-last > args.max_gap: segment+=1
            angle=angles[-1]+math.atan2(math.sin(angle-angles[-1]),math.cos(angle-angles[-1]))
        times.append(r['t']); angles.append(angle); segments.append(segment); last=r['t']
    start=max(rows[0]['t'] for rows in data); start=max(start,times[0])
    end=min(rows[-1]['t'] for rows in data); end=min(end,times[-1])
    if start>=end: raise ValueError('Kein gemeinsamer Zeitraum.')
    selected = [(t, a, seg) for t, a, seg in zip(times, angles, segments) if start <= t <= end]
    periods = rotation_periods(*zip(*selected))
    if not periods:
        raise ValueError('Keine vollständige Umdrehung innerhalb eines Referenzsegments.')
    durations = [p['duration_s'] for p in periods]
    mean_period = st.mean(durations)
    with (data_dir/'rotation_periods.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(periods[0]))
        writer.writeheader(); writer.writerows(periods)
    def angle_at(t):
        j=bisect.bisect_left(times,t)
        if j<len(times) and times[j]==t: return angles[j]
        if j==0 or j==len(times) or segments[j]!=segments[j-1]: return None
        f=(t-times[j-1])/(times[j]-times[j-1])
        return angles[j-1]+f*(angles[j]-angles[j-1])
    residuals=[]; stats={}
    for (name,_,color),rows in zip(files,data):
        result=[]
        for r in rows:
            if r['q'] != 4 or not start<=r['t']<=end: continue
            angle=angle_at(r['t'])
            if angle is None: continue
            se=cx+radius*math.cos(angle); sn=cy+radius*math.sin(angle)
            result.append(dict(utc_seconds=r['t'],seconds_since_start=r['t']-start,quality=r['q'],correction_age_s=r['age'],angle_deg=math.degrees(angle),revolutions=(angle-angles[0])/(2*math.pi),east_m=r['e'],north_m=r['n'],expected_east_m=se,expected_north_m=sn,error_east_m=r['e']-se,error_north_m=r['n']-sn,horizontal_error_m=math.hypot(r['e']-se,r['n']-sn)))
        if not result: raise ValueError(f'Keine zeitlich zuordenbaren Positionen: {name}')
        with (data_dir/f'{name}.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(result[0])); writer.writeheader(); writer.writerows(result)
        errors=sorted(r['horizontal_error_m'] for r in result)
        stats[name]=dict(epochs=len(result),excluded_epochs=len(rows)-len(result),rms_m=math.sqrt(st.mean(x*x for x in errors)),median_m=st.median(errors),p95_m=errors[math.ceil(.95*len(errors))-1],max_m=max(errors))
        residuals.append((name,color,result))
    svg_plot(plots/'horizontal.svg',[(name,color,[(r['error_east_m'],r['error_north_m']) for r in rows]) for name,color,rows in residuals],'Ost-Abweichung [m]','Nord-Abweichung [m]','Horizontale Abweichungen vom zeitgleichen Sollkreis',equal=True,zero=True)
    svg_plot(plots/'horizontal_detail.svg',[(name,color,[(r['error_east_m'],r['error_north_m']) for r in rows]) for name,color,rows in residuals],'Ost-Abweichung [m]','Nord-Abweichung [m]','Detail ±0,10 m (größere Abweichungen ausgeblendet)',equal=True,zero=True,extent_m=.10)
    for coord,label in [('east','Ost'),('north','Nord'),('horizontal','Horizontal')]:
        field='horizontal_error_m' if coord=='horizontal' else f'error_{coord}_m'
        svg_plot(plots/f'{coord}_time.svg',[(name,color,[(r['seconds_since_start']/60,r[field]) for r in rows]) for name,color,rows in residuals],'Zeit seit gemeinsamem Beginn [min]',f'{label}-Abweichung [m]',f'{label}-Abweichung über der Zeit')
    # dAge is the reported GGA correction age, not a reconstructed switch time.
    age_series = [(name, color, [(r['correction_age_s'], r['horizontal_error_m'])
                   for r in rows if r['correction_age_s'] is not None
                   and math.isfinite(r['correction_age_s']) and r['correction_age_s'] >= 0])
                  for name, color, rows in residuals]
    age_bins, age_fits, rms_series, fit_lines = [], {}, [], []
    for name, color, points in age_series:
        bins, fit = age_hrms(points)
        age_bins.extend(dict(receiver=name, **b) for b in bins)
        rms_series.append((name, color, [(b['mean_age_s'], b['hrms_mm']) for b in bins]))
        if fit is not None:
            age_fits[name] = fit
            ends = [fit['min_age_s'], fit['max_age_s']]
            fit_lines.append((f"{name}: {fit['slope_mm_per_s']:+.4f} mm/s", color,
                              [(x, fit['intercept_mm']+fit['slope_mm_per_s']*x) for x in ends]))
    with (data_dir/'horizontal_dage_hrms.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['receiver', 'age_lower_s', 'age_upper_s',
                                              'epochs', 'mean_age_s', 'hrms_mm'])
        writer.writeheader(); writer.writerows(age_bins)
    if any(points for _, _, points in age_series):
        svg_plot(plots/'horizontal_dage_scatter.svg',
                 [(name, color, [(age, error*1000) for age, error in points])
                  for name, color, points in age_series],
                 'Korrekturdatenalter dAge [s]', 'Horizontaler Fehler [mm]',
                 'Horizontaler Fehler über dAge: alle RTK-fixed-Einzelwerte')
        svg_plot(plots/'horizontal_dage.svg', rms_series,
                 'Korrekturdatenalter dAge [s]', 'Horizontaler RMS-Fehler HRMS [mm]',
                 'HRMS über dAge: 10-s-Intervalle und linearer Fit', lines=fit_lines)
        historical_comparison(plots, rms_series, fit_lines)
    svg_plot(plots/'rotation.svg',[(files[0][0],files[0][2],[((t-start)/60,(ang-angles[0])/(2*math.pi)) for t,ang in zip(times,angles) if start<=t<=end])],'Zeit seit gemeinsamem Beginn [min]','Anzahl der Vollkreise seit erstem Referenzpunkt','Umdrehungen: positiv von Ost nach Nord')
    with (data_dir/'reference_angle.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['utc_seconds','angle_deg_from_east_unwrapped','revolutions_since_first_reference','segment'])
        writer.writerows(zip(times,map(math.degrees,angles),((a-angles[0])/(2*math.pi) for a in angles),segments))
    # Fair comparison on common epochs across every outage receiver.
    paired, paired_times = common_outage_epochs(residuals[1:])
    outage_stats = {}
    for name, points in zip([name for name, _, _ in files[1:]], paired):
        errors = sorted(points[t]['horizontal_error_m'] for t in paired_times)
        if errors:
            outage_stats[name] = dict(epochs=len(errors),
                rms_m=math.sqrt(st.mean(x*x for x in errors)), median_m=st.median(errors),
                p95_m=errors[math.ceil(.95*len(errors))-1], max_m=max(errors))
    with (data_dir/'outage_comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['utc_seconds']+[f'{name}_horizontal_error_m' for name, _, _ in files[1:]])
        writer.writerows([t]+[points[t]['horizontal_error_m'] for points in paired] for t in paired_times)
    summary=dict(dataset_id=dataset.identifier, reference_receiver=files[0][0], receiver_colors={name:color for name,_,color in files}, outage_receivers=[name for name,_,_ in files[1:]], dage_hrms=dict(bin_width_s=10, bin_convention='(lower, upper]; age zero included in first bin', fit_method='unweighted OLS of bin HRMS versus mean age, free intercept', fits=age_fits),outage_comparison=dict(correction_age_threshold_s=10,criterion="all outage receivers RTK-fixed, all correction ages > threshold, identical UTC epochs",statistics=outage_stats),mean_rotation_period_s=mean_period,rotation_period_count=len(periods),rotation_period_std_s=st.pstdev(durations),rotation_period_min_s=min(durations),rotation_period_max_s=max(durations),displayed_quality=4,radius_m=radius,center_lat_deg=lat0+math.degrees(cy/m),center_lon_deg=lon0+math.degrees(cx/(n*math.cos(phi))),origin_lat_deg=lat0,origin_lon_deg=lon0,center_east_m=cx,center_north_m=cy,robust_radial_sigma_m=scale,reference_fixed_epochs=len(ref),reference_angle_epochs=len(good),reference_segments=segment+1,unknown_full_turns_across_reference_gaps=segment>0,max_interpolation_gap_s=args.max_gap,common_start_utc_seconds=start,common_end_utc_seconds=end,date=dataset.date,files=info,statistics=stats)
    (data_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    write_html_report(output, summary, dataset.assessment, any(points for _, _, points in age_series))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
