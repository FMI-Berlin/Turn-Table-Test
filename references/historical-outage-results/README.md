# Historical outage comparison

`hrms.csv` contains approximate coordinates extracted from the vector paths of Figure 1, page 2 of `original.pdf`. These are plotted curve coordinates, not original observations. Calibration uses the figure's 0–500 s and 0–1400 mm axes. Displayed precision does not imply measurement precision.

Regenerate with `python3 references/historical-outage-results/extract_pdf_curves.py` (requires Poppler's `pdftocairo`). The standard analysis reads the committed CSV and needs no PDF tools.

`precise_clocks_300s` is one isolated point at approximately 300 s and 20 mm, not a curve. It uses final precise products in the earlier experiment. Historical curves cover 500 s; current measurements end at 299/300 s. The comparison never extends current fits beyond their observed age range. Test geometry, receivers, reference truth and selection criteria differ or are incompletely specified, so the overlay is descriptive rather than a controlled performance ranking.

The detail view includes the two lower historical curves and the isolated precise-clock point. The full view includes all five historical curves.

The source was originally named “Frühere Outage Results.pdf”; the original filenames were normalised during repository organisation. Document contents are unchanged.

## Historical experiment context

Measurement date: **18 July 2005**. Receiver family: **Trimble**, operated **GPS-only**, according to the project owner. These details are supplied context, not inferred from the document export metadata. The 2026 PDF creation date is not the measurement date. Original document contents remain unchanged.
