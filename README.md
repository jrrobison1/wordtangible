# WordTangible
[![PyPI - Version](https://img.shields.io/pypi/v/wordtangible?link=https%3A%2F%2Fpypi.org%2Fproject%2Fwordtangible%2F)](https://pypi.org/project/wordtangible/) [![DOI](https://zenodo.org/badge/844322355.svg)](https://doi.org/10.5281/zenodo.22635419)

WordTangible is a simple Python library for analyzing the concreteness and imageability of words and text. This can be useful for various natural language processing tasks, readability analysis, and linguistic research.

Data is pulled from:
- The Brysbaert dataset (Brysbaert et al., 2014)[1]
- The Muraki multiword-expression dataset (Muraki et al., 2023)[2]
- The Glasgow dataset (Scott et al., 2019)[3]
- The MRC Psycholinguistic Database (Coltheart, 1981; machine-usable
  dictionary: Wilson, 1988)[4][5]

The default rating is a quality-ordered fallback on a 1-5 scale (5 = most
concrete): Brysbaert's raw value when a word is in Brysbaert (the largest
single-word source, natively 1-5), otherwise Muraki (multiword
expressions, same scale and lab lineage), otherwise Glasgow, otherwise
MRC, the latter two linearly rescaled to 1-5. The sources are deliberately *not*
averaged — their normalized distributions have systematically different
means, so a linear-rescale average would skew multi-source words rather
than reduce noise. This way every value is a real published rating from a
single identifiable study (and ~99% of words return Brysbaert's exact
published value). The raw per-source ratings, an MRC-free variant, and a
mean of the available sources are all accessible via the `source`
parameter (see below).

## Features

- Get concreteness ratings for individual words
- Choose the ratings source: the default fallback, any single dataset
  un-normalized (`brysbaert`, `muraki`, `glasgow`, `mrc`), an MRC-free
  variant (`open`) for commercial use, or a normalized `mean`
- Rated multiword expressions match as units, longest first: "baseball
  bat" and "piece of cake" get their own ratings (2,896 Brysbaert
  compounds + 62,889 Muraki expressions, idioms included) instead of
  blending their constituent words; disable with
  `match_expressions=False` if idiom ratings firing on literal uses
  ("he ate a piece of cake") is a concern
- Unrated inflected forms score as their WordNet lemma ("whales" as
  "whale", "replied" as "reply") — worth ~10 points of token coverage on
  typical fiction; disable with `lemma_fallback=False` for values
  strictly comparable to the published norms
- Calculate average concreteness for a given text
- Compute the ratio of concrete to abstract words in a text (with optional
  add-k smoothing to keep it finite and stable on short texts)
- Report rating coverage — how much of a text the concreteness mean
  actually rests on

## Installation

You can install WordTangible using pip:

```bash
pip install wordtangible
```

## Usage

Here are some basic examples of how to use WordTangible:

```python
from wordtangible import word_concreteness, avg_text_concreteness, concrete_abstract_ratio

# Get concreteness rating for a single word
print(word_concreteness("apple"))  # Output: 5.0 (highly concrete)

# Calculate average concreteness of a text
text = "The abstract concept of love is as tangible as the apple in your hand."
print(avg_text_concreteness(text))  # Output: ~2.9 (mix of concrete and abstract)

# Get the ratio of concrete to abstract words
print(concrete_abstract_ratio(text))  # Output: ~1.0 (balanced concrete and abstract words)

# Smoothed ratio: finite even when a text has no very-abstract words,
# and steadier on short texts (add-k smoothing; default k=0 keeps the
# classic behavior, including float('inf') for the no-abstract case)
print(concrete_abstract_ratio(text, smoothing=1))

# How much of the text the concreteness mean rests on (0.0-1.0):
# a mean at 0.85 coverage is trustworthy; the same mean at 0.12
# (jargon, dialect, names) is noise
from wordtangible import concreteness_coverage
print(concreteness_coverage(text))
```

### Choosing a ratings source

Every function accepts a `source` parameter:

```python
word_concreteness("apple")               # 5.0   — default fallback, 1-5 scale
word_concreteness("apple", "brysbaert")  # 5.0   — raw Brysbaert, 1-5 scale
word_concreteness("apple", "glasgow")    # 6.824 — raw Glasgow CNC, 1-7 scale
word_concreteness("apple", "mrc")        # 620   — raw MRC CNC, 100-700 scale
word_concreteness("apple", "open")       # 5.0   — like default, but never MRC
word_concreteness("apple", "mean")       # 4.78  — mean of available sources, rescaled to 1-5
word_concreteness("piece of cake")       # 2.8   — Muraki multiword expressions, idioms included

avg_text_concreteness(text, source="open")
```

- `default` — Brysbaert, else Muraki, else Glasgow, else MRC (the
  latter two rescaled to 1-5).
