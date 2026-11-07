# Turn-Table-Test — 03.11.2026

Ausführen (Python 3.10 oder neuer, keine Zusatzpakete):

```bash
python3 turn_table.py
```

Anschließend `ergebnisse/index.html` im Browser öffnen. Alle Diagramme liegen auch einzeln als SVG vor. CSV-Dateien enthalten die Messpositionen, interpolierten Sollpositionen, Fixqualität, Korrekturdatenalter und Ost-/Nord-Abweichungen in Metern. `auswertung.json` enthält Fitparameter und Statistik.

Andere Verzeichnisse bzw. maximale Referenzlücke:

```bash
python3 turn_table.py --input-dir . --output-dir ergebnisse --max-gap 3
```

## Verfahren und zeitliche Zuordnung

NMEA-Prüfsummen werden geprüft, ungültige Positionen (Qualität 0) verworfen. Auch wörtlich gespeicherte `\r\n` werden unterstützt. Zeitbasis sind die UTC-Epochen der GGA-Sätze, nicht Dateibeginn oder Zeilennummer. Tageswechsel werden erkannt. Das Datum 03.11.2026 kommt aus UM980-RMC; mangels Datumsinformation in den beiden P23A-Dateien wird für sie derselbe Tag angenommen. Eine unbekannte interne Messlatenz lässt sich allein aus GGA nicht unabhängig prüfen; es wird keine nachträgliche Zeitverschiebung geschätzt.

WGS84-Breite/Länge werden mit den lokalen WGS84-Krümmungsradien in Ost-/Nord-Meter umgerechnet (für diesen kleinen Messbereich ausreichend). Ein geometrischer Kreisfit mit Huber-Gewichten bestimmt Mittelpunkt und Radius aus den RTK-fixed-Positionen (GGA-Qualität 4) von P23A_0. Der Kreisfit verwendet die ganze verfügbare Fixed-Referenz.

Der Referenzwinkel ist `atan2(Nord−Mittelpunkt_Nord, Ost−Mittelpunkt_Ost)`, positiv von Ost nach Nord. Die Winkelgrafik zeigt den relativen Drehwinkel geteilt durch 360° als Anzahl der Vollkreise seit dem ersten Referenzpunkt (einschließlich Bruchteilen). Die CSV-Dateien enthalten zusätzlich diese Umdrehungszahl. Seine zeitliche Entwicklung wird entfaltet; es wird keine konstante Drehgeschwindigkeit vorausgesetzt. Radiale Referenzausreißer oberhalb von max(2 cm, 6 robusten Standardabweichungen) werden für die Winkelbestimmung ausgeschlossen. Bei diesen Daten wurden keine Fixed-Punkte dadurch ausgeschlossen.

Ausgewertet wird der gemeinsame Zeitraum mit verfügbarer Fixed-Referenz. Der entfaltete Winkel wird bei Bedarf zwischen benachbarten zuverlässigen Referenzepochen interpoliert, höchstens über `--max-gap` Sekunden. Keine Extrapolation. Vor dem RTK-fixed-Filter stimmen die 13.191 zeitlich zuordenbaren Epochen aller drei Receiver exakt überein; eine Interpolation ist daher hier nicht nötig. Nach dem Filter enthält jeder Receiver nur seine eigenen RTK-fixed-Epochen; die Zeitzuordnung zur Referenz bleibt unverändert. Zwei größere Referenzlücken werden ausgespart. Über solche Lücken ist die Zahl ganzer Umdrehungen unbekannt; der Winkel wird anschließend mit dem nächstliegenden Winkel fortgesetzt. Die Segmentnummer steht in `referenz_winkel.csv`.

Für jede verwendete Messung gilt:

```
Soll_Ost  = Mittelpunkt_Ost  + R*cos(Winkel(t))
Soll_Nord = Mittelpunkt_Nord + R*sin(Winkel(t))
Fehler    = Messposition(t) − Sollposition(t)
```

