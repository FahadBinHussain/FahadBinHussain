# FahadBinHussain - Profile README & Stack Generator

Agent notes for maintaining automated profile README metrics and tech stack detection.

## stack section automation (`generate_stack_section.py`)
- **detection mechanics:**
  - `FILE_HINTS`: matches repository file tree names/paths (e.g. `drizzle.config.ts`, `bun.lockb`, `components.json`).
  - `CONTENT_HINTS`: scans dependency files (`package.json`, `requirements.txt`, `pyproject.toml`, etc.) for library package names.
  - `BADGE_MAP`: renders Shields.io badge (`for-the-badge` style) using verified SimpleIcons logo slugs and hex colors.
  - `normalize_language_name`: cleans GitHub's raw linguist language names.
- **automated execution:**
  - `.github/workflows/wakatime-metrics.yml` runs hourly at `0 * * * *` on GitHub Actions Ubuntu runner.
  - commits and pushes changes back to `main`.

## testing & validation
```bash
uv run --directory . --with pytest --with requests --with python-dotenv pytest -o pythonpath=. tests
```
Ensure all SimpleIcons badge slugs resolve cleanly with HTTP 200 on `https://img.shields.io/badge/<label>-<bg>?style=for-the-badge&logo=<slug>`.
