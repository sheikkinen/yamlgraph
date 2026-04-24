#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env.google ]] || [[ ! -f .env.vertex ]]; then
  echo "Missing .env.google or .env.vertex"
  echo "Copy templates first:"
  echo "  cp .env.google.example .env.google"
  echo "  cp .env.vertex.example .env.vertex"
  echo "  cp .env.azure.example .env.azure  # optional"
  exit 1
fi

runs="${1:-5}"

echo "== Google consumer API =="
set -a
source ./.env.google
set +a
yamlgraph graph bench ./graph.google.yaml \
  --models google/gemini-2.0-flash \
  --var-file ./vars.yaml \
  --runs "$runs"

unset GOOGLE_API_KEY PROVIDER GOOGLE_MODEL

echo
echo "== Vertex API =="
set -a
source ./.env.vertex
set +a
yamlgraph graph bench ./graph.vertex.yaml \
  --models vertex/gemini-2.0-flash \
  --var-file ./vars.yaml \
  --runs "$runs"

if [[ -f .env.azure ]]; then
  unset VERTEX_API_KEY GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION VERTEX_MODEL

  echo
  echo "== Azure AI Foundry =="
  set -a
  source ./.env.azure
  set +a

  azure_model="${AZURE_MODEL:-gpt-4o}"
  yamlgraph graph bench ./graph.azure.yaml \
    --models "azure/${azure_model}" \
    --var-file ./vars.yaml \
    --runs "$runs"
else
  echo
  echo "== Azure AI Foundry =="
  echo "Skipped (.env.azure not found)."
fi
