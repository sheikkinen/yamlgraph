"""Tests for diary digest tools — FR-046.

Tests cover:
- Feed config loading
- Source fetching (HN + RSS)
- Diary entry formatting
- Append-to-diary behavior
- No-op when no relevant articles
- Seed extraction and curation (Phase 2)
"""

from unittest.mock import MagicMock, patch

import pytest

# Canonical modules under examples/diary_digest/nodes/
SRC = "examples.diary_digest.nodes.sources"
WRT = "examples.diary_digest.nodes.writing"


class TestFeedConfig:
    """Test feeds.yaml loading and structure."""

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_exists(self):
        """feeds.yaml config file exists."""
        from examples.diary_digest.nodes.sources import FEEDS_PATH

        assert FEEDS_PATH.exists(), f"feeds.yaml not found at {FEEDS_PATH}"

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_has_required_keys(self):
        """feeds.yaml has topics and feeds keys."""
        from examples.diary_digest.nodes.sources import load_feeds_config

        config = load_feeds_config()
        assert "topics" in config
        assert "feeds" in config
        assert isinstance(config["topics"], list)
        assert isinstance(config["feeds"], list)
        assert len(config["topics"]) > 0
        assert len(config["feeds"]) > 0

    @pytest.mark.req("REQ-YG-072")
    def test_feeds_yaml_has_no_seeds_key(self):
        """feeds.yaml should NOT contain seeds — they are auto-extracted."""
        from examples.diary_digest.nodes.sources import load_feeds_config

        config = load_feeds_config()
        assert (
            "seeds" not in config
        ), "seeds should be auto-extracted from diary, not in feeds.yaml"


class TestFetchSources:
    """Test source fetching (HN + RSS)."""

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_hn_returns_list(self):
        """fetch_hn returns a list of article dicts."""
        from examples.diary_digest.nodes.sources import fetch_hn

        with patch(f"{SRC}.httpx.get") as mock:
            mock.return_value = MagicMock(json=lambda: [1, 2])
            with patch(f"{SRC}._fetch_hn_story") as mock_story:
                mock_story.return_value = {
                    "title": "Test",
                    "url": "https://example.com",
                    "source": "HN",
                    "timestamp": "2026-02-19T08:00:00",
                }
                result = fetch_hn(limit=2)

        assert isinstance(result, list)
        assert len(result) <= 2
        assert result[0]["source"] == "HN"

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_rss_returns_list(self):
        """fetch_rss returns a list of article dicts."""
        from examples.diary_digest.nodes.sources import fetch_rss

        with patch(f"{SRC}.feedparser.parse") as mock:
            mock.return_value = MagicMock(
                entries=[
                    MagicMock(
                        title="RSS Article",
                        link="https://example.com/rss",
                        published_parsed=(2026, 2, 19, 8, 0, 0, 0, 0, 0),
                    )
                ]
            )
            result = fetch_rss(["https://example.com/feed"], limit=5)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["source"] == "RSS"

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_sources_combines_hn_and_rss(self):
        """fetch_sources returns combined HN + RSS articles."""
        from examples.diary_digest.nodes.sources import fetch_all_sources

        with (
            patch(f"{SRC}.fetch_hn") as mock_hn,
            patch(f"{SRC}.fetch_rss") as mock_rss,
        ):
            mock_hn.return_value = [
                {
                    "title": "HN Article",
                    "url": "https://hn.com/1",
                    "source": "HN",
                    "timestamp": "2026-02-19T08:00:00",
                }
            ]
            mock_rss.return_value = [
                {
                    "title": "RSS Article",
                    "url": "https://rss.com/1",
                    "source": "RSS",
                    "timestamp": "2026-02-19T08:00:00",
                }
            ]
            result = fetch_all_sources(
                feeds=["https://example.com/feed"],
                hn_limit=10,
                rss_limit=10,
            )

        assert len(result) == 2

    @pytest.mark.req("REQ-YG-072")
    def test_fetch_hn_handles_api_error(self):
        """fetch_hn returns empty list on API error."""
        from examples.diary_digest.nodes.sources import fetch_hn

        with patch(f"{SRC}.httpx.get") as mock:
            mock.side_effect = Exception("Connection error")
            result = fetch_hn(limit=5)

        assert result == []


