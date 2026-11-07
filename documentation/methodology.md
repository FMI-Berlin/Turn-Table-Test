# Analysis methodology

## Inputs and reference

Each dataset contains three receiver recordings and a `dataset.json` configuration. Original filenames and recording bytes are preserved. The continuously corrected receiver provides the reference circle and rotation angle; the other two receivers are the outage candidates.

NMEA checksums and fields are validated. GGA UTC epochs establish alignment; midnight rollovers are tracked. RMC dates, when present, must match the configured date. Receivers without dates are assumed to belong to that day. No positional time-shift fitting is performed.

## Circle and errors

Positions are converted to local WGS84 east/north coordinates. A robust geometric Huber fit estimates the reference circle from RTK-fixed positions (GGA quality 4). Reference positions with radial residuals above `max(0.02 m, 6 × robust sigma)` are excluded from angle estimation.

Angles are unwrapped inside continuous reference segments. Expected positions are interpolated only inside segments, with the configured maximum reference gap (default 3 seconds). There is no extrapolation across missing reference data. Full-turn counts across gaps remain unknown.

Horizontal error is the distance between a measured position and the time-aligned expected circle position. Complete rotation durations are equally weighted; incomplete turns and turns spanning reference gaps are excluded. Statistical fields retain their existing machine-readable names and unit suffixes.

## Correction age and HRMS

`dAge` is reported GGA correction age in seconds, not an independently logged outage duration. The scatter plot includes every usable fixed epoch with finite, nonnegative age. HRMS bins use `(0,10]`, `(10,20]`, etc.; age zero belongs to the first bin. Each point uses the mean observed age and `sqrt(mean(east_error² + north_error²))`, expressed in millimetres.

An unweighted least-squares line with a free intercept is fitted across bin HRMS values. Slopes are in mm/s; lines stop at observed mean ages. These are empirical trends, not physical limits. The paired outage comparison separately requires identical UTC epochs, both receivers fixed, and both correction ages above 10 seconds.

## Limits and historical comparisons

The reference receiver's tangential error is not independently observable; shared systematic errors may remain hidden. Statistics describe retained fixed solutions, not full outage availability or absolute accuracy.

Historical curves are reconstructed from Figure 1 of `references/historical-outage-results/original.pdf`. The approximately 20 mm point near 300 seconds uses final precise clock/orbit products. Different test conditions limit direct rankings. Dataset-specific interpretations belong in `documentation/assessments/`, not shared numerical code.
