# nashionalinvestments.com

Static site generator for Nashional Investments.

- `src/build.py` builds every page from Python templates.
- `src/glossary.py` holds the glossary terms.
- `src/assets/` holds CSS, JS, images and the favicon.

Build modes:

- `python3 src/build.py preview` relative links, review flags visible, noindex
- `python3 src/build.py staging` clean links, noindex (used until launch)
- `python3 src/build.py prod` clean links, indexable, sitemap and AI crawler rules

Hosting: GitHub Pages via `.github/workflows/pages.yml`.

Launch gate: GitHub Pages stays off until the Form ADV amendment is filed. At launch, change `SITE_MODE` and the artifact path in the workflow to `prod`, add the custom domain, then enable Pages (Settings > Pages > Source: GitHub Actions).
