#!/bin/sh
# FR-1160 R-4: CI-mirror validation of the committed HEAD of /src.
# docker run --rm -v "<repo>:/src:ro" python:3.11-slim sh /src/scripts/ci_mirror_fr1160.sh
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq git curl >/dev/null
useradd -m w
su w -c '
set -e
git config --global --add safe.directory "*"
git clone -q /src ~/r && cd ~/r
git log --oneline -1
python -m venv ~/v && . ~/v/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master,otel,vision]"
python -m pytest tests/unit -q --no-cov -m "not slow" -n auto -p no:cacheprovider
python scripts/req_coverage.py --strict
ruff check yamlgraph/
ruff check --select PLW1514 --preview .
lint-imports
'