class TestDiaryEntryFormatting:
    """Test diary entry output format."""

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_header(self):
        """Formatted entry has ## YYYY-MM-DD: World Digest header."""
        from examples.diary_digest.nodes.writing import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test Theme",
            body="Test body content",
            seed="Test seed question?",
        )
        assert "## 2026-02-19: World Digest — Test Theme" in entry

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_seed(self):
        """Formatted entry ends with a Seed."""
        from examples.diary_digest.nodes.writing import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test",
            body="Body",
            seed="What does this mean?",
        )
        assert "**Seed:**" in entry
        assert "What does this mean?" in entry

    @pytest.mark.req("REQ-YG-072")
    def test_format_diary_entry_has_separator(self):
        """Entry starts with --- separator for diary append."""
        from examples.diary_digest.nodes.writing import format_diary_entry

        entry = format_diary_entry(
            date_str="2026-02-19",
            theme="Test",
            body="Body",
            seed="Question?",
        )
        assert entry.startswith("\n---\n\n##")


class TestAppendToDiary:
    """Test appending entries to diary.md."""

    @pytest.mark.req("REQ-YG-072")
    def test_append_adds_entry_to_end(self, tmp_path):
        """append_to_diary adds entry at end of file."""
        from examples.diary_digest.nodes.writing import append_to_diary

        diary = tmp_path / "diary.md"
        diary.write_text("# Development Diary\n\nExisting content.\n")

        entry = "\n---\n\n## 2026-02-19: World Digest — Test\n\nBody.\n\n**Seed:** Q?\n"
        append_to_diary(diary, entry)

        content = diary.read_text()
        assert "Existing content." in content
        assert "## 2026-02-19: World Digest — Test" in content
        assert content.index("Existing content.") < content.index("World Digest")

    @pytest.mark.req("REQ-YG-072")
    def test_append_preserves_existing(self, tmp_path):
        """append_to_diary doesn't modify existing content."""
        from examples.diary_digest.nodes.writing import append_to_diary

        original = "# Development Diary\n\n## 2026-02-18: Old Entry\n\nOld content.\n"
        diary = tmp_path / "diary.md"
        diary.write_text(original)

        entry = "\n---\n\n## 2026-02-19: World Digest — New\n\nNew content.\n"
        append_to_diary(diary, entry)

        content = diary.read_text()
        assert "Old content." in content
        assert "New content." in content


class TestWriteDiary:
    """Test write_diary graph tool."""

    @pytest.mark.req("REQ-YG-072")
    def test_write_diary_always_writes(self, tmp_path, monkeypatch):
        """write_diary always appends — no dry_run, no commit logic."""
        from examples.diary_digest.nodes.writing import write_diary

        diary = tmp_path / "diary.md"
        diary.write_text("# Diary\n")
        monkeypatch.setattr("examples.diary_digest.nodes.writing.DIARY_PATH", diary)

        state = {
            "diary_entry": {"theme": "Test", "body": "Body.", "seed": "Q?"},
            "date": "2026-02-19",
        }
        result = write_diary(state)

        assert result == {"written": True}
        content = diary.read_text()
        assert "World Digest — Test" in content

    @pytest.mark.req("REQ-YG-072")
    def test_write_diary_has_no_dry_run(self):
        """write_diary should not reference dry_run."""
        import inspect

        from examples.diary_digest.nodes.writing import write_diary

        source = inspect.getsource(write_diary)
        assert "dry_run" not in source

    @pytest.mark.req("REQ-YG-072")
    def test_write_diary_has_no_subprocess(self):
        """write_diary should not import or use subprocess."""
        import examples.diary_digest.nodes.writing as writing_mod

        assert not hasattr(
            writing_mod, "subprocess"
        ), "subprocess should not be imported"


