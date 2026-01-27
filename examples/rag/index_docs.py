#!/usr/bin/env python3
"""Index documents into a LanceDB vector store for RAG.

Usage:
    python index_docs.py ./docs --collection my_docs
    python index_docs.py --list
    python index_docs.py --info my_docs
    python index_docs.py --delete my_docs
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Index documents for RAG retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python index_docs.py ./docs --collection my_docs
    python index_docs.py ./docs --collection my_docs --chunk-size 500
    python index_docs.py --list
    python index_docs.py --info my_docs
    python index_docs.py --delete my_docs
        """,
    )

    # Positional argument for source path (optional for management commands)
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to folder containing .md and .txt files",
    )

    # Collection options
    parser.add_argument(
        "--collection",
        "-c",
        help="Name of the collection to create/update",
    )

    # Chunking options
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum characters per chunk (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Overlap between chunks (default: 100)",
    )

    # Embedding options
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-small",
        help="OpenAI embedding model (default: text-embedding-3-small)",
    )

    # Database options
    parser.add_argument(
        "--db-path",
        default="./vectorstore",
        help="Path to LanceDB database (default: ./vectorstore)",
    )

    # Management commands
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all collections",
    )
    parser.add_argument(
        "--info",
        metavar="COLLECTION",
        help="Show info for a collection",
    )
    parser.add_argument(
        "--delete",
        metavar="COLLECTION",
        help="Delete a collection",
    )

    args = parser.parse_args()

    # Check lancedb is installed
    try:
        import importlib.util

        if importlib.util.find_spec("lancedb") is None:
            raise ImportError("lancedb not found")
    except ImportError:
        logger.error("❌ lancedb not installed. Run: pip install yamlgraph[rag]")
        sys.exit(1)

    # Handle management commands
    if args.list:
        list_collections(args.db_path)
        return

    if args.info:
        show_collection_info(args.db_path, args.info)
        return

    if args.delete:
        delete_collection(args.db_path, args.delete)
        return

    # Indexing requires source and collection
    if not args.source:
        parser.error("source path is required for indexing")
    if not args.collection:
        parser.error("--collection is required for indexing")

    # Check OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Run indexing
    index_documents(
        source_path=args.source,
        collection=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedding_model=args.embedding_model,
        db_path=args.db_path,
    )


def list_collections(db_path: str) -> None:
    """List all collections in the database."""
    import lancedb

    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        logger.info("📂 No vector store found at %s", db_path)
        return

    db = lancedb.connect(str(db_path_obj))
    tables = [t for t in db.table_names() if not t.endswith("_metadata")]

    if not tables:
        logger.info("📂 No collections found")
        return

    logger.info("📂 Collections in %s:", db_path)
    for table in tables:
        tbl = db.open_table(table)
        count = tbl.count_rows()
        logger.info("  • %s (%d chunks)", table, count)


def show_collection_info(db_path: str, collection: str) -> None:
    """Show info for a specific collection."""
    import lancedb

    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        logger.error("❌ Vector store not found at %s", db_path)
        return

    db = lancedb.connect(str(db_path_obj))

    if collection not in db.table_names():
        logger.error("❌ Collection '%s' not found", collection)
        return

    tbl = db.open_table(collection)
    count = tbl.count_rows()

    logger.info("📊 Collection: %s", collection)
    logger.info("   Chunks: %d", count)

    # Try to get metadata
    metadata_table = f"{collection}_metadata"
    if metadata_table in db.table_names():
        meta = db.open_table(metadata_table).to_arrow()
        for i in range(meta.num_rows):
            key = meta.column("key")[i].as_py()
            value = meta.column("value")[i].as_py()
            logger.info("   %s: %s", key.replace("_", " ").title(), value)


def delete_collection(db_path: str, collection: str) -> None:
    """Delete a collection."""
    import lancedb

    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        logger.error("❌ Vector store not found at %s", db_path)
        return

    db = lancedb.connect(str(db_path_obj))

    if collection not in db.table_names():
        logger.error("❌ Collection '%s' not found", collection)
        return

    db.drop_table(collection)
    logger.info("🗑️  Deleted collection: %s", collection)

    # Also delete metadata table if exists
    metadata_table = f"{collection}_metadata"
    if metadata_table in db.table_names():
        db.drop_table(metadata_table)
        logger.info("🗑️  Deleted metadata: %s", metadata_table)


def index_documents(
    source_path: str,
    collection: str,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    db_path: str,
) -> None:
    """Index documents from source path into collection."""
    import lancedb
    import pyarrow as pa
    from openai import OpenAI

    source = Path(source_path)
    if not source.exists():
        logger.error("❌ Source path not found: %s", source_path)
        sys.exit(1)

    # Find all documents
    files = list(source.glob("**/*.md")) + list(source.glob("**/*.txt"))
    if not files:
        logger.error("❌ No .md or .txt files found in %s", source_path)
        sys.exit(1)

    logger.info("📝 Found %d files in %s", len(files), source_path)

    # Read and chunk documents
    chunks = []
    for file_path in files:
        content = file_path.read_text(encoding="utf-8")
        file_chunks = chunk_text(content, chunk_size, chunk_overlap)

        for i, chunk in enumerate(file_chunks):
            chunks.append(
                {
                    "content": chunk,
                    "source": str(file_path),
                    "chunk_index": i,
                }
            )

    logger.info("📦 Created %d chunks", len(chunks))

    # Generate embeddings
    logger.info("🔮 Generating embeddings with %s...", embedding_model)
    client = OpenAI()

    embeddings = []
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch]

        response = client.embeddings.create(input=texts, model=embedding_model)
        for emb in response.data:
            embeddings.append(emb.embedding)

        logger.info(
            "   Embedded %d/%d chunks", min(i + batch_size, len(chunks)), len(chunks)
        )

    # Add embeddings to chunks
    for i, chunk in enumerate(chunks):
        chunk["vector"] = embeddings[i]

    # Create database and table
    db_path_obj = Path(db_path)
    db_path_obj.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_path_obj))

    # Define schema
    vector_dim = len(embeddings[0])
    schema = pa.schema(
        [
            pa.field("content", pa.string()),
            pa.field("source", pa.string()),
            pa.field("chunk_index", pa.int32()),
            pa.field("vector", pa.list_(pa.float32(), vector_dim)),
        ]
    )

    # Create or overwrite table
    db.create_table(collection, data=chunks, schema=schema, mode="overwrite")
    logger.info("💾 Saved to collection: %s", collection)

    # Save metadata
    metadata = [
        {"key": "embedding_model", "value": embedding_model},
        {"key": "indexed_at", "value": datetime.now().isoformat()},
        {"key": "source_path", "value": str(source)},
        {"key": "chunk_count", "value": str(len(chunks))},
    ]
    db.create_table(f"{collection}_metadata", data=metadata, mode="overwrite")

    logger.info("✅ Indexed %d chunks into '%s'", len(chunks), collection)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks.

    Tries to split on paragraph boundaries, falling back to sentences,
    then words, then characters.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find a good break point
        chunk = text[start:end]

        # Prefer paragraph breaks
        para_break = chunk.rfind("\n\n")
        if para_break > chunk_size // 2:
            end = start + para_break + 2
        else:
            # Try sentence breaks
            for sep in [". ", "! ", "? ", "\n"]:
                sent_break = chunk.rfind(sep)
                if sent_break > chunk_size // 2:
                    end = start + sent_break + len(sep)
                    break
            else:
                # Fall back to word break
                space_break = chunk.rfind(" ")
                if space_break > chunk_size // 2:
                    end = start + space_break + 1

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks


if __name__ == "__main__":
    main()