Nur RTK-fixed-Positionen (GGA-Qualität 4) werden in Ergebnis-CSV, Diagrammen und Fehlerstatistiken berücksichtigt. GGA-Qualität 4 allein beweist keinen aktiven Empfang von Referenzdaten. Die Outage-Schaltzeiten werden daher nicht aus der Fixqualität oder dem ungefähren 3-/5-Minuten-Zyklus erfunden. Das gemeldete Korrekturdatenalter ist in den CSV-Dateien enthalten.

Da der Sollwinkel aus P23A_0 selbst stammt, kann dessen tangentialer Fehler nicht unabhängig bestimmt werden. Die rote Spur zeigt hauptsächlich den radialen Restfehler. Gemeinsame systematische Fehler aller Receiver können mit dieser Referenzannahme ebenfalls nicht aufgedeckt werden.

## Ergebnis

Mittlere Umdrehungsdauer: **169,599 s** (≈ **2 min 49,6 s**), arithmetisches Mittel aus **76 vollständigen Umdrehungen**. Standardabweichung: **15,028 s**, Minimum: **160,797 s**, Maximum: **292,545 s**.

Je zusammenhängendem Referenzsegment werden ausgehend vom ersten verwendeten Winkel die Zeitpunkte aufeinanderfolgender 360°-Fortschritte bestimmt; die Durchgangszeiten werden zwischen benachbarten Epochen linear interpoliert. Die Dauer jeder vollständigen Umdrehung geht gleich gewichtet in den Mittelwert ein. Unvollständige Umdrehungen am Segmentende und Referenzlücken werden ausgeschlossen. Langsamere Abschnitte oder Stillstände innerhalb einer vollständigen Umdrehung bleiben enthalten. Einzelwerte und Segmentnummern stehen in `ergebnisse/umdrehungsdauer.csv`, Kennwerte zusätzlich in `auswertung.json`.

Radius: **0,330966 m**. Gemeinsamer auswertbarer Zeitraum: **03:41:09–08:15:08 UTC**, mit ausgesparten Referenzlücken.

| Receiver | RMS horizontal | 95%-Quantil | Maximum |
|---|---:|---:|---:|
| P23A_0 | 0,00383 m | 0,00769 m | 0,01710 m |
| P23A_1 | 0,01746 m | 0,03542 m | 0,09647 m |
| UM980 | 0,02071 m | 0,04256 m | 0,07939 m |

Die vollständige horizontale Ansicht enthält sämtliche RTK-fixed-Abweichungen; die zusätzliche Detailansicht zeigt ±10 cm und blendet Punkte außerhalb aus. Gleiche Achsenskalierung, rot=P23A_0, grün=P23A_1, blau=UM980, schwarzes Kreuz=Sollposition. Zusätzlich: Anzahl der Vollkreise, Ost-, Nord- und horizontaler Fehler über der Zeit. Vor dem HRMS-/Fit-Diagramm zeigt `horizontal_dage_scatter.svg` alle verwendbaren RTK-fixed-Einzelwerte des horizontalen Fehlers [mm] über dAge [s], ohne Binning. Before the HRMS/fit plot, `horizontal_dage_scatter.svg` shows every usable RTK-fixed horizontal error sample [mm] versus dAge [s], without binning. `horizontal_dage.svg`: dAge ist das gemeldete GGA-Korrekturdatenalter [s]. HRMS = sqrt(Mittelwert(Ostfehler² + Nordfehler²)) je 10-s-Intervall (0,10], (10,20], …; dAge=0 zählt zum ersten Intervall. Punkte liegen beim mittleren dAge je Intervall. Die Geraden werden ungewichtet an die Intervall-HRMS-Werte angepasst, mit freiem Achsenabschnitt und nur im belegten Altersbereich; ihre Steigungen stehen in mm/s. Alle verwendbaren RTK-fixed-Epochen mit gültigem dAge sind enthalten, ohne Paarung der Receiver. dAge ist keine extern gemessene Outage-Dauer. Alle Diagramme markieren den Ursprung und die Nulllinien; das Raster verwendet runde Schrittweiten. Intervallwerte stehen in `horizontal_dage_hrms.csv`, Fitparameter in `auswertung.json`. Statistiken beziehen sich auf alle verwendeten Epochen, nicht nur auf das Detailfenster oder einzelne Outage-Phasen.

