# Turn-Table-Test — 2026-11-03

[Deutsch](#deutsch) · [English](#english) · [简体中文](#简体中文)

## Deutsch

Auswertung eines rotierenden Antennenaufbaus mit drei GNSS-Receivern und gemeinsamer Antenne. P23A_0 erhält kontinuierliche Referenzdaten und definiert den Sollkreis. P23A_1 und UM980 durchlaufen Referenzdaten-Outages.

### Starten

Python 3.10 oder neuer; die Analyse benötigt keine externen Python-Pakete:

```bash
python3 turn_table.py
```

Danach [ergebnisse/index.html](ergebnisse/index.html) im Browser öffnen. Die Übersicht enthält deutsche, englische und chinesische Kapitel einschließlich übersetzter Diagramme.

```bash
python3 turn_table.py --input-dir . --output-dir ergebnisse --max-gap 3
```

### Ergebnis

- Kreisradius: **0,330966 m**.
- Mittlere Umdrehungsdauer: **169,599 s**, berechnet aus 76 vollständigen Umdrehungen ohne Referenzlücken.
- Nur RTK-fixed-Positionen (GGA-Qualität 4), Zuordnung anhand der UTC-Messzeit.
- **P23A_1 hat die kleineren typischen Outage-Abweichungen:** bei 6.812 identischen Fixed-Epochen mit beidseitigem Korrekturdatenalter >10 s beträgt der horizontale RMS **1,89 cm**, gegenüber **2,69 cm** beim UM980.
- UM980 hat den kleineren maximalen Einzelfehler: **7,94 cm** gegenüber **9,65 cm**.

Das Fazit betrifft die Genauigkeit der erhaltenen Fixed-Lösungen. Es bewertet nicht die gesamte Verfügbarkeit während der Outages. Die tatsächlichen Schaltzeiten wurden nicht extern protokolliert. Das Testdatum stammt aus UM980-RMC; für die P23A-Dateien wird derselbe Tag angenommen. Der Sollwinkel aus P23A_0 lässt dessen tangentialen Eigenfehler nicht unabhängig erkennen. Weitere Methoden und Grenzen: [AUSWERTUNG.md](AUSWERTUNG.md).

### Dateien

| Datei | Inhalt |
|---|---|
| `p23a_continious.nmea` | P23A_0, kontinuierliche Referenzdaten; Schreibweise des Originalnamens beibehalten |
| `p23a_outages.nmea` | P23A_1 mit Referenzdaten-Outages |
| `um980_outages.nmea` | UM980 mit Referenzdaten-Outages |
| `turn_table.py`, `report_languages.py` | Analyse und dreisprachige HTML-/SVG-Ausgabe; beide Dateien zusammen aufbewahren |
| `AUSWERTUNG.md` | Dreisprachige Methodik, Ergebnisse und Fazit |
| `ergebnisse/` | HTML, SVG, Messwert-CSV und JSON-Statistiken |
| `bericht/turn_table_report.tex` | LaTeX-Bericht in allen drei Sprachen |
| `bericht/turn_table_report.pdf` | Fertiger PDF-Bericht in allen drei Sprachen |
| `bericht/abbildungen/` | Vektorgrafiken für den LaTeX-Bericht |
| `build_report.py` | Erzeugung von LaTeX und PDF aus Dokumentation und Diagrammen |

### LaTeX/PDF neu erzeugen

Voraussetzungen zusätzlich zur Analyse: XeLaTeX mit `fontspec`, `geometry`, `graphicx`, `xcolor`, `booktabs`, `hyperref` sowie DejaVu- und Droid-Sans-Fallback-Schriften für chinesische Zeichen. Kein Shell-Escape nötig. Fehlt der Befehl `xelatex`, kann das Skript aus einem vorhandenen `xetex` und `xelatex.ini` ein lokales Format erzeugen.

```bash
python3 turn_table.py
python3 build_report.py
```

Der Berichtsaufbau verwendet `AUSWERTUNG.md` und `ergebnisse/` im Projektverzeichnis. Nach Änderungen an Eingabedaten die Ergebniszahlen und Texte in `AUSWERTUNG.md` ebenfalls aktualisieren: Die Berichtserzeugung übernimmt diese Dokumentation, statt ihre Zahlen automatisch neu zu berechnen. Das PDF enthält sechs Diagramme pro Sprache. Der HTML-Bericht und die CSV-/JSON-Ergebnisse werden dagegen direkt aus den Messdaten erzeugt.

## English

This project analyses a rotating shared GNSS antenna connected to three receivers. P23A_0 continuously receives reference data and defines the expected circle. P23A_1 and UM980 experience reference-data outages.

### Run

Python 3.10 or newer is required; the analysis needs no third-party Python packages:

```bash
python3 turn_table.py
```

Open [ergebnisse/index.html](ergebnisse/index.html) for German, English and Simplified Chinese chapters with translated plots. Options: `--input-dir`, `--output-dir`, `--max-gap` (maximum reference interpolation gap in seconds; default 3).

### Results

Radius: **0.330966 m**. Mean rotation period: **169.599 s**, based on 76 complete revolutions excluding reference gaps. Only RTK-fixed positions (GGA quality 4) are displayed, aligned using UTC measurement epochs.

**P23A_1 has the smaller typical outage errors:** for 6,812 identical fixed epochs with correction ages >10 s at both receivers, horizontal RMS is **1.89 cm**, versus **2.69 cm** for UM980. UM980 has the smaller maximum individual error: **7.94 cm**, versus **9.65 cm**.

This conclusion concerns the accuracy of retained fixed solutions, not overall outage availability. Actual outage switching times were not externally logged. The test date comes from UM980 RMC; the same day is assumed for the P23A files. Because the reference angle comes from P23A_0, its tangential error cannot be independently measured.

### Outputs and PDF generation

- [AUSWERTUNG.md](AUSWERTUNG.md): full methodology, results and conclusion in all three languages.
- [PDF report](bericht/turn_table_report.pdf) and [LaTeX source](bericht/turn_table_report.tex): all three languages, with six plots per language.
- `ergebnisse/`: HTML, SVG plots, measurement CSV files, rotation durations, paired outage comparison and JSON statistics.
- Keep `turn_table.py` and `report_languages.py` together. Input filenames and machine-readable fields remain unchanged.

To regenerate the LaTeX/PDF report, run `python3 build_report.py` after the analysis. This additionally requires XeLaTeX, the packages `fontspec`, `geometry`, `graphicx`, `xcolor`, `booktabs`, `hyperref`, and the DejaVu and Droid Sans Fallback fonts. No shell escape is needed. The builder reads `AUSWERTUNG.md` and `ergebnisse/` from the project directory and writes `bericht/`, including the figure assets needed by the LaTeX source. If input data change, also update the results and text in `AUSWERTUNG.md`; the PDF builder uses that document without recalculating its numbers. HTML and CSV/JSON results are generated directly from the measurements.

## 简体中文

本项目分析一套旋转的 GNSS 共用天线系统。三个接收机通过分配器连接同一天线。P23A_0 持续接收参考数据，用于确定理论圆周；P23A_1 和 UM980 经历参考数据中断。

### 运行

需要 Python 3.10 或更新版本；分析程序无需第三方 Python 软件包：

```bash
python3 turn_table.py
```

在浏览器中打开 [ergebnisse/index.html](ergebnisse/index.html)，可查看德文、英文和简体中文章节及相应语言的图表。可选参数：`--input-dir`（输入目录）、`--output-dir`（输出目录）、`--max-gap`（参考插值允许的最大时间间隔，默认 3 秒）。

### 结果

半径：**0.330966 m**。平均旋转周期：**169.599 秒**，基于排除参考数据缺口后的 76 次完整旋转。仅显示 RTK 固定解位置（GGA 质量标识为 4），按 UTC 测量历元进行时间对齐。

**P23A_1 的典型中断误差更小：** 在两个接收机均为固定解且改正数据龄期均超过 10 秒的 6,812 个相同历元中，P23A_1 的水平误差均方根为 **1.89 cm**，UM980 为 **2.69 cm**。但 UM980 的最大单次误差更小：**7.94 cm**，P23A_1 为 **9.65 cm**。

本结论针对保留下来的固定解精度，不评价整个中断期间的完整可用性。实际中断切换时刻未由外部日志记录。测试日期来自 UM980 的 RMC 消息，P23A 数据假定采集于同一天。由于参考角来自 P23A_0，无法独立测量其自身的切向误差。

### 输出与 PDF 生成

- [AUSWERTUNG.md](AUSWERTUNG.md)：三种语言的完整方法、结果和结论。
- [PDF 报告](bericht/turn_table_report.pdf) 和 [LaTeX 源文件](bericht/turn_table_report.tex)：包含全部三种语言，每种语言各六幅图。
- `ergebnisse/`：HTML、SVG 图、测量 CSV、旋转周期、配对中断比较和 JSON 统计。
- 请将 `turn_table.py` 和 `report_languages.py` 保存在同一目录。原始输入文件名和机器可读字段名保持不变。

分析完成后运行 `python3 build_report.py` 可重新生成 LaTeX/PDF。额外需要 XeLaTeX、`fontspec`、`geometry`、`graphicx`、`xcolor`、`booktabs`、`hyperref` 软件包，以及 DejaVu 和用于中文字符的 Droid Sans Fallback 字体。无需启用 shell escape。生成程序读取项目目录中的 `AUSWERTUNG.md` 和 `ergebnisse/`，并将报告及 LaTeX 所需的图形资源写入 `bericht/`。若输入数据改变，还应更新 `AUSWERTUNG.md` 中的结果数值和文字；PDF 生成程序直接采用该文档，不会重新计算文档中的数值。HTML 和 CSV/JSON 结果则直接根据测量数据生成。

## Lokales Git-Repository / Local Git repository / 本地 Git 仓库

Die Umgebung stellt `.git` schreibgeschützt bereit. Deshalb liegen die lokalen Git-Metadaten unter `.git-local/`. Der Aufrufhelfer verwendet automatisch dieses Repository:

The environment reserves a read-only `.git` directory. Local Git metadata therefore reside in `.git-local/`. Use the wrapper to address this repository:

当前环境中的 `.git` 目录为只读，因此本地 Git 元数据保存在 `.git-local/` 中。请使用以下辅助命令操作仓库：

```bash
./git-local status
./git-local log --oneline
./git-local add README.md
./git-local commit -m "Update documentation"
```

GitHub-Remote: https://github.com/FMI-Berlin/Turn-Table-Test.git. Temporäre Dateien und Build-Caches sind ausgeschlossen. Für den ersten Commit wird mangels vorhandener Git-Identität die lokale Projektkennung `Turn-Table-Test <turn-table-test@localhost>` verwendet; globale Git-Einstellungen werden nicht verändert.

GitHub remote: https://github.com/FMI-Berlin/Turn-Table-Test.git. Temporary files and build caches are ignored. In the absence of an existing Git identity, the initial commit uses the local project identity `Turn-Table-Test <turn-table-test@localhost>`; global Git settings are unchanged.

GitHub 远程仓库：https://github.com/FMI-Berlin/Turn-Table-Test.git。临时文件及构建缓存已排除。由于没有现有的 Git 身份配置，首次提交采用本地项目身份 `Turn-Table-Test <turn-table-test@localhost>`，不会修改全局 Git 设置。

Außerhalb dieser Umgebung lässt sich das Projekt regulär klonen; danach funktionieren normale `git`-Befehle. / Outside this environment, clone normally and use standard `git` commands. / 在此环境之外，可正常克隆并使用标准 `git` 命令。

```bash
git clone https://github.com/FMI-Berlin/Turn-Table-Test.git
```
