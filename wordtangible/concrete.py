import csv
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from importlib import resources

_nltk_ready = False


def _ensure_nltk_data() -> None:
    """Make sure the NLTK resources tokenization needs are available.

    Runs lazily on first use (not at import time, which breaks offline
    environments) and only downloads what is actually missing. Note that
    NLTK >= 3.8.2 tokenizes with the `punkt_tab` resource — downloading
    only `punkt` leaves word_tokenize raising LookupError on fresh
    installs.
    """
    global _nltk_ready
    if _nltk_ready:
        return
    for resource, path in (
        ("punkt_tab", "tokenizers/punkt_tab"),
        ("punkt", "tokenizers/punkt"),
        ("stopwords", "corpora/stopwords"),
    ):
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(resource, quiet=True)
    _nltk_ready = True


def _load_concreteness_ratings() -> dict[str, float]:
    concreteness_dict = {}

    ref = resources.files("wordtangible.resources") / "concreteness_ratings.csv"
    with ref.open("r", encoding="utf-8") as csvfile:
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
    smoothing: float = 0.0,
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
        smoothing (float, optional): Additive (add-k) smoothing constant applied to
            both counts: (concrete + k) / (abstract + k). The default of 0.0 keeps
            the exact historical behavior. A small positive value (k=1 is typical)
            keeps the ratio finite when a text has no very-abstract words and damps
            small-sample jumpiness, which makes the ratio safe to average, plot,
            or correlate downstream. Defaults to 0.0.

    Returns:
        float: The ratio of very concrete words to very abstract words.
            With smoothing == 0 (the default):
            Returns float('inf') if there are concrete words but no abstract words.
            Returns 0.0 if there are no concrete words or if the text is empty.
            With smoothing > 0 the result is always finite; a text with no rated
            words in either category returns 1.0 (neutral).

    Raises:
        ValueError: If smoothing is negative.

    Note:
        - Concreteness ratings range from 1 (highly abstract) to 5 (highly concrete).
        - Words with concreteness ratings between the two thresholds are not counted
          in either category.
        - Words without known concreteness ratings are ignored.
    """
    if smoothing < 0:
        raise ValueError("smoothing must be >= 0")
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

    if smoothing > 0:
        return (concrete_words + smoothing) / (abstract_words + smoothing)

    if abstract_words == 0:
        return float("inf") if concrete_words > 0 else 0.0

    return concrete_words / abstract_words


def concreteness_coverage(text: str, include_stopwords: bool = False) -> float:
    """
    Calculate the fraction of tokens that have a known concreteness rating.

    avg_text_concreteness averages over only the words found in the ratings
    lexicon; this function reports how much of the text that actually was.
    A mean computed at 0.85 coverage rests on most of the text, while the
    same mean at 0.12 coverage (dialect, jargon, names, other languages)
    rests on a handful of incidental matches — reporting or thresholding
    on coverage tells you how much to trust the mean.

    Args:
        text (str): The input text to analyze.
        include_stopwords (bool, optional): Whether to include stopwords in the
            token count, matching the tokenization used by the other functions.
            Defaults to False.

    Returns:
        float: rated_tokens / total_tokens, in [0.0, 1.0]. Returns 0.0 for an
        empty text (or one with no alphabetic tokens).
    """
    tokens = _get_tokens(text, include_stopwords)
    if not tokens:
        return 0.0
    rated = sum(1 for token in tokens if word_concreteness(token) is not None)
    return rated / len(tokens)


def _get_tokens(text: str, include_stopwords: bool = False):
    _ensure_nltk_data()
    tokens = [token for token in word_tokenize(text.lower()) if token.isalpha()]

    if not include_stopwords:
        stop_words = set(stopwords.words("english"))
        tokens = [token for token in tokens if token not in stop_words]

    return tokens
