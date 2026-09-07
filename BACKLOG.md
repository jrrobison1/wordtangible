# Backlog

Ideas noted while integrating wordtangible into a stylometry tool (where
it now charts concreteness across rolling windows of novels):

- **Log-ratio variant**: with `smoothing` now in place (0.2.0), a
  companion `log_concrete_abstract_ratio` would make "3x more concrete"
  and "3x more abstract" symmetric around zero — nice for charts.
- **Lazy ratings load**: `CONCRETENESS_RATINGS` parses the CSV at import;
  loading on first lookup would make `import wordtangible` instant.
- **Vectorized text API**: `avg_text_concreteness(tokens: list[str])`
  overload (or a `tokenizer=None` hook) would let callers who already
  have tokens skip NLTK entirely — also removes the NLTK dependency for
  that path.
- **imageable.py**: currently an empty stub — either implement
  imageability ratings (MRC has them) or drop the module until ready.
- **Publish 0.3.0 to PyPI** once reviewed. (Done in 0.3.0: per-source
  provenance in the ratings build, `source` parameter incl. the
  commercial-safe `"open"` variant.)
