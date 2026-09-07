import csv
import nltk
from functools import lru_cache
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from importlib import resources

_nltk_ready = False
_wordnet_ready = False


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


def _ensure_wordnet() -> None:
    """Make sure WordNet is available for the lemma fallback.

    Separate from _ensure_nltk_data so that plain word lookups with the
    fallback never pull in the tokenizer resources (and vice versa).
    """
    global _wordnet_ready
    if _wordnet_ready:
        return
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        nltk.download("wordnet", quiet=True)
    _wordnet_ready = True


def _load_concreteness_ratings() -> (
    tuple[dict[str, dict[str, float]], dict[tuple[str, str], str]]
):
    ratings: dict[str, dict[str, float]] = {
        "default": {},
        "brysbaert": {},
        "glasgow": {},
        "mrc": {},
    }
    # (token, token) -> the rated entry's key, e.g. ("baseball", "bat") ->
    # "baseball bat" and ("dutch", "oven") -> "Dutch oven". The Brysbaert
    # norms deliberately rated 2,896 two-word compounds; tokenization maps
    # adjacent token pairs back onto them (see _get_tokens).
    bigrams: dict[tuple[str, str], str] = {}

    ref = resources.files("wordtangible.resources") / "concreteness_ratings.csv"
    with ref.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            word = row["Word"]
            if row["Concreteness"]:
                ratings["default"][word] = float(row["Concreteness"])
            if row["Brysbaert"]:
                ratings["brysbaert"][word] = float(row["Brysbaert"])
            if row["Glasgow"]:
                ratings["glasgow"][word] = float(row["Glasgow"])
            if row["MRC"]:
                ratings["mrc"][word] = float(row["MRC"])
            parts = word.lower().split(" ")
            if len(parts) == 2:
                bigrams[(parts[0], parts[1])] = word

    return ratings, bigrams


_RATINGS, _BIGRAMS = _load_concreteness_ratings()
CONCRETENESS_RATINGS = _RATINGS["default"]

SOURCES = ("default", "brysbaert", "glasgow", "mrc", "open", "mean")


def _normalize_glasgow(conc: float) -> float:
    """Linearly rescale Glasgow's 1-7 CNC to the 1-5 scale."""
    return 1 + (conc - 1) * 4 / 6


def _normalize_mrc(conc: float) -> float:
    """Linearly rescale MRC's 100-700 CNC to the 1-5 scale."""
    return 1 + (conc - 100) * 4 / 600


def _validate_source(source: str) -> None:
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}, got {source!r}")


_lemmatizer = WordNetLemmatizer()


@lru_cache(maxsize=100_000)
def _lemma_rating(word: str, source: str) -> float | None:
    """Rating for the first WordNet lemma of `word` the source rates.

    Tried as noun, verb, adjective, then adverb. Only consulted when the
    surface form itself is unrated, which acts as a guardrail: plurals
    whose meaning drifts from their lemma ("goods", "arms", "customs")
    are rated directly in Brysbaert, so they never reach this fallback.
    """
    _ensure_wordnet()
    for pos in ("n", "v", "a", "r"):
        lemma = _lemmatizer.lemmatize(word, pos)
        if lemma != word:
            rating = word_concreteness(lemma, source, lemma_fallback=False)
            if rating is not None:
                return rating
    return None