- `brysbaert` / `muraki` / `glasgow` / `mrc` — one dataset's raw, un-normalized
  values on its native scale; `None` for words it doesn't rate. Useful
  for comparing directly against the published norms. If you pass these
  to `concrete_abstract_ratio`, adjust its thresholds to the source's
  scale.
- `open` — Brysbaert, else Muraki, else Glasgow: excludes the MRC database, whose
  terms are "for research purposes" (see licensing below), making this
  the right choice for commercial products.
- `mean` — the mean of whichever of the four rate the word, each
  linearly rescaled to 1-5. Beware: linear rescaling doesn't fully align
  the scales (the sources' normalized means differ systematically), so
  these values aren't comparable to any single set of published norms.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

The WordTangible **code** is licensed under the MIT License - see the
[LICENSE](LICENSE) file for details.

### Data sources & licensing

The bundled ratings file (`wordtangible/resources/concreteness_ratings.csv`)
is derived from third-party datasets, and the MIT license above does **not**
apply to that data. Each source has its own terms:

- **Glasgow Norms** (Scott et al., 2019): published open access under a
  [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
  license — redistribution of derived data is permitted with attribution,
  which the citation below provides.
- **Brysbaert concreteness norms** (Brysbaert et al., 2014): made freely
  available by the authors (via the *Behavior Research Methods* supplement
  and the Ghent CRR lab) and widely redistributed in research software;
  no formal license accompanies the data, so provenance and citation are
  provided here as is standard practice.
- **Muraki multiword-expression norms** (Muraki et al., 2023): distributed
  by the authors via the paper's OSF repository (osf.io/ksypa), same
  research-community terms as the Brysbaert norms.
- **MRC Psycholinguistic Database** (Coltheart, 1981; Wilson, 1988): the
  database's distribution terms state that it is available **for research
  purposes**. The default ratings fall back to MRC-derived values for the
  few hundred words none of the other sources rate. If you intend to
  use WordTangible in a commercial (non-research) product, pass
  `source="open"` — it draws only on Brysbaert, Muraki, and Glasgow —
  or verify the MRC terms for your use case.

The bundled CSV keeps each source's raw rating in its own column, and
`scripts/build_ratings.py` regenerates it from the original datasets
(downloaded on demand; the raw files are not stored in this repository).

The lemma fallback additionally uses **WordNet** (Miller, 1995), which is
not bundled either: NLTK downloads it on first use, under the permissive
[Princeton WordNet license](https://wordnet.princeton.edu/license-and-commercial-use).

This section documents provenance in good faith and is not legal advice.

## Citing WordTangible

If you use WordTangible in research, please cite both the tool and the
rating datasets your results rest on (all four under the default
source; Brysbaert, Muraki, and Glasgow if you use `source="open"`; the
single dataset if you use a raw source). GitHub's "Cite this repository"
button generates a citation from [CITATION.cff](CITATION.cff), or use:

> Robison, J. (2026). *WordTangible* (Version 0.6.0) [Computer software].
> https://github.com/jrrobison1/wordtangible

```bibtex
@software{robison_wordtangible,
  author  = {Robison, Jason},
  title   = {WordTangible},
  version = {0.6.0},
  year    = {2026},
  url     = {https://github.com/jrrobison1/wordtangible}
}
```

If your analysis uses the default lemma fallback (`lemma_fallback=True`),
consider also citing WordNet[6], which provides the lemmatization.

Dataset citations are given in full in the [References](#references)
below.

## References
[1] Brysbaert, M., Warriner, A. B., & Kuperman, V. (2014). Concreteness ratings for 40 thousand generally known English word lemmas. *Behavior Research Methods, 46*(3), 904-911. https://doi.org/10.3758/s13428-013-0403-5

[2] Muraki, E. J., Abdalla, S., Brysbaert, M., & Pexman, P. M. (2023). Concreteness ratings for 62,000 English multiword expressions. *Behavior Research Methods, 55*(5), 2522-2531. https://doi.org/10.3758/s13428-022-01912-6

[3] Scott, G. G., Keitel, A., Becirspahic, M., Yao, B., & Sereno, S. C. (2019). The Glasgow Norms: Ratings of 5,500 words on nine scales. *Behavior Research Methods, 51*(3), 1258-1270. https://doi.org/10.3758/s13428-018-1099-3

[4] Coltheart, M. (1981). The MRC psycholinguistic database. *The Quarterly Journal of Experimental Psychology Section A, 33*(4), 497-505. https://doi.org/10.1080/14640748108400805

[5] Wilson, M. (1988). MRC Psycholinguistic Database: Machine-usable dictionary, version 2.00. *Behavior Research Methods, Instruments, & Computers, 20*(1), 6-10. https://doi.org/10.3758/BF03202594

[6] Miller, G. A. (1995). WordNet: A lexical database for English. *Communications of the ACM, 38*(11), 39-41. https://doi.org/10.1145/219717.219748