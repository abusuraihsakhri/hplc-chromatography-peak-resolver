# HPLC Chromatography Peak Resolver

Chromatogram peak screening and approximate integration for time–signal HPLC data. The repository also retains earlier, generic threshold-based audit agents and two Python API/CLI implementations for backward compatibility.

## Browser application

Open `web/index.html` in a modern desktop or mobile browser. The static application is also configured for GitHub Pages deployment after the repository's Pages environment is enabled and a deployment succeeds.

- Load a CSV, TSV, or semicolon-delimited file with increasing **retention time (minutes)** and **detector response**. Column headers are optional.
- Adjust prominence threshold and optionally provide dead time, t₀.
- View a chromatogram and peak table; export peak parameters as CSV.
- Try **Load example** without uploading any data. A second sample is in `chromatogram_sample.csv`.

**Privacy:** Browser calculations and file processing are local. The page uses no external libraries, analytics, or API calls. GitHub Pages, when enabled, serves only the static files.

## Calculations and limitations

The browser (`web/peak-analysis.js`) and Python (`hplc_resolver/peaks.py`) use three-point smoothing, prominence-based peak detection, valley-based peak segmentation, local linear-baseline subtraction, and trapezoidal area estimation. Adjacent-peak resolution is approximated using `Rs = 1.18 × (tR₂ − tR₁)/(FWHM₁ + FWHM₂)`; retention factor is `k′ = (tR − t₀)/t₀` when dead time is given. Area percentages are fractions of **detected integrated area**, not assay purity.

**This is not peak deconvolution, Gaussian/EMG fitting, compound identification, spectral peak purity analysis, automated method validation, or certified pharmacopeial conformance testing.** Overlapping peaks, baseline drift, sampling resolution, and noise can significantly bias reported estimates. Confirm scientific decisions in qualified chromatography software.

The older `agents/`, `hplc_resolver/agents.py`, and `enrichment.py` modules remain available. Their numeric alerts are generic operational thresholds; their named enrichment modules are not implementations of the claimed domain-specific optimizers. They should not be interpreted as USP <621> or other standards-conformant assessments.

## Python installation and CLI

Python 3.10+:

```bash
python -m pip install -e ".[server,test]"
python cli.py peaks -i chromatogram_sample.csv -o peak_results.csv
python cli.py peaks -i chromatogram_sample.csv --prominence 0.05 --dead-time 1.0
python -m pytest -q
```

Both `python cli.py peaks` and the installed `hplc-chromatography-peak-resolver peaks` command analyze time–signal data. The `--output` argument writes peak metrics to a CSV; without it, results are printed as JSON. Paths are confined to the working directory.

Legacy threshold audit commands are preserved:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The legacy audit CLI and server require `AUDIT_SECRET_KEY` (at least 32 characters). Use an unpredictable, deployment-specific key; never commit it or distribute it with browser assets. A key change invalidates verification of any stored audit trail created with a previous key; the current audit ledger is process-memory-only.

## REST API

The primary server (`python cli.py serve`) exposes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Health and metadata |
| POST | `/api/peaks` | Compute peaks from `{"samples": [[time, signal], ...], "min_prominence": 0.06, "dead_time": null}` |
| POST | `/api/audit` | Legacy threshold-based assessment |
| POST | `/api/chat` | Deterministic mock response (no external language model) |
| GET | `/metrics` | Basic counters |
| GET | `/api/audit/logs` | Admin-restricted audit metadata |

To request audit logs, configure a separate `API_ADMIN_TOKEN` of at least 32 characters and supply it as an `X-Admin-Token` request header. If not configured, the audit-log endpoint is disabled. The API has no user identity management or rate limiting; restrict network exposure and do not send sensitive real patient identifiers.

The alternative `hplc_resolver.server.create_app()` also supports `/api/peaks` and retains its existing generic audit endpoints.

## Docker

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build
```

Compose binds the service to **127.0.0.1:8000** by default, not the public internet. Supply `API_ADMIN_TOKEN` separately to enable audit-log viewing. The image installs the declared server dependencies from `pyproject.toml`.

## Validation and development

```bash
python -m pip install -e ".[server,test]"
python -m pytest -q
python -m compileall -q agents hplc_resolver cli.py enrichment.py simulator.py
node --check web/peak-analysis.js
node --check web/app.js
node --test tests/peak-analysis.test.cjs
```

GitHub Actions runs Python tests on 3.10–3.12 and browser-algorithm tests on Node 22. The browser UI requires a modern browser with file upload, SVG, Blob downloads, and JavaScript enabled. No Python runtime is loaded in the static page; native JavaScript avoids large Pyodide downloads.

## License

MIT — see [LICENSE](LICENSE).
