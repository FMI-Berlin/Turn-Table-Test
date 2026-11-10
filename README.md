# Turn-Table-Test

Analysis of a shared GNSS antenna rotating on a turntable. A continuously corrected receiver defines the expected circle; the other receivers undergo reference-data outages. Python 3.10 or newer is required. The analysis uses only the standard library.

## Repository structure

```text
analysis/                         Shared analysis and report scripts
datasets/                        Dataset configurations and original recordings
  2026-11-03/dataset.json          Receiver mapping and analysis parameters
  2026-11-03/raw/                  Unmodified measurement files
results/<dataset-id>/
  data/                           Measurement CSV files and summary.json
  plots/                          SVG plots in German, English and Chinese
  index.html                      Trilingual HTML report
  report/                         PDF, LaTeX source and figures/
documentation/
  methodology.md                  Shared analysis method and limitations
  assessments/<dataset-id>.md     Dataset-specific interpretation
references/historical-outage-results/
                                  Earlier report and reconstructed curves
comparisons/                      Reserved for comparisons across datasets
tests/                            Standard-library regression tests
```

## Run an analysis

From the repository root:

```bash
python3 analysis/turn_table.py --dataset datasets/2026-11-03
python3 analysis/build_report.py --dataset datasets/2026-11-03
```

Open [the HTML report](results/2026-11-03/index.html) or [the PDF report](results/2026-11-03/report/turn_table_report.pdf). Omitting `--dataset` selects the existing `2026-11-03` dataset. Both commands also accept a path to `dataset.json` directly. Absolute paths work from another working directory.

For isolated output or a different interpolation threshold:

```bash
python3 analysis/turn_table.py --dataset datasets/2026-11-03 --output-dir /tmp/turn-table-check --max-gap 3
python3 analysis/build_report.py --dataset datasets/2026-11-03 --results-dir /tmp/turn-table-check
```

The PDF builder requires XeLaTeX, `fontspec`, `geometry`, `graphicx`, `xcolor`, `booktabs`, `hyperref`, DejaVu fonts and Droid Sans Fallback. It can build a local format from `xetex` and `xelatex.ini` if `xelatex` is unavailable. No shell escape is used. LaTeX figure paths are relative to the report directory.

For layout-only PDF rebuilds, add `--reuse-figures` to the report command to reuse geometry PDFs newer than their SVG sources. Omit this option after changing the SVG-to-PDF converter. The first two LaTeX passes resolve the contents in XDV form; only the final pass renders the complete PDF.

## Add a dataset

1. Create `datasets/<dataset-id>/raw/` and copy the original recordings into it without renaming or editing them. For multiple runs on one date, use an identifier such as `2026-11-03_run-02`.
2. Copy `datasets/dataset.example.json` to `datasets/<dataset-id>/dataset.json`. Set the identifier, measurement date, receiver names (one reference and at least two outage receivers), file paths, reference receiver, colors and known firmware versions. Paths are relative to the configuration file. The reference receiver is processed first.
3. Run both commands with the new dataset path. Outputs go to `results/<dataset-id>/`; earlier datasets remain separate.
4. Optionally write `documentation/assessments/<dataset-id>.md` and set `assessment` to its relative path in the configuration. A manual PDF assessment must contain German, English and Chinese top-level chapters, in that order. Without one, the PDF uses generated numerical summaries and does not reuse the old dataset's interpretation.

Do not reuse an existing dataset identifier for a different recording. The configured date is checked against available NMEA RMC dates. Unknown firmware or test conditions should remain `null`, rather than being guessed. Update manual assessment numbers when inputs or parameters change: prose is not recalculated automatically.

## Existing results

The `2026-11-03` dataset gives a radius of **0.330966 m** and a mean rotation period of **169.599 s** across 76 complete revolutions. For 6,812 paired fixed epochs with both correction ages above 10 s, horizontal RMS is **18.85 mm** for P23A_1 and **26.85 mm** for UM980.

Vertical analysis adds signed height residuals, VRMS versus time (60-second bins) and dAge (10-second bins), and linear fits in mm/s. Heights are converted to ellipsoidal height before comparison with the time-aligned continuous reference. This measures relative height agreement, with bias retained; the reference itself is not an independent accuracy benchmark. CSV exports and `summary.json` include vertical statistics and coefficients.

Plots include every retained fixed-position error, dAge scatter, 10-second HRMS bins, fitted slopes in mm/s, and historical comparison views. All plots show the origin, zero lines and rounded grid intervals. Historical coordinates are approximate reconstructions, not original observations. See [methodology](documentation/methodology.md) and the [dataset assessment](documentation/assessments/2026-11-03.md).

## November 7 dataset

```bash
python3 analysis/turn_table.py --dataset datasets/2026-11-07
python3 analysis/build_report.py --dataset datasets/2026-11-07
```

[HTML report](results/2026-11-07/index.html) · [PDF report](results/2026-11-07/report/turn_table_report.pdf) · [Assessment](documentation/assessments/2026-11-07.md)

P23M_0 is the approximately 10 Hz reference; P23M_1, UM980 and LG290P are approximately 1 Hz outage receivers. The radius is **0.304865 m**, with a mean period of **181.215 s** across 72 complete revolutions. On 7,655 common fixed epochs with every outage receiver's dAge above 10 s, HRMS is **17.59 mm**, **24.06 mm** and **17.84 mm**, respectively. The three-way selection differs from the older two-receiver comparison. P23M_1 and LG290P are close; no statistical significance is claimed for their small RMS difference.

## Report interpretation and references

Reports include a linked table of contents and source links in HTML and PDF. The November 7 assessment explains broadcast-only outage bridging, distinguishes research evidence from manufacturer claims, and evaluates FMI P23A/M against UM980 and LG290P. The historical experiment is dated **18 July 2005**, Trimble GPS-only; the project-owner revision of 10 November 2026 now states this explicitly and names **U. Vollath and S. Klose** in its header. Its current source files are `references/historical-outage-results/trimble-report.docx` and `trimble-report.pdf`.

The bibliography and evidence limits are recorded in [references/literature/](references/literature/README.md). The receiver assessment separates retained-fixed accuracy from whole-record fixed fractions and does not claim an independent absolute ranking or a world first. The earlier discussion is now available as the October 18 ChatGPT implementation note (R10). It documents a discussed 0.36 m over 120 s scale, not a directly comparable FMI HRMS benchmark or verified firmware history.

## Validation and Git

```bash
python3 -m unittest discover -s tests -v
./git-local status
./git-local diff --check
```

This managed environment reserves an empty, read-only `.git/`; `./git-local` uses `.git-local/`. Ordinary clones use standard Git commands. Remote: https://github.com/FMI-Berlin/Turn-Table-Test.git.