Validiert durch vollständigen Lauf mit den drei Eingabedateien, identische Ergebnis-Zeitstempel, einen synthetischen Kreis mit bekanntem Mittelpunkt/Radius und einen GGA-Mitternachtswechsel.

## Fazit zum Outage-Vergleich

**P23A_1 zeigt die kleineren typischen horizontalen Abweichungen während Abschnitten mit veralteten Referenzdaten.** Der UM980 hat dagegen den kleineren maximalen Einzelfehler. P23A_0 dient als kontinuierlich versorgte Referenz und wird nicht als Outage-Kandidat gewertet.

Für einen fairen direkten Vergleich werden 6.812 identische UTC-Epochen ausgewählt: beide Receiver RTK-fixed, beide mit gemeldetem Korrekturdatenalter >10 s. Das ist ein nachvollziehbarer Indikator für veraltete Korrekturen, kein externes Protokoll der tatsächlichen Schaltzeiten. Nicht-fixed-Positionen und Referenzlücken sind ausgeschlossen. Das Fazit bewertet die Genauigkeit der verbleibenden Fixed-Lösungen, nicht die vollständige Verfügbarkeit über sämtliche Outage-Phasen.

| Receiver | RMS | Median | 95%-Quantil | Maximum |
|---|---:|---:|---:|---:|
| P23A_1 | 1,89 cm | 1,30 cm | 3,59 cm | 9,65 cm |
| UM980 | 2,69 cm | 1,90 cm | 5,42 cm | 7,94 cm |

Damit liegt der RMS von P23A_1 in diesem Vergleich rund 30 % unter dem des UM980. Die einzelnen Vergleichsepochen stehen in `ergebnisse/outage_vergleich.csv`, die Statistik in `auswertung.json`.

# English — Turn-table test — 2026-11-03

Run with Python 3.10 or newer; no additional packages are required:

```bash
python3 turn_table.py
```

Open `ergebnisse/index.html` in a browser. The report contains German, English and Simplified Chinese chapters, each with labelled SVG plots. The SVG files are also available separately. The CSV files contain measured and expected positions, fix quality, correction age, revolutions and east/north errors in metres. `auswertung.json` contains fit parameters and statistics. Machine-readable CSV/JSON field names remain unchanged across languages. Keep `report_languages.py` alongside `turn_table.py`.

To select directories or the maximum reference interpolation gap:

```bash
python3 turn_table.py --input-dir . --output-dir ergebnisse --max-gap 3
```

## Method and time alignment

NMEA checksums are verified and invalid positions (quality 0) are discarded. Literal `\r\n` sequences are supported. Time alignment uses the UTC epochs of the GGA messages, rather than file start times or line numbers. Midnight rollovers are detected. The date, 3 November 2026, comes from UM980 RMC messages; the same date is assumed for both P23A files because they contain no date information. An unknown internal measurement latency cannot be independently verified using GGA alone; no subsequent time shift is estimated.

WGS84 latitude/longitude are converted to local east/north coordinates in metres using local WGS84 radii of curvature, which is sufficient for this small measurement area. A geometric circle fit with Huber weights determines the centre and radius from all available RTK-fixed P23A_0 positions (GGA quality 4).

The reference angle is `atan2(north−centre_north, east−centre_east)`, positive from east towards north. The rotation plot shows the relative angle divided by 360° as the number of revolutions since the first reference point, including fractional turns. The CSV files also include this revolution count. The angle is unwrapped over time; a constant rotation rate is not assumed. Radial reference outliers exceeding max(2 cm, 6 robust standard deviations) are excluded from angle determination. No fixed reference points were excluded by this criterion in these data.