class TestFilterRelevant:
    """Test filter_relevant handles map node output structure."""

    @pytest.mark.req("REQ-YG-072")
    def test_filter_extracts_score_from_map_output(self):
        """filter_relevant extracts relevance_score from map node structure.

        Map nodes collect results as:
        {"_map_index": N, "_map_analyze_all_sub": RelevanceScore(...)}
        """
        from pydantic import BaseModel

        from examples.diary_digest.nodes.writing import filter_relevant

        class RelevanceScore(BaseModel):
            title: str
            relevance_score: float
            reason: str

        state = {
            "scored_articles": [
                {
                    "_map_index": 0,
                    "_map_analyze_all_sub": RelevanceScore(
                        title="LangGraph 2.0 Released",
                        relevance_score=0.9,
                        reason="Direct framework relevance",
                    ),
                },
                {
                    "_map_index": 1,
                    "_map_analyze_all_sub": RelevanceScore(
                        title="Sizing chaos",
                        relevance_score=0.1,
                        reason="Unrelated",
                    ),
                },
            ]
        }
        result = filter_relevant(state)
        assert result["relevant_count"] == 1
        assert len(result["relevant_articles"]) == 1

    @pytest.mark.req("REQ-YG-072")
    def test_filter_flattens_map_output(self):
        """filter_relevant flattens map output for downstream prompts.

        The synthesize_diary_entry prompt expects article.title, article.url,
        article.relevance_score etc. at the top level — not nested inside
        _map_*_sub Pydantic models.
        """
        from pydantic import BaseModel

        from examples.diary_digest.nodes.writing import filter_relevant

        class RelevanceScore(BaseModel):
            title: str
            relevance_score: float
            reason: str

        state = {
            "raw_articles": [
                {
                    "title": "LangGraph 2.0",
                    "url": "https://example.com/lg2",
                    "source": "HN",
                    "timestamp": "2026-02-19T07:00:00",
                },
                {
                    "title": "Unrelated",
                    "url": "https://example.com/no",
                    "source": "RSS",
                    "timestamp": "2026-02-19T08:00:00",
                },
            ],
            "scored_articles": [
                {
                    "_map_index": 0,
                    "_map_analyze_all_sub": RelevanceScore(
                        title="LangGraph 2.0",
                        relevance_score=0.9,
                        reason="Direct relevance",
                    ),
                },
                {
                    "_map_index": 1,
                    "_map_analyze_all_sub": RelevanceScore(
                        title="Unrelated",
                        relevance_score=0.1,
                        reason="Not relevant",
                    ),
                },
            ],
        }
        result = filter_relevant(state)
        assert result["relevant_count"] == 1
        article = result["relevant_articles"][0]
        # Flattened: original fields + score fields at top level
        assert article["title"] == "LangGraph 2.0"
        assert article["url"] == "https://example.com/lg2"
        assert article["source"] == "HN"
        assert article["relevance_score"] == 0.9
        assert article["reason"] == "Direct relevance"
        # No map internal keys
        assert "_map_index" not in article
        assert "_map_analyze_all_sub" not in article

    @pytest.mark.req("REQ-YG-072")
    def test_filter_handles_flat_dict(self):
        """filter_relevant still works with flat dict articles."""
        from examples.diary_digest.nodes.writing import filter_relevant

        state = {
            "scored_articles": [
                {"title": "Relevant", "relevance_score": 0.8},
                {"title": "Irrelevant", "relevance_score": 0.2},
            ]
        }
        result = filter_relevant(state)
        assert result["relevant_count"] == 1


class TestNoOpBehavior:
    """Test that no entry is written when nothing is relevant."""

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_false_when_no_articles(self):
        """should_write_entry returns False for empty articles list."""
        from examples.diary_digest.nodes.writing import should_write_entry

        assert should_write_entry([]) is False

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_false_when_below_threshold(self):
        """should_write_entry returns False when all scores below threshold."""
        from examples.diary_digest.nodes.writing import should_write_entry

        articles = [
            {"title": "Irrelevant", "relevance_score": 0.2},
            {"title": "Also irrelevant", "relevance_score": 0.4},
        ]
        assert should_write_entry(articles, threshold=0.7) is False

    @pytest.mark.req("REQ-YG-072")
    def test_should_write_true_when_above_threshold(self):
        """should_write_entry returns True when any article above threshold."""
        from examples.diary_digest.nodes.writing import should_write_entry

        articles = [
            {"title": "Irrelevant", "relevance_score": 0.2},
            {"title": "Relevant!", "relevance_score": 0.8},
        ]
        assert should_write_entry(articles, threshold=0.7) is True


