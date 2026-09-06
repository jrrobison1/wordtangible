# Changelog

## 0.2.0

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
