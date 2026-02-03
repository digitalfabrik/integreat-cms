"""
Tests for the search suggestion functionality
"""

from __future__ import annotations

import pytest

from integreat_cms.cms.models import Contact, Page
from integreat_cms.cms.search.matchers import TrigramMatcher
from integreat_cms.cms.search.suggest import (
    normalize_search_fields,
    suggest_tokens_for_model,
)


class TestNormalizeSearchFields:
    """Tests for the normalize_search_fields function"""

    def test_normalize_numeric_weight(self) -> None:
        """Test that numeric weights are normalized to dict format"""
        search_fields = {"title": 2}
        result = normalize_search_fields(search_fields)

        assert result == {"title": {"weight": 2.0, "tokenize": True}}

    def test_normalize_dict_config(self) -> None:
        """Test that dict configs are normalized with defaults"""
        search_fields = {"title": {"weight": 3}}
        result = normalize_search_fields(search_fields)

        assert result == {"title": {"weight": 3.0, "tokenize": True}}

    def test_normalize_dict_config_with_tokenize_false(self) -> None:
        """Test that tokenize=False is preserved"""
        search_fields = {"name": {"weight": 2, "tokenize": False}}
        result = normalize_search_fields(search_fields)

        assert result == {"name": {"weight": 2.0, "tokenize": False}}

    def test_normalize_empty_dict(self) -> None:
        """Test that empty dict returns empty dict"""
        result = normalize_search_fields({})
        assert result == {}


class TestSuggestTokensForModel:
    """Tests for the suggest_tokens_for_model function"""

    @pytest.mark.django_db
    def test_empty_query_returns_empty_suggestions(self, load_test_data: None) -> None:
        """Test that empty query returns empty suggestions"""
        result = suggest_tokens_for_model(Contact, query="")

        assert result == {"suggestions": []}

    @pytest.mark.django_db
    def test_whitespace_query_returns_empty_suggestions(
        self, load_test_data: None
    ) -> None:
        """Test that whitespace-only query returns empty suggestions"""
        result = suggest_tokens_for_model(Contact, query="   ")

        assert result == {"suggestions": []}

    @pytest.mark.django_db
    def test_short_query_returns_empty_suggestions(self, load_test_data: None) -> None:
        """Test that queries shorter than MIN_QUERY_LENGTH return empty suggestions"""
        result = suggest_tokens_for_model(Contact, query="a")

        assert result == {"suggestions": []}

    @pytest.mark.django_db
    def test_returns_matching_suggestions_for_contact(
        self, load_test_data: None
    ) -> None:
        """Test that matching contact names are returned as suggestions"""
        # Query for a term that should match contacts in test data
        result = suggest_tokens_for_model(Contact, query="test")
        suggestions = result.get("suggestions", [])

        assert isinstance(suggestions, list)
        # Each suggestion should have the expected structure
        for suggestion in suggestions:
            assert "suggestion" in suggestion
            assert "score" in suggestion
            assert isinstance(suggestion["score"], float)
        assert "Testkontakt" in [s["suggestion"] for s in suggestions]

    @pytest.mark.django_db
    def test_returns_matching_suggestions_for_page(self, load_test_data: None) -> None:
        """Test that matching page titles are returned as suggestions"""
        result = suggest_tokens_for_model(Page, query="willkommen")
        suggestions = result.get("suggestions", [])

        assert isinstance(suggestions, list)
        assert "Willkommen in Augsburg" in [s["suggestion"] for s in suggestions]

    @pytest.mark.django_db
    def test_no_matches_returns_empty_suggestions(self, load_test_data: None) -> None:
        """Test that non-matching query returns empty suggestions"""
        result = suggest_tokens_for_model(Contact, query="xyznonexistentquery123")
        suggestions = result.get("suggestions", [])

        assert suggestions == []

    @pytest.mark.django_db
    def test_query_is_case_insensitive(self, load_test_data: None) -> None:
        """Test that query matching is case insensitive"""
        result_lower = suggest_tokens_for_model(Contact, query="test")
        result_upper = suggest_tokens_for_model(Contact, query="TEST")

        # Both should return the same suggestions
        assert len(result_lower.get("suggestions", [])) == len(
            result_upper.get("suggestions", [])
        )

    @pytest.mark.django_db
    def test_suggestions_have_positive_scores(self, load_test_data: None) -> None:
        """Test that all returned suggestions have positive scores"""
        result = suggest_tokens_for_model(Contact, query="test")
        suggestions = result.get("suggestions", [])

        for suggestion in suggestions:
            assert suggestion["score"] > 0

    @pytest.mark.django_db
    def test_duplicate_tokens_are_merged(self, load_test_data: None) -> None:
        """Test that duplicate tokens from multiple fields are merged"""
        result = suggest_tokens_for_model(Contact, query="test")
        suggestions = result.get("suggestions", [])

        # Each suggestion text should appear only once
        suggestion_texts = [s["suggestion"] for s in suggestions]
        assert len(suggestion_texts) == len(set(suggestion_texts))


class TestTrigramMatcher:
    """Tests for the TrigramMatcher"""

    def test_value_alias(self) -> None:
        """Test that value_alias generates correct alias names"""
        matcher = TrigramMatcher()

        assert matcher.value_alias("name") == "name_value"
        # Nested field names have __ replaced with _
        assert matcher.value_alias("location__title") == "location_title_value"

    def test_sim_alias(self) -> None:
        """Test that sim_alias generates correct alias names"""
        matcher = TrigramMatcher()

        assert matcher.sim_alias("name") == "name_sim"
        assert matcher.sim_alias("location__title") == "location_title_sim"
