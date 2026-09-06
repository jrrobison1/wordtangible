import pytest
from unittest.mock import patch
from wordtangible.concrete import (
    avg_text_concreteness,
    concrete_abstract_ratio,
    concreteness_coverage,
)


@pytest.mark.parametrize(
    "text, include_stopwords, only_rated_words, expected_result",
    [
        ("concrete word", False, True, 5.0),
        ("abstract concept", False, True, 2.0),
        ("mixed concrete abstract", False, True, 3.5),
        ("", False, True, 0.0),
        ("unrated word", False, True, 0.0),
        ("concrete stopword abstract", True, True, 3.33),
        ("concrete stopword abstract", False, False, 3.5),
    ],
)
@patch("wordtangible.concrete._get_tokens")
@patch("wordtangible.concrete.word_concreteness")
def test_avg_text_concreteness(
    mock_word_concreteness,
    mock_get_tokens,
    text,
    include_stopwords,
    only_rated_words,
    expected_result,
):
    mock_get_tokens.return_value = [
        word for word in text.split() if (word != "stopword" or include_stopwords)
    ]

    def mock_concreteness(word):
        concreteness_dict = {
            "concrete": 5.0,
            "abstract": 2.0,
            "mixed": 3.5,
            "stopword": 3.0,
        }
        return concreteness_dict.get(word, None)

    mock_word_concreteness.side_effect = mock_concreteness

    result = avg_text_concreteness(text, include_stopwords, only_rated_words)

    assert round(result, 2) == expected_result
    mock_get_tokens.assert_called_once_with(text, include_stopwords)
    assert mock_word_concreteness.call_count == len(
        [word for word in text.split() if (word != "stopword" or include_stopwords)]
    )


@patch("wordtangible.concrete._get_tokens")
def test_avg_text_concreteness_empty_tokens(mock_get_tokens):
    mock_get_tokens.return_value = []
    result = avg_text_concreteness("some text")
    assert result == 0.0


@pytest.mark.parametrize(
    "text, include_stopwords, very_concrete_threshold, very_abstract_threshold, expected_result",
    [
        ("concrete abstract", False, 4.0, 2.0, 1.0),
        (
            "very_concrete somewhat_concrete neutral somewhat_abstract very_abstract",
            False,
            4.0,
            2.0,
            1.0,
        ),
        ("very_concrete very_concrete neutral very_abstract", False, 4.0, 2.0, 2.0),
        ("neutral neutral neutral", False, 4.0, 2.0, 0.0),
        ("very_concrete very_concrete", False, 4.0, 2.0, float("inf")),
        ("", False, 4.0, 2.0, 0.0),
        ("unrated_word", False, 4.0, 2.0, 0.0),
        ("concrete stopword abstract", True, 4.0, 2.0, 1.0),
        ("concrete stopword abstract", False, 4.0, 2.0, 1.0),
        ("somewhat_concrete somewhat_abstract", False, 3.5, 2.5, 1.0),
    ],
)
@patch("wordtangible.concrete._get_tokens")
@patch("wordtangible.concrete.word_concreteness")
def test_concrete_abstract_ratio(
    mock_word_concreteness,
    mock_get_tokens,
    text,
    include_stopwords,
    very_concrete_threshold,
    very_abstract_threshold,
    expected_result,
):
    mock_get_tokens.return_value = [
        word for word in text.split() if (word != "stopword" or include_stopwords)
    ]

    def mock_concreteness(word):
        concreteness_dict = {
            "very_concrete": 5.0,
            "somewhat_concrete": 4.0,
            "neutral": 3.0,
            "somewhat_abstract": 2.0,
            "very_abstract": 1.0,
            "concrete": 4.5,
            "abstract": 1.5,
            "stopword": 3.0,
        }
        return concreteness_dict.get(word, None)

    mock_word_concreteness.side_effect = mock_concreteness

    result = concrete_abstract_ratio(
        text, include_stopwords, very_concrete_threshold, very_abstract_threshold
    )

    assert result == expected_result
    mock_get_tokens.assert_called_once_with(text, include_stopwords)
    assert mock_word_concreteness.call_count == len(
        [word for word in text.split() if (word != "stopword" or include_stopwords)]
    )


@patch("wordtangible.concrete._get_tokens")
def test_concrete_abstract_ratio_empty_tokens(mock_get_tokens):
    mock_get_tokens.return_value = []
    result = concrete_abstract_ratio("some text")
    assert result == 0.0


@pytest.mark.parametrize(
    "text, smoothing, expected_result",
    [
        # k=1: finite where the unsmoothed ratio is inf
        ("very_concrete very_concrete", 1.0, 3.0),        # (2+1)/(0+1)
        # k=1 damps small-sample jumpiness
        ("very_concrete very_concrete very_abstract", 1.0, 1.5),  # (2+1)/(1+1)
        # neutral result when nothing is rated in either category
        ("neutral neutral", 1.0, 1.0),                    # (0+1)/(0+1)
        ("", 1.0, 1.0),
        # smoothing=0 keeps historical behavior exactly
        ("very_concrete very_concrete", 0.0, float("inf")),
        ("neutral neutral", 0.0, 0.0),
        # small k approaches the unsmoothed ratio
        ("very_concrete very_concrete very_abstract", 0.001, pytest.approx(2.0, abs=0.01)),
    ],
)
@patch("wordtangible.concrete._get_tokens")
@patch("wordtangible.concrete.word_concreteness")
def test_concrete_abstract_ratio_smoothing(
    mock_word_concreteness, mock_get_tokens, text, smoothing, expected_result
):
    mock_get_tokens.return_value = text.split()

    def mock_concreteness(word):
        concreteness_dict = {
            "very_concrete": 5.0,
            "neutral": 3.0,
            "very_abstract": 1.0,
        }
        return concreteness_dict.get(word, None)

    mock_word_concreteness.side_effect = mock_concreteness

    result = concrete_abstract_ratio(text, smoothing=smoothing)
    assert result == expected_result


def test_concrete_abstract_ratio_negative_smoothing_raises():
    with pytest.raises(ValueError):
        concrete_abstract_ratio("some text", smoothing=-0.5)


@pytest.mark.parametrize(
    "tokens, expected_result",
    [
        (["concrete", "abstract"], 1.0),          # everything rated
        (["concrete", "zzzunrated"], 0.5),        # half rated
        (["zzzunrated", "qqqunrated"], 0.0),      # nothing rated
        ([], 0.0),                                # empty text
    ],
)
@patch("wordtangible.concrete._get_tokens")
@patch("wordtangible.concrete.word_concreteness")
def test_concreteness_coverage(
    mock_word_concreteness, mock_get_tokens, tokens, expected_result
):
    mock_get_tokens.return_value = tokens

    def mock_concreteness(word):
        return {"concrete": 4.5, "abstract": 1.5}.get(word, None)

    mock_word_concreteness.side_effect = mock_concreteness

    assert concreteness_coverage("some text") == expected_result
