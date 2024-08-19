# WordTangible

WordTangible is a Python library for analyzing the concreteness and imageability of words and text. It provides tools to measure how abstract or concrete the language in a given text is, which can be useful for various natural language processing tasks, readability analysis, and linguistic research.

## Features

- Get concreteness ratings for individual words
- Calculate average concreteness for a given text
- Compute the ratio of concrete to abstract words in a text
- Customizable thresholds for concrete and abstract word classification
- Option to include or exclude stopwords in analysis

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
print(avg_text_concreteness(text))  # Output: ~3.5 (mix of concrete and abstract)

# Get the ratio of concrete to abstract words
print(concrete_abstract_ratio(text))  # Output: ~1.0 (balanced concrete and abstract words)
```

For more detailed usage instructions and API documentation, please refer to our [documentation](link-to-your-docs).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The concreteness ratings are derived from multiple sources, including the MRC Psycholinguistic Database, Brysbaert et al. concreteness ratings, and Glasgow concreteness ratings.
- This project uses NLTK for tokenization and stopword filtering.

## Citation

If you use WordTangible in your research, please cite it as follows:

```
Robison, J. (2024). WordTangible: A Python library for word concreteness and imageability analysis. [Software]. Available from https://github.com/jrrobison1/wordtangible
```
