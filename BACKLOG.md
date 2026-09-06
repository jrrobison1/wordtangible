# Backlog

Ideas noted while integrating wordtangible into a stylometry tool (where
it now charts concreteness across rolling windows of novels):

- **Smoothed ratio option**: `concrete_abstract_ratio` returning
  `float('inf')` when a text has zero abstract words is documented, but
  awkward for downstream aggregation/plotting. A `smoothing` parameter
  (add-k on both counts) or a companion `log_concrete_abstract_ratio`
  would keep the ratio finite without breaking the current contract.
- **Lazy ratings load**: `CONCRETENESS_RATINGS` parses the CSV at import;
  loading on first lookup would make `import wordtangible` instant.
- **Vectorized text API**: `avg_text_concreteness(tokens: list[str])`
  overload (or a `tokenizer=None` hook) would let callers who already
  have tokens skip NLTK entirely — also removes the NLTK dependency for
  that path.
- **Coverage stat**: expose the fraction of tokens that had a rating
  (e.g. return an optional `(mean, coverage)`), useful for judging how
  trustworthy the mean is on unusual vocabulary.
- **imageable.py**: currently an empty stub — either implement
  imageability ratings (MRC has them) or drop the module until ready.
- **Publish 0.2.0 to PyPI** once reviewed.
