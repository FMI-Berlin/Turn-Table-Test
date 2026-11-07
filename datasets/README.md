# Datasets

Use one directory per recording session: `<date>` or `<date>_run-<number>`. Keep original inputs in `raw/` and describe the session in `dataset.json`. See `dataset.example.json` and the root README for the workflow.

The current analysis expects three receivers: one continuously corrected reference and two outage receivers. Receiver names become CSV filename stems and must contain only letters, digits, underscores or hyphens. Input paths and optional assessment paths are relative to the configuration file. Colors may be `red`, `green` or `blue`.

`id` determines the output directory under `results/`; `date` must match available RMC dates. Record unknown firmware versions as `null`. The optional `assessment` defaults to `null`, preventing a new recording from inheriting the original dataset's conclusions.