def word_concreteness(
    word: str, source: str = "default", lemma_fallback: bool = True
) -> float | None:
    """
    Get the concreteness rating for a given word.

    Ratings come from three published datasets: the Brysbaert et al. (2014)
    concreteness norms, the Glasgow Norms (Scott et al., 2019), and the MRC
    Psycholinguistic Database.

    Args:
        word (str): The word to look up.
        source (str, optional): Which rating to return. One of:

            - ``"default"``: quality-ordered fallback on a 1-5 scale —
              Brysbaert's raw value if the word is in Brysbaert (the
              largest, most recent source, natively 1-5), else Glasgow,
              else MRC, each linearly rescaled to 1-5. Every value is a
              real published rating from a single identifiable study;
              the sources are not averaged, because their normalized
              distributions have systematically different means and
              averaging would skew multi-source words.
            - ``"brysbaert"``: raw Brysbaert rating, 1-5 scale.
            - ``"glasgow"``: raw Glasgow CNC rating, 1-7 scale.
            - ``"mrc"``: raw MRC CNC rating, 100-700 scale.
            - ``"open"``: like ``"default"`` but never uses MRC (Brysbaert,
              else Glasgow rescaled to 1-5). The MRC database's terms are
              "for research purposes"; Brysbaert and Glasgow carry no such
              restriction, so this source suits commercial use.
            - ``"mean"``: mean of all available ratings rescaled to 1-5.
              Note the scale-mixing caveat above — values are not
              comparable to any single set of published norms.
        lemma_fallback (bool, optional): When the exact word is unrated,
            fall back to its WordNet lemma (tried as noun, verb,
            adjective, adverb) and return the first rated lemma's value —
            so "whales" gets the rating of "whale", "replied" of
            "reply". Only consulted on an exact miss: inflected forms
            rated directly (including sense-drifting plurals like
            "goods" or "arms") always use their own rating. Set False
            for values strictly comparable to the published norms.
            Defaults to True. The first fallback lookup downloads
            WordNet via NLTK if it is missing.

    Returns:
        float | None: The word's rating in the chosen source (on that
        source's scale), or None if the source does not rate the word.

    Raises:
        ValueError: If source is not one of the recognized names.

    Note:
        On the 1-5 scale, 1 represents highly abstract words and 5 highly
        concrete words. Glasgow's raw scale runs 1-7 and MRC's 100-700,
        with higher likewise meaning more concrete.
    """
    _validate_source(source)
    if source in ("default", "brysbaert", "glasgow", "mrc"):
        rating = _RATINGS[source].get(word, None)
    elif source == "open":
        brysbaert = _RATINGS["brysbaert"].get(word)
        glasgow = _RATINGS["glasgow"].get(word)
        if brysbaert is not None:
            rating = brysbaert
        else:
            rating = (
                None if glasgow is None else round(_normalize_glasgow(glasgow), 2)
            )
    else:  # source == "mean"
        brysbaert = _RATINGS["brysbaert"].get(word)
        glasgow = _RATINGS["glasgow"].get(word)
        mrc = _RATINGS["mrc"].get(word)
        values = [
            value
            for value in (
                brysbaert,
                None if glasgow is None else _normalize_glasgow(glasgow),
                None if mrc is None else _normalize_mrc(mrc),
            )
            if value is not None
        ]
        rating = round(sum(values) / len(values), 2) if values else None

    if rating is None and lemma_fallback:
        rating = _lemma_rating(word, source)
    return rating


