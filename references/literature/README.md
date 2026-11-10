# Literature and evidence provenance

The report cites the primary sources listed in `catalog.json`. Research papers support the mechanisms and show that outage bridging is established work. Manufacturer documents establish advertised functions, not independently measured accuracy or the enabled firmware options in this experiment.

R1 is the historical Trimble GPS-only report, now stored as `references/historical-outage-results/trimble-report.docx` and `trimble-report.pdf`. The project-owner revision of 10 November 2026 explicitly identifies **18 July 2005**, **Trimble**, **GPS-only**, and **U. Vollath and S. Klose** in its header. The DOCX body paragraphs are unchanged; formatting and PDF pagination changed from four pages to three. Figure 1 remains on page 2 and Figure 2 is on page 3. The 2026 PDF export date is not the measurement date. Paths, revision context and SHA-256 hashes are recorded under R1 in `catalog.json`.

Important comparison limits:

- R2 studies asynchronous broadcast errors at short delays. Its 15-second statistics must not be extrapolated into a 300-second positioning guarantee.
- R3 establishes multi-constellation outage research in 2013. Its abstract does not substantiate our exact 22–33 mm at 300 seconds.
- R4 reports longer bridging using precise/final or ultra-rapid products. Its component standard deviations are not horizontal RMS values; it is not a broadcast-only replication.
- R5 and R6 describe RTK HOLD/KEEP. Advertised durations are not a universal accuracy specification and do not identify the settings used here.
- R9 requires an additional correction service during a local RTK link outage. It illustrates a different architecture, not correction-free performance.

No independently verified, method-matched comparison of FMI P23A/M, UM980 and LG290P was identified in this search. No novelty or market-leading claim is made. The earlier discussion is now represented by R10, an AI-generated implementation note dated 18 October 2026. Page 11 discusses 0.36 m over 120 s; it does not supply an attributed FMI raw-data HRMS benchmark or firmware versions. Only the two local November datasets can be recomputed here.

## October 18 implementation note (R10)

The supplied PDF has 14 pages. Pages 3–8 discuss transmission times, complete clock changes, prediction and anchored delta-phase equivalence; page 11 discusses 0.36 m over 120 s (3 mm/s, 18 cm/min). This is a discussed position-change scale, not an HRMS series. Pages 12–13 reproduce earlier material, including the same historical clock plot as R1; they are not new FMI data.

The companion JPG is a conceptual workflow, not a measurement plot. Source checksums are recorded in `catalog.json`. A single position change divided by time must not be equated to a slope of binned HRMS, nor used to infer a firmware improvement factor. The note identifies checks to investigate, not proven fixes in the current receiver implementation.

## Rotation-rate and phase wind-up discussion (R11–R13)

Both dataset reports now include the rotation-rate and phase wind-up questions and answers in all three languages. R11 supplies the carrier-phase model and cycle continuity; R12 distinguishes common yaw from geometry-dependent roll/pitch; R13's publisher abstract supports the corresponding RTK distinction. The ION primary record establishes R12 as the 2011 conference paper despite the later bibliographic wrapper on the available author PDF. Full text was inspected for R12; only the indexed publisher abstract was inspected for R13. The sources were checked on 10 November 2026.

The numerical rates come from the local mean revolution periods. The L1 example is a range-equivalent phase term, not a position error or an HRMS/VRMS slope. Cancellation during outages is a conditional deduction from an unchanged double-difference model, not verification of FMI, Unicore or Quectel firmware. The shared antenna, unknown attitude and unavailable internal models limit interpretation.
