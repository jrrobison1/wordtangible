import pytest
from unittest.mock import patch
from wordtangible.concrete import avg_text_concreteness, concrete_abstract_ratio


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