def avg_text_concreteness(
    text: str,
    include_stopwords: bool = False,
    only_rated_words: bool = True,
    source: str = "default",
    lemma_fallback: bool = True,
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
        source (str, optional): Which ratings to use — see word_concreteness.
            Defaults to "default". Note that the result is on the chosen
            source's scale: 1-5 for "default"/"brysbaert"/"open"/"mean",
            1-7 for "glasgow", 100-700 for "mrc".
        lemma_fallback (bool, optional): Score unrated words by their
            WordNet lemma when one is rated ("whales" scores as "whale") —
            see word_concreteness. Defaults to True.

    Returns:
        float: The average concreteness rating of the text. Returns 0.0 if no words
        are found or if no words have concreteness ratings.

    Raises:
        ValueError: If source is not one of the recognized names.

    Note:
        - On the default 1-5 scale, ratings range from 1 (highly abstract)
          to 5 (highly concrete).
        - Adjacent words forming a rated two-word compound ("baseball bat")
          are scored as one unit using the compound's own rating.
        - If only_rated_words is True, words without concreteness ratings are excluded
          from both the numerator and denominator of the average calculation.
        - If only_rated_words is False, all words are included in the denominator,
          but only rated words contribute to the numerator.
    """
    _validate_source(source)
    tokens = _get_tokens(text, include_stopwords, source)

    if len(tokens) == 0:
        return 0.0

    concreteness_ratings = [
        rating
        for token in tokens
        if (rating := word_concreteness(token, source, lemma_fallback)) is not None
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
    source: str = "default",
    lemma_fallback: bool = True,
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
        source (str, optional): Which ratings to use — see word_concreteness.
            Defaults to "default". The thresholds are compared on the chosen
            source's scale, and the defaults (4.0 / 2.0) assume the 1-5 scale;
            pass adjusted thresholds for "glasgow" (1-7) or "mrc" (100-700).
        lemma_fallback (bool, optional): Score unrated words by their
            WordNet lemma when one is rated ("whales" scores as "whale") —
            see word_concreteness. Defaults to True.

    Returns:
        float: The ratio of very concrete words to very abstract words.
            With smoothing == 0 (the default):
            Returns float('inf') if there are concrete words but no abstract words.
            Returns 0.0 if there are no concrete words or if the text is empty.
            With smoothing > 0 the result is always finite; a text with no rated
            words in either category returns 1.0 (neutral).

    Raises:
        ValueError: If smoothing is negative, or source is not one of the
            recognized names.

    Note:
        - On the default 1-5 scale, ratings range from 1 (highly abstract)
          to 5 (highly concrete).
        - Words with concreteness ratings between the two thresholds are not counted
          in either category.
        - Words without known concreteness ratings are ignored.
    """
    if smoothing < 0:
        raise ValueError("smoothing must be >= 0")
    _validate_source(source)
    tokens = _get_tokens(text, include_stopwords, source)

    concrete_words = 0
    abstract_words = 0

    for token in tokens:
        concreteness = word_concreteness(token, source, lemma_fallback)
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


def concreteness_coverage(
    text: str,
    include_stopwords: bool = False,
    source: str = "default",
    lemma_fallback: bool = True,
) -> float:
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
        source (str, optional): Which ratings to use — see word_concreteness.
            Defaults to "default".
        lemma_fallback (bool, optional): Score unrated words by their
            WordNet lemma when one is rated ("whales" scores as "whale") —
            see word_concreteness. Defaults to True.
            A lemma-rescued word counts as rated, so coverage reflects
            the ratings the other functions actually use.

    Returns:
        float: rated_tokens / total_tokens, in [0.0, 1.0]. Returns 0.0 for an
        empty text (or one with no alphabetic tokens). A matched two-word
        compound ("baseball bat") counts as a single token.

    Raises:
        ValueError: If source is not one of the recognized names.
    """
    _validate_source(source)
    tokens = _get_tokens(text, include_stopwords, source)
    if not tokens:
        return 0.0
    rated = sum(
        1
        for token in tokens
        if word_concreteness(token, source, lemma_fallback) is not None
    )
    return rated / len(tokens)


def _get_tokens(text: str, include_stopwords: bool = False, source: str = "default"):
    """Tokenize text into rateable units: single words and rated compounds.

    Adjacent token pairs that form a rated two-word compound ("baseball
    bat", "act on") are emitted as one unit, greedily left to right, and
    their tokens are consumed so they aren't also counted singly. The
    bigram pass runs on the raw token stream, before punctuation and
    stopwords are dropped: punctuation between two words blocks a match
    ("...the baseball, bat in hand..."), and compounds containing a
    stopword ("act on") survive stopword removal. A compound only matches
    if the chosen source rates it — otherwise the words fall back to
    being scored singly (the compounds all come from Brysbaert, so raw
    "glasgow"/"mrc" lookups keep plain word-by-word behavior).
    """
    _ensure_nltk_data()
    raw = word_tokenize(text.lower())

    units = []
    i = 0
    while i < len(raw):
        if i + 1 < len(raw):
            compound = _BIGRAMS.get((raw[i], raw[i + 1]))
            if (
                compound is not None
                and word_concreteness(compound, source, lemma_fallback=False)
                is not None
            ):
                units.append(compound)
                i += 2
                continue
        if raw[i].isalpha():
            units.append(raw[i])
        i += 1

    if not include_stopwords:
        stop_words = set(stopwords.words("english"))
        units = [unit for unit in units if unit not in stop_words]

    return units
