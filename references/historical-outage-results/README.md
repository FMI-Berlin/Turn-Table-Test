# Historical Trimble GPS-only outage comparison

## Source documents

- [trimble-report.pdf](trimble-report.pdf): current PDF, three pages; Figure 1 (HRMS) is on page 2 and Figure 2 (satellite clocks) is on page 3.
- [trimble-report.docx](trimble-report.docx): editable source supplied by the project owner.

The revised header identifies **18 July 2005**, **Trimble**, **GPS-only**, and **U. Vollath and S. Klose**. These details previously came from project-owner context; they now appear explicitly in the owner's document revision of **10 November 2026**. The 2026 PDF export date is not the measurement date. Its embedded PDF title still contains an earlier Word filename; use the visible report header and the current filenames for citations.

The documents were previously stored as `original.docx` and `original.pdf`, following the earlier title “Frühere Outage Results”. A paragraph comparison of the old and revised DOCX confirms that only the opening title/header text changed. Formatting and pagination changed, including the chart's position on page 2; the explanatory body paragraphs are unchanged. The owner-supplied documents are preserved as received. R1 in [the literature catalog](../literature/catalog.json) records both paths, revision context and SHA-256 hashes.

## Reconstructed curve data

`hrms.csv` contains approximate coordinates extracted from Figure 1's vector paths, not original observations. Calibration uses its 0–500 s and 0–1400 mm axes. Displayed precision does not imply measurement precision.

Regenerate from the current PDF with:

```bash
python3 references/historical-outage-results/extract_pdf_curves.py
```

This requires Poppler's `pdftocairo`. The extractor detects the chart frame and transforms each path into page coordinates; it no longer depends on the old chart position. It also writes `hrms.provenance.json` with source/CSV hashes, calibration bounds and point counts. Use `--pdf` and `--output` for an isolated extraction. Normal dataset analysis reads the committed CSV and requires no PDF tools.

Re-extraction after the November 10 revision preserves all six series and their reported approximate accuracy levels. The maximum difference between the old and new piecewise-linear curves is below 0.08 mm over 0–500 s. These differences and changed vertex counts arise from the new PDF export. `precise_clocks_300s` remains one isolated point near 300 s and 20 mm, using final precise products, not a curve.

## Comparison limits and archived history

Historical curves cover 500 s; current measurements end at 299/300 s. Current fits are never extended beyond their observed age range. The detail view includes the two lower historical curves and the isolated precise-clock point; the full view includes all five curves. Test geometry, receivers, reference truth and selection criteria differ or are incompletely specified, so overlays are descriptive rather than controlled product rankings.

The October 18 implementation note and `documentation/work-logs/` are historical source material and dated snapshots. They retain the filenames and statements recorded at their creation; they are not rewritten to follow a later rename. Active scripts, documentation, literature entries and generated reports use the current source names.
