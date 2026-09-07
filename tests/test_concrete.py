import pytest
from unittest.mock import patch
from wordtangible.concrete import (
    avg_text_concreteness,
    concrete_abstract_ratio,
    concreteness_coverage,
    word_concreteness,
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

    def mock_concreteness(word, source="default"):
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
    mock_get_tokens.assert_called_once_with(text, include_stopwords, "default")
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

    def mock_concreteness(word, source="default"):
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
    mock_get_tokens.assert_called_once_with(text, include_stopwords, "default")
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

    def mock_concreteness(word, source="default"):
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

    def mock_concreteness(word, source="default"):
        return {"concrete": 4.5, "abstract": 1.5}.get(word, None)

    mock_word_concreteness.side_effect = mock_concreteness

    assert concreteness_coverage("some text") == expected_result


class TestWordConcretenessSources:
    """Integration tests against the bundled ratings data."""

    def test_default_is_brysbaert_when_available(self):
        # apple is in all three sources; the default returns Brysbaert's
        # raw published value, not a blend
        assert word_concreteness("apple") == 5.0
        assert word_concreteness("apple") == word_concreteness("apple", "brysbaert")

    def test_default_falls_back_to_glasgow_then_mrc(self):
        # abattoir: Glasgow-only -> Glasgow CNC 5.455 rescaled from 1-7 to 1-5
        assert word_concreteness("abattoir") == pytest.approx(3.97, abs=0.01)
        assert word_concreteness("abattoir", "brysbaert") is None
        # abbess: MRC-only -> CNC 401 rescaled from 100-700 to 1-5
        assert word_concreteness("abbess") == pytest.approx(3.01, abs=0.01)

    def test_raw_single_sources_keep_native_scales(self):
        assert word_concreteness("apple", "brysbaert") == 5.0  # 1-5
        assert word_concreteness("apple", "glasgow") == 6.824  # 1-7
        assert word_concreteness("apple", "mrc") == 620  # 100-700

    def test_unrated_word_is_none_for_every_source(self):
        for source in ("default", "brysbaert", "glasgow", "mrc", "open", "mean"):
            assert word_concreteness("zzzunrated", source) is None

    def test_open_never_uses_mrc(self):
        # abbess is rated only by MRC
        assert word_concreteness("abbess", "open") is None
        # brysbaert wins when present, else glasgow rescaled
        assert word_concreteness("apple", "open") == 5.0
        assert word_concreteness("abattoir", "open") == pytest.approx(3.97, abs=0.01)

    def test_mean_averages_available_normalized_ratings(self):
        # apple: mean of brysbaert 5.0, glasgow 6.824 -> 4.88, mrc 620 -> 4.47
        assert word_concreteness("apple", "mean") == pytest.approx(4.78, abs=0.01)
        # single-source words: mean equals that source normalized
        assert word_concreteness("abbess", "mean") == pytest.approx(3.01, abs=0.01)

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError):
            word_concreteness("apple", "webster")
        with pytest.raises(ValueError):
            avg_text_concreteness("some text", source="webster")
        with pytest.raises(ValueError):
            concrete_abstract_ratio("some text", source="webster")
        with pytest.raises(ValueError):
            concreteness_coverage("some text", source="webster")

    def test_text_functions_accept_source(self):
        text = "The apple fell."
        assert avg_text_concreteness(text, source="brysbaert") == pytest.approx(
            avg_text_concreteness(text)
        )
        # on glasgow's 1-7 scale the same text scores higher than on 1-5
        assert avg_text_concreteness(text, source="glasgow") > avg_text_concreteness(
            text
        )
        assert concreteness_coverage("apple abbess", source="mrc") == 1.0
        assert concreteness_coverage("apple abbess", source="glasgow") == 0.5


class TestBigramMatching:
    """Rated two-word compounds (all from Brysbaert) match as one unit."""

    def test_compound_looked_up_directly(self):
        assert word_concreteness("baseball bat") is not None

    def test_compound_beats_single_words(self):
        # the text's only unit is the compound, so the average is exactly
        # the compound's rating, not a blend of "baseball" and "bat"
        expected = word_concreteness("baseball bat")
        assert avg_text_concreteness("The baseball bat broke.") == pytest.approx(
            (expected + word_concreteness("broke")) / 2
        )

    def test_compound_counts_as_one_unit(self):
        assert concreteness_coverage("baseball bat") == 1.0

    def test_punctuation_blocks_match(self):
        # "baseball, bat" must not join across the comma
        assert avg_text_concreteness("baseball, bat") == pytest.approx(
            (word_concreteness("baseball") + word_concreteness("bat")) / 2
        )

    def test_stopword_compound_survives_stopword_removal(self):
        # "act on" contains the stopword "on" but matches as a unit before
        # stopword filtering
        expected = word_concreteness("act on")
        assert avg_text_concreteness("They act on impulse.") == pytest.approx(
            (expected + word_concreteness("impulse")) / 2
        )

    def test_cased_compound_matches_lowercased_text(self):
        expected = word_concreteness("Dutch oven")
        assert expected is not None
        assert avg_text_concreteness("the dutch oven", include_stopwords=False) == (
            pytest.approx(expected)
        )

    def test_greedy_left_to_right(self):
        # after "chain saw" is consumed, "blade" is scored alone
        expected = word_concreteness("chain saw")
        assert avg_text_concreteness("chain saw blade") == pytest.approx(
            (expected + word_concreteness("blade")) / 2
        )

    def test_raw_sources_unaffected(self):
        # Glasgow and MRC rate no compounds; the pair falls back to singles
        assert concreteness_coverage("baseball bat", source="mrc") == 0.5  # bat only