class TestExtractRawSeeds:
    """Test regex extraction of Seeds from diary files."""

    @pytest.mark.req("REQ-YG-072")
    def test_extract_from_single_file(self, tmp_path):
        """extract_raw_seeds finds **Seed:** lines in diary files."""
        from examples.diary_digest.nodes.sources import extract_raw_seeds

        diary = tmp_path / "diary.md"
        diary.write_text(
            "# Diary\n\n"
            "**Seed:** What replaces cost?\n\n"
            "Some text.\n\n"
            "**Seed:** Could archaeology be a graph?\n"
        )
        seeds = extract_raw_seeds(tmp_path)
        assert len(seeds) == 2
        assert "What replaces cost?" in seeds
        assert "Could archaeology be a graph?" in seeds

    @pytest.mark.req("REQ-YG-072")
    def test_extract_across_multiple_files(self, tmp_path):
        """extract_raw_seeds scans all diary*.md in directory."""
        from examples.diary_digest.nodes.sources import extract_raw_seeds

        (tmp_path / "diary.md").write_text("**Seed:** Seed from current.\n")
        (tmp_path / "diary-2026-02-17.md").write_text("**Seed:** Seed from archive.\n")
        (tmp_path / "not-a-diary.md").write_text("**Seed:** Should not appear.\n")

        seeds = extract_raw_seeds(tmp_path)
        assert "Seed from current." in seeds
        assert "Seed from archive." in seeds
        assert "Should not appear." not in seeds

    @pytest.mark.req("REQ-YG-072")
    def test_extract_empty_when_no_seeds(self, tmp_path):
        """extract_raw_seeds returns empty list when no Seeds found."""
        from examples.diary_digest.nodes.sources import extract_raw_seeds

        (tmp_path / "diary.md").write_text("# Diary\n\nNo seeds here.\n")
        seeds = extract_raw_seeds(tmp_path)
        assert seeds == []

    @pytest.mark.req("REQ-YG-072")
    def test_extract_ignores_non_seed_bold(self, tmp_path):
        """Only **Seed:** prefix is matched, not other bold text."""
        from examples.diary_digest.nodes.sources import extract_raw_seeds

        (tmp_path / "diary.md").write_text(
            "**Trap:** Not a seed.\n"
            "**Seed:** This is a seed.\n"
            "**Heuristic:** Also not a seed.\n"
        )
        seeds = extract_raw_seeds(tmp_path)
        assert seeds == ["This is a seed."]


class TestSeedsYaml:
    """Test seeds.yaml read/write for curated seeds."""

    @pytest.mark.req("REQ-YG-072")
    def test_load_seeds_from_file(self, tmp_path):
        """load_seeds reads plain list from seeds.yaml."""
        from examples.diary_digest.nodes.sources import load_seeds

        seeds_file = tmp_path / "seeds.yaml"
        seeds_file.write_text(
            '- "What replaces cost?"\n' '- "Could archaeology be a graph?"\n'
        )
        seeds = load_seeds(seeds_file)
        assert len(seeds) == 2
        assert "What replaces cost?" in seeds

    @pytest.mark.req("REQ-YG-072")
    def test_load_seeds_missing_file(self, tmp_path):
        """load_seeds returns empty list when file doesn't exist."""
        from examples.diary_digest.nodes.sources import load_seeds

        seeds = load_seeds(tmp_path / "nonexistent.yaml")
        assert seeds == []

    @pytest.mark.req("REQ-YG-072")
    def test_save_seeds_writes_file(self, tmp_path):
        """save_seeds writes curated list to seeds.yaml."""
        from examples.diary_digest.nodes.sources import load_seeds, save_seeds

        seeds_file = tmp_path / "seeds.yaml"
        save_seeds(seeds_file, ["Question one?", "Question two?"])

        loaded = load_seeds(seeds_file)
        assert loaded == ["Question one?", "Question two?"]

    @pytest.mark.req("REQ-YG-072")
    def test_save_seeds_graph_tool(self):
        """save_seeds_tool is a graph tool (state -> dict)."""
        from examples.diary_digest.nodes.sources import save_seeds_tool

        with patch(f"{SRC}.save_seeds") as mock_save:
            result = save_seeds_tool(
                {
                    "seeds": ["Q1?", "Q2?"],
                }
            )
            mock_save.assert_called_once()
            assert "seeds_saved" in result


class TestLoadConfigSeeds:
    """Test that load_config populates seeds and raw_seeds."""

    @pytest.mark.req("REQ-YG-072")
    def test_load_config_returns_seeds(self):
        """load_config reads seeds from seeds.yaml."""
        from examples.diary_digest.nodes.sources import load_config

        with (
            patch(f"{SRC}.load_feeds_config") as mock_feeds,
            patch(f"{SRC}.load_seeds") as mock_seeds,
            patch(f"{SRC}.extract_raw_seeds") as mock_raw,
        ):
            mock_feeds.return_value = {"topics": ["AI"], "feeds": ["http://x"]}
            mock_seeds.return_value = ["Curated question?"]
            mock_raw.return_value = ["Raw seed 1", "Raw seed 2"]

            result = load_config({})

        assert result["seeds"] == ["Curated question?"]
        assert result["raw_seeds"] == ["Raw seed 1", "Raw seed 2"]
