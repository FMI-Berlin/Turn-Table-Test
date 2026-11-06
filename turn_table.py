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

FILES = [('P23A_0', 'p23a_continious.nmea', 'red'),
         ('P23A_1', 'p23a_outages.nmea', 'green'),
         ('UM980', 'um980_outages.nmea', 'blue')]

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


def svg_plot(path, series, xlabel, ylabel, title, equal=False, zero=False, extent_m=None):
    allpoints=[p for _,_,pts in series for p in pts if p is not None]
    if zero: allpoints.append((0,0))
    xmin,xmax=min(p[0] for p in allpoints),max(p[0] for p in allpoints)
    ymin,ymax=min(p[1] for p in allpoints),max(p[1] for p in allpoints)
    if equal:
        extent=extent_m or max(abs(xmin),abs(xmax),abs(ymin),abs(ymax),.001)*1.08
        xmin,ymin,xmax,ymax=-extent,-extent,extent,extent
        w,h=680,680
    else:
        w,h=1000,430
        dx=max(xmax-xmin,.001)*.04; dy=max(ymax-ymin,.001)*.08
        xmin-=dx; xmax+=dx; ymin-=dy; ymax+=dy
    left,top,pw,ph=95,65,w-130,h-135
    def xy(x,y): return left+(x-xmin)/(xmax-xmin)*pw,top+ph-(y-ymin)/(ymax-ymin)*ph
    elements=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>',
              '<g font-family="sans-serif" font-size="12">',f'<text x="{left}" y="23" font-size="16">{html.escape(title)}</text>']
    for i in range(6):
        x=xmin+(xmax-xmin)*i/5; y=ymin+(ymax-ymin)*i/5
        px,_=xy(x,0); _,py=xy(0,y)
        elements += [f'<path d="M{px},{top}v{ph} M{left},{py}h{pw}" stroke="#ddd" fill="none"/>',f'<text x="{px}" y="{top+ph+20}" text-anchor="middle">{x:.4g}</text>',f'<text x="{left-8}" y="{py+4}" text-anchor="end">{y:.4g}</text>']
    for k,(label,color,points) in enumerate(series):
        elements.append(f'<text x="{left+k*170}" y="45" fill="{color}">{html.escape(label)}</text>')
        # Punkte statt Verbindung über Messlücken oder große Ausreißer.
        d=' '.join(f'M{px:.2f},{py:.2f}h0.1' for x,y in points if xmin<=x<=xmax and ymin<=y<=ymax if (px_py:=xy(x,y)) for px,py in [px_py])
        elements.append(f'<path d="{d}" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity="0.55"/>')
    if zero:
        x,y=xy(0,0)
        elements.append(f'<path d="M{x-7},{y}h14 M{x},{y-7}v14" stroke="black" stroke-width="2"/><text x="{x+9}" y="{y-9}">Soll (0,0)</text>')
    elements += [f'<text x="{left+pw/2}" y="{h-12}" text-anchor="middle">{html.escape(xlabel)}</text>',f'<text transform="translate(19,{top+ph/2}) rotate(-90)" text-anchor="middle">{html.escape(ylabel)}</text>','</g></svg>']
    path.write_text('\n'.join(elements))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output-dir',type=Path,default=Path('ergebnisse'))
    parser.add_argument('--max-gap',type=float,default=3.,help='Maximale Lücke zwischen Referenzpunkten [s]')
    args=parser.parse_args()
    if args.max_gap <= 0: parser.error('--max-gap muss positiv sein')
    output=args.output_dir; output.mkdir(parents=True,exist_ok=True)
    data=[]; info={}; dates=set()
    for name,file,_ in FILES:
        rows,ds,bad,duplicates=parse(args.input_dir/file)
        if not rows: raise ValueError(f'Keine gültigen Positionen: {file}')
        data.append(rows); dates.update(ds)
        info[name]=dict(positions=len(rows),invalid_checksums_or_fields=bad,duplicate_epochs=duplicates,dates=ds,
                        quality_counts={str(q):sum(r['q']==q for r in rows) for q in sorted({r['q'] for r in rows})})
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
    with (output/'umdrehungsdauer.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(periods[0]))
        writer.writeheader(); writer.writerows(periods)
    def angle_at(t):
        j=bisect.bisect_left(times,t)
        if j<len(times) and times[j]==t: return angles[j]
        if j==0 or j==len(times) or segments[j]!=segments[j-1]: return None
        f=(t-times[j-1])/(times[j]-times[j-1])
        return angles[j-1]+f*(angles[j]-angles[j-1])
    residuals=[]; stats={}
    for (name,_,color),rows in zip(FILES,data):
        result=[]
        for r in rows:
            if r['q'] != 4 or not start<=r['t']<=end: continue
            angle=angle_at(r['t'])
            if angle is None: continue
            se=cx+radius*math.cos(angle); sn=cy+radius*math.sin(angle)
            result.append(dict(utc_seconds=r['t'],seconds_since_start=r['t']-start,quality=r['q'],correction_age_s=r['age'],angle_deg=math.degrees(angle),revolutions=(angle-angles[0])/(2*math.pi),east_m=r['e'],north_m=r['n'],expected_east_m=se,expected_north_m=sn,error_east_m=r['e']-se,error_north_m=r['n']-sn,horizontal_error_m=math.hypot(r['e']-se,r['n']-sn)))
        if not result: raise ValueError(f'Keine zeitlich zuordenbaren Positionen: {name}')
        with (output/f'{name}.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(result[0])); writer.writeheader(); writer.writerows(result)
        errors=sorted(r['horizontal_error_m'] for r in result)
        stats[name]=dict(epochs=len(result),excluded_epochs=len(rows)-len(result),rms_m=math.sqrt(st.mean(x*x for x in errors)),median_m=st.median(errors),p95_m=errors[math.ceil(.95*len(errors))-1],max_m=max(errors))
        residuals.append((name,color,result))
    svg_plot(output/'horizontal.svg',[(name,color,[(r['error_east_m'],r['error_north_m']) for r in rows]) for name,color,rows in residuals],'Ost-Abweichung [m]','Nord-Abweichung [m]','Horizontale Abweichungen vom zeitgleichen Sollkreis',equal=True,zero=True)
    svg_plot(output/'horizontal_detail.svg',[(name,color,[(r['error_east_m'],r['error_north_m']) for r in rows]) for name,color,rows in residuals],'Ost-Abweichung [m]','Nord-Abweichung [m]','Detail ±0,10 m (größere Abweichungen ausgeblendet)',equal=True,zero=True,extent_m=.10)
    for coord,label in [('east','Ost'),('north','Nord'),('horizontal','Horizontal')]:
        field='horizontal_error_m' if coord=='horizontal' else f'error_{coord}_m'
        svg_plot(output/f'{coord}_zeit.svg',[(name,color,[(r['seconds_since_start']/60,r[field]) for r in rows]) for name,color,rows in residuals],'Zeit seit gemeinsamem Beginn [min]',f'{label}-Abweichung [m]',f'{label}-Abweichung über der Zeit')
    svg_plot(output/'winkel.svg',[('P23A_0','red',[((t-start)/60,(ang-angles[0])/(2*math.pi)) for t,ang in zip(times,angles) if start<=t<=end])],'Zeit seit gemeinsamem Beginn [min]','Anzahl der Vollkreise seit erstem Referenzpunkt','Umdrehungen: positiv von Ost nach Nord')
    with (output/'referenz_winkel.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['utc_seconds','angle_deg_from_east_unwrapped','revolutions_since_first_reference','segment'])
        writer.writerows(zip(times,map(math.degrees,angles),((a-angles[0])/(2*math.pi) for a in angles),segments))
    # Paired comparison: both receivers fixed and both correction ages >10 s.
    paired = [{r['utc_seconds']: r for r in rows} for _, _, rows in residuals[1:]]
    paired_times = sorted(t for t in paired[0].keys() & paired[1].keys()
                          if all(p[t]['correction_age_s'] is not None and
                                 p[t]['correction_age_s'] > 10 for p in paired))
    outage_stats = {}
    for name, points in zip(['P23A_1', 'UM980'], paired):
        errors = sorted(points[t]['horizontal_error_m'] for t in paired_times)
        if errors:
            outage_stats[name] = dict(epochs=len(errors),
                rms_m=math.sqrt(st.mean(x*x for x in errors)), median_m=st.median(errors),
                p95_m=errors[math.ceil(.95*len(errors))-1], max_m=max(errors))
    with (output/'outage_vergleich.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['utc_seconds','P23A_1_horizontal_error_m','UM980_horizontal_error_m'])
        writer.writerows((t,paired[0][t]['horizontal_error_m'],paired[1][t]['horizontal_error_m']) for t in paired_times)
    summary=dict(outage_comparison=dict(correction_age_threshold_s=10,criterion="both RTK-fixed, both correction ages > threshold, identical UTC epochs",statistics=outage_stats),mean_rotation_period_s=mean_period,rotation_period_count=len(periods),rotation_period_std_s=st.pstdev(durations),rotation_period_min_s=min(durations),rotation_period_max_s=max(durations),displayed_quality=4,radius_m=radius,center_lat_deg=lat0+math.degrees(cy/m),center_lon_deg=lon0+math.degrees(cx/(n*math.cos(phi))),origin_lat_deg=lat0,origin_lon_deg=lon0,center_east_m=cx,center_north_m=cy,robust_radial_sigma_m=scale,reference_fixed_epochs=len(ref),reference_angle_epochs=len(good),reference_segments=segment+1,unknown_full_turns_across_reference_gaps=True,max_interpolation_gap_s=args.max_gap,common_start_utc_seconds=start,common_end_utc_seconds=end,date=next(iter(dates),None),files=info,statistics=stats)
    (output/'auswertung.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'index.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>Turn-Table-Test</title><body style="font-family:sans-serif"><h1>Turn-Table-Test</h1>'+f'<p>Radius: {radius:.5f} m. Mittlere Umdrehungsdauer: {mean_period:.3f} s ({len(periods)} vollständige Umdrehungen, ohne Referenzlücken). UTC: {dt.timedelta(seconds=start)} bis {dt.timedelta(seconds=end)}. Datum: {summary["date"]} (aus UM980; gleicher Tag für P23A angenommen).</p><p>Rot: P23A_0; grün: P23A_1; blau: UM980; schwarzes Kreuz: Sollposition. Nur RTK-fixed-Positionen (GGA-Qualität 4) sind enthalten. Die Winkelgrafik zeigt den Drehwinkel geteilt durch 360° als Anzahl der Vollkreise.</p><p>Der Referenzwinkel wird aus P23A_0 abgeleitet. Dessen tangentialer Fehler ist damit nicht unabhängig messbar; die rote Spur beschreibt hauptsächlich den radialen Restfehler. Keine Extrapolation oder Interpolation über große Referenzlücken. Keine nachträgliche Zeitverschiebung der Empfänger. Über Referenzlücken ist die Anzahl ganzer Umdrehungen unbekannt; der entfaltete Winkel setzt danach mit dem nächstliegenden Winkel fort (Segmentnummer in referenz_winkel.csv).</p>'+''.join(f'<div><img src="{file}" style="max-width:100%"></div>' for file in ['horizontal.svg','horizontal_detail.svg','winkel.svg','east_zeit.svg','north_zeit.svg','horizontal_zeit.svg'])+'</body></html>')
    from report_languages import append_report_chapters
    append_report_chapters(output)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