Analysis uses the common time interval with available fixed reference data. Where necessary, the unwrapped angle is interpolated between adjacent reliable reference epochs, across no more than `--max-gap` seconds. There is no extrapolation. Before the RTK-fixed filter, all three receivers have exactly matching timestamps for the 13,191 time-aligned epochs, so interpolation is unnecessary for these data. After filtering, each receiver retains only its own RTK-fixed epochs; alignment to the reference remains unchanged. Two larger reference gaps are excluded. The number of complete revolutions during these gaps is unknown; the angle resumes at the nearest equivalent angle. Segment numbers are recorded in `referenz_winkel.csv`.

For every measurement used:

```
expected_east  = centre_east  + R*cos(angle(t))
expected_north = centre_north + R*sin(angle(t))
error         = measured_position(t) − expected_position(t)
```

Only RTK-fixed positions (GGA quality 4) contribute to result CSV files, plots and error statistics. Quality 4 alone does not prove that correction data are currently being received. Outage switching times are therefore not inferred from fix quality or the approximate 3/5-minute cycle. Reported correction ages are included in the CSV files.

Because the expected angle is derived from P23A_0 itself, its tangential error cannot be determined independently. The red trace mainly shows its radial residual. Systematic errors common to all receivers also cannot be identified under this reference assumption.

## Results

Mean rotation period: **169.599 s** (approximately **2 min 49.6 s**), the arithmetic mean of **76 complete revolutions**. Standard deviation: **15.028 s**; minimum: **160.797 s**; maximum: **292.545 s**.

Within each continuous reference segment, successive 360° advances are timed relative to the first angle used. Crossing times are linearly interpolated between adjacent epochs. Each complete revolution has equal weight in the mean. Incomplete turns at segment ends and reference gaps are excluded. Slower motion or stops within a complete turn remain included. Individual durations and segment numbers are saved in `ergebnisse/umdrehungsdauer.csv`; summary values are also recorded in `auswertung.json`.

Radius: **0.330966 m**. Common analysis interval: **03:41:09–08:15:08 UTC**, excluding reference gaps.

| Receiver | Horizontal RMS | 95th percentile | Maximum |
|---|---:|---:|---:|
| P23A_0 | 0.00383 m | 0.00769 m | 0.01710 m |
| P23A_1 | 0.01746 m | 0.03542 m | 0.09647 m |
| UM980 | 0.02071 m | 0.04256 m | 0.07939 m |

The full horizontal view shows all RTK-fixed errors. The detail view covers ±10 cm and hides points outside this range. Both axes have equal scales. Red=P23A_0, green=P23A_1, blue=UM980, black cross=expected position. Additional plots show revolutions and east, north and horizontal errors over time. Before the HRMS/fit plot, `horizontal_dage_scatter.svg` shows every usable RTK-fixed horizontal error sample [mm] versus dAge [s], without binning. `horizontal_dage.svg`: dAge is the reported GGA correction age [s]. HRMS = sqrt(mean(east error² + north error²)) per 10-s interval (0,10], (10,20], …; age zero belongs to the first interval. Points use the mean observed age in each interval. Lines use unweighted least squares on interval HRMS values with a free intercept, restricted to the observed age range; slopes are in mm/s. All usable RTK-fixed epochs with valid dAge are included, without pairing receivers. dAge is not an externally measured outage duration. All plots mark the origin and zero lines, with rounded grid steps. Bin values are saved in `horizontal_dage_hrms.csv`, fit parameters in `auswertung.json`. Statistics cover all retained epochs, rather than just the detail window or individual outage phases.

Validation included a complete run with all three input files, matching timestamps before the fixed filter and reference alignment after it, a synthetic circle with known centre/radius, a GGA midnight rollover, and the conversion from degrees to revolutions.

## Outage comparison conclusion

**P23A_1 has smaller typical horizontal errors during periods with stale reference data.** UM980 has the smaller maximum individual error. P23A_0 receives continuous reference data and is the reference, rather than an outage comparison candidate.

The direct comparison uses 6,812 identical UTC epochs where both receivers are RTK-fixed and both report correction ages >10 s. This is an explicit indicator of stale corrections, not an external log of actual switching times. Non-fixed positions and reference gaps are excluded. The conclusion assesses the accuracy of the remaining fixed solutions, not complete availability throughout all outage phases.

