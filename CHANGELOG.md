# Changelog

## 0.6.0

- **New data source: Muraki et al. (2023) multiword expressions.**
  Concreteness ratings for 62,889 expressions — noun compounds through
  long idioms — from the same lab lineage, scale (1-5), and method as
  the Brysbaert norms (though with ~10 raters per expression vs ~30).
  A new `Muraki` CSV column and `source="muraki"` raw option; the
  default and `open` fallbacks become Brysbaert → Muraki → Glasgow
  (→ MRC for default), and `mean` includes it. Where both rate the same
  expression (2,854 of our 2,896 Brysbaert compounds, r = 0.86),
  Brysbaert's value wins — continuity, and 3x the raters.
- **Expression matching generalizes from bigrams to n-grams.** Runs of
  adjacent tokens matching a rated expression are scored as one unit,
  longest match first ("ice cream cone" beats "ice cream"; "a piece of
  cake" beats "piece of cake"). The 0.4.0 rules carry over: matching
  happens before punctuation/stopword filtering, punctuation blocks a
  match, and a source that doesn't rate the expression falls back to
  word-by-word.
- **All-stopword expressions respect the stopword filter.** Muraki rates
  function-word combinations ("of a", "that is", "the same") that, if
  matched as units, would survive the default stopword removal even
  though word-by-word scoring would have dropped every constituent —
  measured on six reference texts, this injected thousands of abstract
  junk units per book and dragged every average down. The stopword rule
  now applies uniformly: a unit is dropped when all of its words are
  stopwords, so "of a" goes while "act on", "at last", and "piece of
  cake" stay; `include_stopwords=True` keeps everything, as before.
- **New: `match_expressions` parameter on the text functions.** Idioms
  are rated for their figurative meaning ("piece of cake" = 2.8), which
  is wrong when the text means literal cake; exact-match-only limits
  this (inflected literal uses don't trigger), but
  `match_expressions=False` turns expression matching off entirely for
  strict word-by-word scoring.
- Muraki's ~1,100 hyphenated single-word entries ("able-bodied") are
  included and reachable via direct `word_concreteness` lookup, though
  not through text tokenization (hyphenated tokens fail the alphabetic
  filter, as before). Its ~4,700 entries with digits or punctuation
  (".22 caliber", "3D printer") are likewise lookup-only. 3,543
  unrated (NA) rows in the source file are dropped.
- The ratings CSV grows to 100,445 rows (~2.7MB); import time rises from
  ~0.23s to ~0.38s. No existing word's default value changed.

## 0.5.0

- **Lemma fallback, on by default.** A word with no rating of its own is
  now scored by its WordNet lemma (tried as noun, verb, adjective, then
  adverb): "whales" scores as "whale", "replied" as "reply", "began" as
  "begin". Measured on full novels, token coverage rises from ~78-81% to
  ~91% — over half of all previously unrated tokens — and what remains
  unrated is almost entirely proper names. The fallback is consulted
  only on an exact miss, which acts as a guardrail: sense-drifting
  plurals ("goods", "arms", "customs", "glasses") are rated directly in
  Brysbaert and always keep their own rating. Pass
  `lemma_fallback=False` (available on every function) for values
  strictly comparable to the published norms. WordNet is downloaded
  lazily via NLTK on the first fallback lookup; lookups are cached.
  Scores and coverage shift wherever a lemma now matches — that's the
  feature.

## 0.4.0

- **Rated two-word compounds now match in text analysis.** The Brysbaert
  norms deliberately rated 2,896 two-word expressions ("baseball bat",
  "big toe", "act on"), but tokenization only ever looked up single
  words, so those entries could never match. Adjacent words forming a
  rated compound are now scored as one unit with the compound's own
  rating, greedily left to right. Punctuation between the words blocks a
  match ("...the baseball, bat in hand..." stays two words), compounds
  containing a stopword ("act on") survive stopword removal, and a
  matched compound counts as a single token for coverage and averaging.
  A compound only matches when the chosen `source` rates it, so raw
  `"glasgow"`/`"mrc"` lookups keep plain word-by-word behavior. Scores
  shift slightly wherever a compound now matches — that's the feature.
  (The 18 hyphenated compounds, e.g. "first-aid kit", remain out of
  reach: hyphenated tokens are dropped by the alphabetic-token filter.)

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
