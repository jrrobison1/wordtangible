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
- **Per-source provenance in the ratings build**: add a source column (or
  regenerate with per-source values kept) so an MRC-free variant of the
  CSV can be produced for commercial-safe use — the MRC database's terms
  say "for research purposes", while Glasgow is CC BY 4.0 and Brysbaert
  is author-distributed without a formal license. Brysbaert alone covers
  ~40k lemmas, so an MRC-free build loses little coverage.
- **imageable.py**: currently an empty stub — either implement
  imageability ratings (MRC has them) or drop the module until ready.
- **Publish 0.2.0 to PyPI** once reviewed.