| Receiver | RMS | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
| P23A_1 | 1.89 cm | 1.30 cm | 3.59 cm | 9.65 cm |
| UM980 | 2.69 cm | 1.90 cm | 5.42 cm | 7.94 cm |

P23A_1 therefore has approximately 30% lower RMS than UM980 in this comparison. Individual comparison epochs are saved in `ergebnisse/outage_vergleich.csv`, with summary statistics in `auswertung.json`.

# 中文（简体）— 转台测试 — 2026年11月3日

运行环境为 Python 3.10 或更新版本，无需安装额外软件包：

```bash
python3 turn_table.py
```

在浏览器中打开 `ergebnisse/index.html`。报告依次包含德文、英文和简体中文章节，每个章节均配有相应语言标注的 SVG 图。各 SVG 图也可单独打开。CSV 文件包含实测位置、理论位置、定位解质量、差分改正数据龄期、旋转圈数以及以米为单位的东向和北向误差。`auswertung.json` 包含拟合参数和统计结果。CSV/JSON 的机器可读字段名不随报告语言改变。请将 `report_languages.py` 与 `turn_table.py` 放在同一目录中。

如需指定目录或参考数据插值所允许的最大时间间隔：

```bash
python3 turn_table.py --input-dir . --output-dir ergebnisse --max-gap 3
```

## 方法与时间对齐

程序验证 NMEA 校验和，并丢弃无效位置（质量标识为 0）。同时支持以字面字符形式保存的 `\r\n`。时间对齐采用 GGA 消息中的 UTC 历元，而非文件起始时间或行号。程序可识别跨越午夜的情况。日期 2026 年 11 月 3 日来自 UM980 的 RMC 消息；由于两份 P23A 文件不含日期信息，假定其采集于同一天。仅凭 GGA 无法独立验证未知的接收机内部测量延迟，因此不估计或施加事后时间平移。

利用当地 WGS84 曲率半径，将 WGS84 经纬度转换为以米为单位的局部东向和北向坐标；对于本测试的小范围测量，该近似足够。采用带 Huber 权重的几何圆拟合，使用 P23A_0 全部可用的 RTK 固定解位置（GGA 质量标识为 4）估计圆心和半径。

参考角为 `atan2(北向坐标−圆心北向坐标, 东向坐标−圆心东向坐标)`，从东向北为正方向。旋转图将相对转角除以 360°，表示自首个参考点起的旋转圈数，包括不足一圈的小数部分。CSV 文件也包含该圈数。角度随时间进行展开，不假定恒定转速。若参考点的径向残差超过 max(2 cm, 6 倍稳健标准差)，则不使用该点确定角度。本次数据中，没有固定解参考点因该条件被剔除。

分析仅覆盖具有可用固定解参考数据的共同时间范围。必要时，在相邻可靠参考历元之间对展开角进行插值，间隔不超过 `--max-gap` 秒；不进行外推。在 RTK 固定解筛选之前，三个接收机可按时间对齐的 13,191 个历元具有完全相同的时间戳，因此本次数据无需插值。筛选后，各接收机仅保留自身的 RTK 固定解历元，与参考数据的时间对应关系保持不变。两处较大的参考数据缺口被排除。缺口期间的完整旋转圈数未知；缺口后的角度采用最接近的等效角继续。分段编号记录于 `referenz_winkel.csv`。

对每个参与分析的测量值：

```
理论东向坐标 = 圆心东向坐标 + R*cos(角度(t))
理论北向坐标 = 圆心北向坐标 + R*sin(角度(t))
误差         = 实测位置(t) − 理论位置(t)
```

结果 CSV、图表及误差统计仅包含 RTK 固定解位置（GGA 质量标识为 4）。仅凭质量标识 4 不能证明接收机当时正在接收差分改正数据，因此不根据解质量或近似的“3 分钟有改正、5 分钟中断”周期推断实际切换时刻。接收机报告的改正数据龄期保存在 CSV 文件中。

由于理论角本身来自 P23A_0，无法独立确定其切向误差。红色轨迹主要表示其径向残差。在这一参考假设下，也无法识别所有接收机共有的系统误差。

