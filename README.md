# WordTangible
[![PyPI - Version](https://img.shields.io/pypi/v/wordtangible?link=https%3A%2F%2Fpypi.org%2Fproject%2Fwordtangible%2F)](https://pypi.org/project/wordtangible/) 

WordTangible is a simple Python library for analyzing the concreteness and imageability of words and text. This can be useful for various natural language processing tasks, readability analysis, and linguistic research.

Data is pulled from:
- The Brysbaert dataset (Brysbaert et al., 2014)[1]
- The Glasgow dataset (Scott et al., 2019)[2]
- The MRC Psycholinguistic Database (Coltheart, 1981; machine-usable
  dictionary: Wilson, 1988)[3][4]

The concreteness ratings from these datasets were averaged and normalized to a 1-5 scale, where 5 represents the highest level of concreteness.

## Features

- Get concreteness ratings for individual words
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
- **MRC Psycholinguistic Database** (Coltheart, 1981; Wilson, 1988): the
  database's distribution terms state that it is available **for research
  purposes**. Because words rated in multiple lists are averaged, MRC-derived
  values are merged into the bundled ratings. If you intend to use
  WordTangible in a commercial (non-research) product, you should verify the
  MRC terms for your use case, or ask about an MRC-free build of the ratings.

This section documents provenance in good faith and is not legal advice.

## References
[1] Brysbaert, M., Warriner, A. B., & Kuperman, V. (2014). Concreteness ratings for 40 thousand generally known English word lemmas. *Behavior Research Methods, 46*(3), 904-911. https://doi.org/10.3758/s13428-013-0403-5

[2] Scott, G. G., Keitel, A., Becirspahic, M., Yao, B., & Sereno, S. C. (2019). The Glasgow Norms: Ratings of 5,500 words on nine scales. *Behavior Research Methods, 51*(3), 1258-1270. https://doi.org/10.3758/s13428-018-1099-3

[3] Coltheart, M. (1981). The MRC psycholinguistic database. *The Quarterly Journal of Experimental Psychology Section A, 33*(4), 497-505. https://doi.org/10.1080/14640748108400805

[4] Wilson, M. (1988). MRC Psycholinguistic Database: Machine-usable dictionary, version 2.00. *Behavior Research Methods, Instruments, & Computers, 20*(1), 6-10. https://doi.org/10.3758/BF03202594