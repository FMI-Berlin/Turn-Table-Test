# Repository Guidelines

## Project Structure & Module Organization

- `analysis/turn_table.py`: standard-library GNSS parsing, circle fitting, time alignment, statistics, and SVG/CSV/JSON generation.
- `analysis/report_languages.py`: English and Simplified Chinese translations of the German HTML/SVG report.
- `analysis/report_markdown.py`: shared escaped HTML rendering, source links, and contents navigation.
- `analysis/build_report.py`: LaTeX and PDF generation from `documentation/assessments/<dataset-id>.md` and generated diagrams.
- `datasets/<dataset-id>/raw/`: measurement inputs; preserve original filenames, including `p23a_continious.nmea`. The `.rawpb` file is additional raw data.
- `results/<dataset-id>/`: generated HTML, SVG plots, CSV measurements, and JSON statistics.
- `results/<dataset-id>/report/`: report source, PDF, and vector assets in `figures/`.

## Build, Test, and Development Commands

Run from the repository root with Python 3.10 or newer:

```bash
python3 analysis/turn_table.py --dataset datasets/2026-11-03
python3 analysis/turn_table.py --dataset datasets/2026-11-03 --output-dir /tmp/turn-table-check --max-gap 3
python3 analysis/build_report.py --dataset datasets/2026-11-03
```

The first command regenerates `results/<dataset-id>/`; the second produces an isolated analysis for comparison. Open `results/2026-11-03/index.html` to inspect results. The PDF builder reads the selected dataset's `results/<dataset-id>/`, requiring XeLaTeX, the packages and fonts listed in `README.md`, or the documented XeTeX fallback.

Dataset configurations live in `datasets/<dataset-id>/dataset.json`. Shared methodology is in `documentation/methodology.md`; historical source documents and extracted curves are in `references/historical-outage-results/`.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, and uppercase constants. Keep analysis dependencies within Python's standard library. Preserve machine-readable field names and unit suffixes such as `_m`, `_mm`, and `_s`. Translate new report labels into all three languages. Keep citations linked in HTML and PDF; identify research, manufacturer claims, and project-owner context separately. Retain visible origins, zero lines, rounded grid steps, and the raw dAge scatter plot before its HRMS/fit plot.

## Testing Guidelines

Run `python3 -m unittest discover -s tests -v` for the standard-library dataset and report regression tests. No coverage threshold or formatter/linter is configured. Validate numerical changes with synthetic cases covering known circles, time gaps, midnight rollover, RMS bins, or regression as appropriate. Run the complete analysis and compare CSV/JSON results. For plot changes, inspect HTML and PDF in all languages, checking units, labels, ordering, and point counts.

## Commit & Pull Request Guidelines

The brief history uses descriptive English subjects, for example `Document GitHub remote and support standard clones`; follow that style. In this managed workspace, use `./git-local status` and `./git-local diff --check`; ordinary clones use standard Git commands. PRs should explain the change, validation, and numerical effects, with plot previews for visual changes. Regenerate affected artifacts together. Update result text in `documentation/assessments/<dataset-id>.md` manually when numbers change: the PDF builder does not recalculate that prose.