## 结果

平均旋转周期：**169.599 秒**（约 **2 分 49.6 秒**），为 **76 次完整旋转**周期的算术平均值。标准差：**15.028 秒**；最小值：**160.797 秒**；最大值：**292.545 秒**。

在每个连续参考数据段内，以首个参与分析的角度为起点，确定连续推进 360° 的通过时刻，并在相邻历元之间进行线性插值。每次完整旋转在平均值中具有相同权重。数据段末尾不完整的旋转及参考数据缺口被排除；完整旋转期间的减速或停顿仍计入周期。各次旋转的周期和分段编号保存在 `ergebnisse/umdrehungsdauer.csv` 中，汇总值也记录于 `auswertung.json`。

半径：**0.330966 m**。共同可分析时间范围：**03:41:09–08:15:08 UTC**，其中已排除参考数据缺口。

| 接收机 | 水平误差均方根（RMS） | 第 95 百分位数 | 最大值 |
|---|---:|---:|---:|
| P23A_0 | 0.00383 m | 0.00769 m | 0.01710 m |
| P23A_1 | 0.01746 m | 0.03542 m | 0.09647 m |
| UM980 | 0.02071 m | 0.04256 m | 0.07939 m |

完整水平视图显示全部 RTK 固定解误差。局部视图覆盖 ±10 cm，并隐藏范围外的数据点。两个坐标轴采用相同的比例尺。红色=P23A_0，绿色=P23A_1，蓝色=UM980，黑色十字=理论位置。另有旋转圈数、东向误差、北向误差和水平误差随时间变化的图。在 HRMS 及拟合图之前，`horizontal_dage_scatter.svg` 显示全部可用 RTK 固定解单点水平误差 [mm] 随 dAge [s] 的变化，不进行分箱。`horizontal_dage.svg`：dAge 为 GGA 报告的改正数据龄期 [s]。每个 10 秒区间 (0,10]、(10,20] 等计算 HRMS = sqrt(平均值(东向误差² + 北向误差²))；零龄期计入首个区间。点的横坐标为各区间的平均龄期。对各区间 HRMS 采用不加权最小二乘直线拟合，截距自由，仅在实际龄期范围内绘制，斜率单位为 mm/s。包含具有有效 dAge 的全部可用 RTK 固定解历元，不要求接收机历元配对。dAge 并非外部测得的中断持续时间。所有图均标出原点和零轴，网格采用整齐的步长。区间值保存在 `horizontal_dage_hrms.csv`，拟合参数保存在 `auswertung.json`。统计值基于全部保留历元，而非仅局部视图或某些中断阶段的数据。

验证包括：使用三份输入文件完整运行；确认固定解筛选前的时间戳一致性以及筛选后与参考数据的时间对齐；已知圆心和半径的合成圆测试；GGA 跨午夜测试；以及从角度到旋转圈数的换算检查。

## 参考数据中断对比结论

**在改正数据过时的时段内，P23A_1 的典型水平误差更小。** 但 UM980 的最大单次误差更小。P23A_0 持续接收参考数据，仅作为参考基准，不参与中断性能排名。

直接对比采用 6,812 个相同 UTC 历元，要求两个接收机均为 RTK 固定解，且均报告超过 10 秒的改正数据龄期。这是明确、可复现的改正数据过时判据，并非外部日志记录的实际切换时刻。非固定解位置和参考数据缺口均被排除。因此，结论评价的是保留的固定解精度，而非整个中断期间的完整可用性。

| 接收机 | 均方根 | 中位数 | 第95百分位数 | 最大值 |
|---|---:|---:|---:|---:|
| P23A_1 | 1.89 cm | 1.30 cm | 3.59 cm | 9.65 cm |
| UM980 | 2.69 cm | 1.90 cm | 5.42 cm | 7.94 cm |

本次比较中，P23A_1 的均方根误差比 UM980 低约 30%。各对比历元保存在 `ergebnisse/outage_vergleich.csv`，汇总统计保存在 `auswertung.json`。
