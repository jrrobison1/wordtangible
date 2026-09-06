# Changelog

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
