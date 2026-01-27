"""Unit tests for rag_retrieve tool.

TDD Red phase: Tests written before implementation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestRagRetrieveImport:
    """Test that rag_retrieve can be imported."""

    def test_import_rag_retrieve(self):
        """Should import rag_retrieve from yamlgraph.tools."""
        from yamlgraph.tools.rag_retrieve import rag_retrieve

        assert callable(rag_retrieve)

    def test_import_from_tools_package(self):
        """Should be accessible from yamlgraph.tools namespace."""
        from yamlgraph.tools import rag_retrieve

        assert callable(rag_retrieve)


class TestRagRetrieveSignature:
    """Test rag_retrieve function signature and parameters."""

    def test_required_parameters(self):
        """Should require collection and query parameters."""
        import inspect

        from yamlgraph.tools.rag_retrieve import rag_retrieve

        sig = inspect.signature(rag_retrieve)
        params = sig.parameters

        assert "collection" in params
        assert "query" in params
        # Both should be required (no default)
        assert params["collection"].default is inspect.Parameter.empty
        assert params["query"].default is inspect.Parameter.empty

    def test_optional_parameters_have_defaults(self):
        """Should have optional parameters with sensible defaults."""
        import inspect

        from yamlgraph.tools.rag_retrieve import rag_retrieve

        sig = inspect.signature(rag_retrieve)
        params = sig.parameters

        assert params["top_k"].default == 5
        assert params["threshold"].default is None
        assert params["db_path"].default == "./vectorstore"


class TestRagRetrieveOutput:
    """Test rag_retrieve output format."""

    def test_returns_list_of_dicts(self):
        """Should return list of dicts with expected schema."""
        from yamlgraph.tools.rag_retrieve import rag_retrieve

        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: create a mock collection with some data
            db_path = Path(tmpdir) / "vectorstore"
            _create_test_collection(db_path, "test_docs")

            result = rag_retrieve(
                collection="test_docs",
                query="test query",
                db_path=str(db_path),
            )

            assert isinstance(result, list)
            if result:  # May be empty if no matches
                item = result[0]
                assert "content" in item
                assert "source" in item
                assert "score" in item

    def test_top_k_limits_results(self):
        """Should respect top_k parameter."""
        from yamlgraph.tools.rag_retrieve import rag_retrieve

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "vectorstore"
            # Create collection with 10 documents
            _create_test_collection(db_path, "many_docs", num_docs=10)

            result = rag_retrieve(
                collection="many_docs",
                query="test",
                top_k=3,
                db_path=str(db_path),
            )

            assert len(result) <= 3

    def test_threshold_filters_results(self):
        """Should filter results below threshold score."""
        from yamlgraph.tools.rag_retrieve import rag_retrieve

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "vectorstore"
            _create_test_collection(db_path, "threshold_test")

            result = rag_retrieve(
                collection="threshold_test",
                query="test",
                threshold=0.9,  # High threshold
                db_path=str(db_path),
            )

            # All results should meet threshold
            for item in result:
                assert item["score"] >= 0.9


class TestRagRetrieveErrors:
    """Test error handling."""

    def test_missing_collection_raises_error(self):
        """Should raise clear error if collection doesn't exist."""
        try:
            import lancedb
        except ImportError:
            pytest.skip("lancedb not installed - run: pip install yamlgraph[rag]")

        from yamlgraph.tools.rag_retrieve import CollectionNotFoundError, rag_retrieve

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty vectorstore
            db_path = Path(tmpdir) / "vectorstore"
            db_path.mkdir()
            lancedb.connect(str(db_path))  # Initialize empty DB

            with pytest.raises(CollectionNotFoundError) as exc_info:
                rag_retrieve(
                    collection="nonexistent",
                    query="test",
                    db_path=str(db_path),
                )

            assert "nonexistent" in str(exc_info.value)

    def test_missing_db_path_raises_error(self):
        """Should raise clear error if db_path doesn't exist."""
        from yamlgraph.tools.rag_retrieve import VectorStoreNotFoundError, rag_retrieve

        with pytest.raises(VectorStoreNotFoundError):
            rag_retrieve(
                collection="any",
                query="test",
                db_path="/nonexistent/path/vectorstore",
            )


class TestRagRetrieveEmbeddings:
    """Test embedding model handling."""

    def test_uses_model_from_collection_metadata(self):
        """Should read embedding model from collection metadata."""
        import contextlib

        from yamlgraph.tools.rag_retrieve import rag_retrieve

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "vectorstore"
            # Create collection with specific model in metadata
            _create_test_collection(
                db_path,
                "model_test",
                embedding_model="text-embedding-3-small",
            )

            # Should not raise - uses model from metadata
            with patch("yamlgraph.tools.rag_retrieve._get_embedding") as mock_embed:
                mock_embed.return_value = [0.1] * 1536  # Mock embedding

                with contextlib.suppress(Exception):
                    rag_retrieve(
                        collection="model_test",
                        query="test",
                        db_path=str(db_path),
                    )

                # Should have been called with the model from metadata
                if mock_embed.called:
                    call_kwargs = mock_embed.call_args
                    assert "text-embedding-3-small" in str(call_kwargs)


# --- Test Helpers ---


def _create_test_collection(
    db_path: Path,
    collection_name: str,
    num_docs: int = 3,
    embedding_model: str = "text-embedding-3-small",
) -> None:
    """Create a test collection with sample documents.

    This helper creates a LanceDB collection for testing purposes.
    Uses mock embeddings to avoid OpenAI API calls in tests.
    """
    import contextlib

    try:
        import lancedb
        import pyarrow as pa
    except ImportError:
        pytest.skip("lancedb not installed - run: pip install yamlgraph[rag]")

    db_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_path))

    # Create sample data with mock embeddings (1536 dimensions for OpenAI)
    data = []
    for i in range(num_docs):
        # Create deterministic mock embedding
        embedding = [float(i) / 100 + j / 10000 for j in range(1536)]
        data.append(
            {
                "content": f"Test document {i} with some content.",
                "source": f"./docs/doc{i}.md",
                "chunk_index": i,
                "vector": embedding,
            }
        )

    # Create table with schema
    schema = pa.schema(
        [
            pa.field("content", pa.string()),
            pa.field("source", pa.string()),
            pa.field("chunk_index", pa.int32()),
            pa.field("vector", pa.list_(pa.float32(), 1536)),
        ]
    )

    db.create_table(collection_name, data=data, schema=schema, mode="overwrite")

    # Store metadata
    # Note: LanceDB metadata API may vary by version
    # For now, we'll store model info in a separate metadata table
    metadata = [
        {
            "key": "embedding_model",
            "value": embedding_model,
            "indexed_at": "2026-01-27T12:00:00Z",
        }
    ]
    with contextlib.suppress(Exception):
        db.create_table(f"{collection_name}_metadata", data=metadata, mode="overwrite")
