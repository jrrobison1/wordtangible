# Changelog

## 0.3.0

- **New: `source` parameter on every function.** Choose which ratings to
  use: `"default"` (see below), a single dataset's raw un-normalized
  values on its native scale (`"brysbaert"` 1-5, `"glasgow"` 1-7,
  `"mrc"` 100-700), `"open"` (Brysbaert else Glasgow — excludes the
  research-purposes-only MRC database, suitable for commercial use), or
  `"mean"` (mean of the available sources rescaled to 1-5).
- **The Glasgow Norms are now actually used.** Reverse-engineering the
  original data file against its sources showed it was never the
  documented three-way average: it was Brysbaert's raw value with an
  MRC fallback, and the Glasgow data was never incorporated at all
  (an apparent bug in the original, lost build script). The default is
  now an intentional quality-ordered fallback — Brysbaert, else Glasgow,
  else MRC, rescaled to 1-5 — chosen over averaging because the sources'
  normalized distributions have systematically different means (3.04 /
  3.38 / 3.25), so a linear-rescale average skews multi-source words
  instead of reducing noise. Practical impact: 202 words gained ratings
  (Glasgow-only vocabulary — British spellings and some inflected
  forms — plus `ah`, which the old build dropped inexplicably), 26
  words switched from MRC-derived to Glasgow-derived values, and
  MRC-derived values are now rounded to two decimals instead of one.
  Brysbaert-backed values — over 99% of lookups — are unchanged.
- **New: `scripts/build_ratings.py`.** The ratings CSV is now
  reproducible: the script downloads the three source datasets, merges
  them, and writes the resource file, which also gained per-source raw
  columns (`Brysbaert`, `Glasgow`, `MRC`) alongside the default
  `Concreteness` column. Raw downloads are cached in `data/raw/` and not
  committed (the MRC database is "for research purposes").
- Validated the Glasgow CNC ratings before adopting them: they correlate
  with Brysbaert at r = 0.93 over 4,455 shared words — as strongly as
  Brysbaert and MRC agree with each other — and the norms were validated
  by their authors against 18 other sets of psycholinguistic norms.

## 0.2.0

- **New: `smoothing` parameter on `concrete_abstract_ratio`.** Add-k
  smoothing — `(concrete + k) / (abstract + k)` — keeps the ratio finite
  when a text has no very-abstract words and damps small-sample swings,
  making the ratio safe to average, plot, or correlate. The default
  (`smoothing=0.0`) preserves the historical behavior exactly, including
  the documented `float('inf')` case.
- **New: `concreteness_coverage(text)`.** Returns the fraction of tokens
  that have a rating in the norms (0.0-1.0), so users can report or
  threshold on how much of a text the concreteness mean actually rests
  on — a mean at 0.85 coverage is trustworthy; the same mean at 0.12
  (dialect, jargon, names) is noise.
- **Fixed tokenization on modern NLTK.** `word_tokenize` in NLTK >= 3.8.2
  requires the `punkt_tab` resource; only `punkt` was being downloaded, so
  fresh installs raised `LookupError` on first use. All three needed
  resources (`punkt_tab`, `punkt`, `stopwords`) are now ensured.
- **No more network access at import time.** NLTK data is checked and
  (only if missing) downloaded lazily on first tokenization instead of at
  `import wordtangible`, which failed in offline environments and could
  emit NLTK's unwritable-directory warning before any function was called.
- Replaced the deprecated `importlib.resources.open_text` API with the
  `files()` API (removes the deprecation warning on Python 3.11+).
- Declared support for Python 3.11-3.13 in classifiers; added a CI test
  matrix (3.10-3.13).
- **Documentation: data sources & licensing.** The README now
  distinguishes the MIT-licensed code from the bundled ratings data and
  states each source's terms (Glasgow Norms: CC BY 4.0; Brysbaert norms:
  author-distributed, no formal license; MRC: "for research purposes" —
  commercial users should verify). Citations upgraded to full APA with
  DOIs, and Wilson (1988) added for the machine-usable MRC dictionary.
- Added `CITATION.cff` so studies can cite WordTangible (and its
  underlying datasets) directly from GitHub's cite button.
