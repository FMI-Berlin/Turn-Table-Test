# Analysis methodology

## Inputs and reference

Each dataset contains a reference recording and at least two outage receiver recordings and a `dataset.json` configuration. Original filenames and recording bytes are preserved. The continuously corrected receiver provides the reference circle and rotation angle; the remaining receivers are the outage candidates.

NMEA checksums and fields are validated. GGA UTC epochs establish alignment; midnight rollovers are tracked. RMC dates, when present, must match the configured date. Receivers without dates are assumed to belong to that day. No positional time-shift fitting is performed.

## Circle and errors

Positions are converted to local WGS84 east/north coordinates. A robust geometric Huber fit estimates the reference circle from RTK-fixed positions (GGA quality 4). Reference positions with radial residuals above `max(0.02 m, 6 × robust sigma)` are excluded from angle estimation.

Angles are unwrapped inside continuous reference segments. Expected positions are interpolated only inside segments, with the configured maximum reference gap (default 3 seconds). There is no extrapolation across missing reference data. Full-turn counts across gaps remain unknown.

Horizontal error is the distance between a measured position and the time-aligned expected circle position. Complete rotation durations are equally weighted; incomplete turns and turns spanning reference gaps are excluded. Statistical fields retain their existing machine-readable names and unit suffixes.

## Correction age and HRMS

`dAge` is reported GGA correction age in seconds, not an independently logged outage duration. The scatter plot includes every usable fixed epoch with finite, nonnegative age. HRMS bins use `(0,10]`, `(10,20]`, etc.; age zero belongs to the first bin. Each point uses the mean observed age and `sqrt(mean(east_error² + north_error²))`, expressed in millimetres.

An unweighted least-squares line with a free intercept is fitted across bin HRMS values. Slopes are in mm/s; lines stop at observed mean ages. These are empirical trends, not physical limits. The paired outage comparison separately requires identical UTC epochs, all outage receivers fixed, and every correction age above 10 seconds.

## Limits and historical comparisons

The reference receiver's tangential error is not independently observable; shared systematic errors may remain hidden. Statistics describe retained fixed solutions, not full outage availability or absolute accuracy.

Historical curves are reconstructed from Figure 1 of `references/historical-outage-results/trimble-report.pdf`. The approximately 20 mm point near 300 seconds uses final precise clock/orbit products. Different test conditions limit direct rankings. Dataset-specific interpretations belong in `documentation/assessments/`, not shared numerical code.

## Relative vertical accuracy

Recover ellipsoidal height as `h = GGA altitude + GGA geoid separation` (both in metres). The recorded receivers use different geoid separations, including zero, so comparing altitude fields alone produces metre-scale artefacts. Missing, nonfinite, or non-metric height fields are excluded from vertical analysis without changing the horizontal selection.

Use `delta_h = h_receiver - h_reference(t)` for the shared antenna. Interpolate only RTK-fixed reference heights, without extrapolation or bridging intervals longer than the configured `max_gap_s`. Apply the existing horizontal epoch selection first. No receiver-specific offset is removed. This is relative agreement, not independently measured absolute vertical accuracy; reference errors and correlated errors limit interpretation. The reference's own residual is zero by construction and is excluded from plots/fits.

Plot signed raw height residuals over elapsed time and dAge before interpreting RMS. Define `VRMS = sqrt(mean(delta_h²))`, which includes bias, and separately report mean bias and population standard deviation (`VRMS² = bias² + STD²`). Export per-receiver heights/residuals in `data/*_vertical.csv`, 10-second dAge VRMS bins and 60-second elapsed-time VRMS bins in `data/vertical_*_vrms.csv`. Use the same interval boundary convention and unweighted OLS fit as HRMS, free intercept and observed mean bin coordinates. Fit slopes use mm/s even when the time axis is displayed in minutes. The full-record time slope includes repeated outages and is not a per-outage drift rate.

The paired vertical comparison requires valid heights at identical UTC epochs across every outage receiver, with each dAge > 10 s. Binned plots use each receiver's own eligible epochs. Numerical statistics, fit coefficients, sample counts, and reference definitions are stored under `vertical` in `summary.json` and rendered into all three report languages.

## Report organisation and equations

PDF and HTML use one shared assembler. The English cover distinguishes author/company, report issue date and dataset measurement date. German, English and Simplified Chinese editions preserve the same scientific order: setup and rotation, horizontal errors, common-epoch comparison, HRMS versus correction age, then relative vertical accuracy. Rotation/wind-up discussion and historical interpretation follow the results. Reproduction commands appear at the end of each language edition.

Figures remain beside their related sections, with raw scatter before binned RMS/fit plots. The numerical CSV/JSON outputs and SVG data are not changed by report layout. Statistical tables use millimetres; plots and CSV fields retain their explicitly labelled units. Equations show the expected circle, residuals, bin RMS, unweighted least squares, ellipsoidal height, bias/STD decomposition and rotation/wind-up scales. They are typeset as LaTeX mathematics in PDF and native MathML in HTML, without a network-based math renderer.

One English reference list follows all language editions. The source catalog provides authors, publication details, evidence scope and source links; citations in every edition point to the same reference anchors. Local PDF/DOCX links are relative to the report location.
