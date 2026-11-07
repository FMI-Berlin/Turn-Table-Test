# Repository Guidelines

## Project Structure & Module Organization

- `turn_table.py`: standard-library GNSS parsing, circle fitting, time alignment, statistics, and SVG/CSV/JSON generation.
- `report_languages.py`: English and Simplified Chinese translations of the German HTML/SVG report.
- `build_report.py`: LaTeX and PDF generation from `AUSWERTUNG.md` and generated diagrams.
- Root-level `.nmea` files: measurement inputs; preserve original filenames, including `p23a_continious.nmea`. The `.rawpb` file is additional raw data.
- `ergebnisse/`: generated HTML, SVG plots, CSV measurements, and JSON statistics.
- `bericht/`: report source, PDF, and vector assets in `abbildungen/`.

## Build, Test, and Development Commands

Run from the repository root with Python 3.10 or newer:

```bash
python3 turn_table.py
python3 turn_table.py --output-dir /tmp/turn-table-check --max-gap 3
python3 build_report.py
```

The first command regenerates `ergebnisse/`; the second produces an isolated analysis for comparison. Open `ergebnisse/index.html` to inspect results. The PDF builder reads the repository's `ergebnisse/`, requiring XeLaTeX, the packages and fonts listed in `README.md`, or the documented XeTeX fallback.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, and uppercase constants. Keep analysis dependencies within Python's standard library. Preserve machine-readable field names and unit suffixes such as `_m`, `_mm`, and `_s`. Translate new report labels into all three languages. Retain visible origins, zero lines, rounded grid steps, and the raw dAge scatter plot before its HRMS/fit plot.

## Testing Guidelines

No automated test suite, test framework, coverage threshold, or formatter/linter is configured. Validate numerical changes with synthetic cases covering known circles, time gaps, midnight rollover, RMS bins, or regression as appropriate. Run the complete analysis and compare CSV/JSON results. For plot changes, inspect HTML and PDF in all languages, checking units, labels, ordering, and point counts.

## Commit & Pull Request Guidelines

The brief history uses descriptive English subjects, for example `Document GitHub remote and support standard clones`; follow that style. In this managed workspace, use `./git-local status` and `./git-local diff --check`; ordinary clones use standard Git commands. PRs should explain the change, validation, and numerical effects, with plot previews for visual changes. Regenerate affected artifacts together. Update result text in `AUSWERTUNG.md` manually when numbers change: the PDF builder does not recalculate that prose.
