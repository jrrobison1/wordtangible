import csv
from pathlib import Path
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from importlib import resources

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)


def _load_concreteness_ratings() -> dict[str, float]:
    concreteness_dict = {}

    # Use importlib.resources to access the CSV file
    with resources.open_text(
        "wordtangible.resources", "concreteness_ratings.csv"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            concreteness_dict[row["Word"]] = float(row["Concreteness"])

    return concreteness_dict


CONCRETENESS_RATINGS = _load_concreteness_ratings()


def word_concreteness(word: str) -> float | None:
    """
    Get the concreteness rating for a given word.

    The concreteness ratings are derived from three sources:
    1. MRC Psycholinguistic Database
    2. Brysbaert et al. concreteness ratings
    3. Glasgow concreteness ratings

    All ratings were normalized to a 1-5 scale, where:
    - 1 represents highly abstract words
    - 5 represents highly concrete words

    If a word was rated in only one list, that list's rating was used.
    If a word was rated in multiple lists, the average of those ratings was used.

    Args:
        word (str): The word to look up.

    Returns:
        float | None: The concreteness rating of the word if available, None otherwise.
    """
    return CONCRETENESS_RATINGS.get(word, None)


def avg_text_concreteness(
    text: str, include_stopwords: bool = False, only_rated_words: bool = True
) -> float:
    """
    Calculate the average concreteness rating for a given text.

    This function tokenizes the input text, retrieves concreteness ratings for each token,
    and calculates the average concreteness score.

    Args:
        text (str): The input text to analyze.
        include_stopwords (bool, optional): Whether to include stopwords in the analysis.
            Defaults to False.
        only_rated_words (bool, optional): Whether to only consider words with known
            concreteness ratings in the average calculation. Defaults to True.

    Returns:
        float: The average concreteness rating of the text. Returns 0.0 if no words
        are found or if no words have concreteness ratings.

    Note:
        - Concreteness ratings range from 1 (highly abstract) to 5 (highly concrete).
        - If only_rated_words is True, words without concreteness ratings are excluded
          from both the numerator and denominator of the average calculation.
        - If only_rated_words is False, all words are included in the denominator,
          but only rated words contribute to the numerator.
    """
    tokens = _get_tokens(text, include_stopwords)

    if len(tokens) == 0:
        return 0.0

    concreteness_ratings = [
        concreteness
        for token in tokens
        if (concreteness := word_concreteness(token)) is not None
    ]
    num_tokens = len(concreteness_ratings if only_rated_words else tokens)
    total_concreteness = sum(concreteness_ratings)

    return (total_concreteness / num_tokens) if num_tokens > 0 else 0.0


def concrete_abstract_ratio(
    text: str,
    include_stopwords: bool = False,
    very_concrete_threshold: float = 4.0,
    very_abstract_threshold: float = 2.0,
) -> float:
    """
    Calculate the ratio of very concrete words to very abstract words in a given text.

    This function tokenizes the input text, determines the concreteness of each word,
    and calculates the ratio of words that are considered very concrete to those
    considered very abstract based on the provided thresholds.

    Args:
        text (str): The input text to analyze.
        include_stopwords (bool, optional): Whether to include stopwords in the analysis.
            Defaults to False.
        very_concrete_threshold (float, optional): The concreteness rating threshold
            for a word to be considered very concrete. Defaults to 4.0.
        very_abstract_threshold (float, optional): The concreteness rating threshold
            for a word to be considered very abstract. Defaults to 2.0.

    Returns:
        float: The ratio of very concrete words to very abstract words.
            Returns float('inf') if there are concrete words but no abstract words.
            Returns 0.0 if there are no concrete words or if the text is empty.

    Note:
        - Concreteness ratings range from 1 (highly abstract) to 5 (highly concrete).
        - Words with concreteness ratings between the two thresholds are not counted
          in either category.
        - Words without known concreteness ratings are ignored.
    """
    tokens = _get_tokens(text, include_stopwords)

    concrete_words = 0
    abstract_words = 0

    for token in tokens:
        concreteness = word_concreteness(token)
        if concreteness is not None:
            if concreteness >= very_concrete_threshold:
                concrete_words += 1
            elif concreteness <= very_abstract_threshold:
                abstract_words += 1

    if abstract_words == 0:
        return float("inf") if concrete_words > 0 else 0.0

    return concrete_words / abstract_words


def _get_tokens(text: str, include_stopwords: bool = False):
    tokens = [token for token in word_tokenize(text.lower()) if token.isalpha()]

    if not include_stopwords:
        stop_words = set(stopwords.words("english"))
        tokens = [token for token in tokens if token not in stop_words]

    return tokens
