#!/bin/bash
# RAG Demo Script
# Indexes sample docs and runs a question through the RAG pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "❌ .env file not found in project root"
    exit 1
fi

echo "🗂️  Indexing sample documents..."
python examples/rag/index_docs.py examples/rag/docs --collection test_docs

echo ""
echo "🔍 Running RAG query..."
QUESTION="${1:-What is YAMLGraph?}"
echo "   Question: $QUESTION"
echo ""

yamlgraph graph run examples/rag/graph.yaml -v "question=$QUESTION" --full
