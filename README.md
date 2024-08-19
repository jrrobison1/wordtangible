# WordTangible
[![PyPI - Version](https://img.shields.io/pypi/v/wordtangible?link=https%3A%2F%2Fpypi.org%2Fproject%2Fwordtangible%2F)](https://pypi.org/project/wordtangible/) 

WordTangible is a simple Python library for analyzing the concreteness and imageability of words and text. This can be useful for various natural language processing tasks, readability analysis, and linguistic research.

Data is pulled from:
- The Brysbaert dataset (Brysbaert et al., 2014)[1]
- The Glasgow dataset (Scott et al., 2019)[2]
- The MRC Psycholinguistic Database (Coltheart 1981)[3]

The concreteness ratings from these datasets were averaged and normalized to a 1-5 scale, where 5 represents the highest level of concreteness.

## Features

- Get concreteness ratings for individual words
- Calculate average concreteness for a given text
- Compute the ratio of concrete to abstract words in a text

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
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References
[1] Brysbaert, M., Warriner, A. B., & Kuperman, V. (2014). Concreteness ratings for 40 thousand generally known English word lemmas. Behavior research methods, 46, 904-911.

[2] Scott, G. G., Keitel, A., Becirspahic, M., Yao, B., & Sereno, S. C. (2019). The Glasgow Norms: Ratings of 5,500 words on nine scales. Behavior research methods, 51, 1258-1270.

[3] Coltheart, M. (1981). The MRC psycholinguistic database. The Quarterly Journal of Experimental Psychology Section A, 33(4), 497-505.