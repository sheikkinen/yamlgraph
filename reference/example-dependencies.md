# Example Dependency Taxonomy (FR-762)

## The rule

Every example root under `examples/` is classified into exactly one of two
states — no third state, no "or judgement call" branch:

| Status | Meaning | Consequence |
|---|---|---|
| `extra-backed` | Every third-party import used by the root resolves to a distribution declared somewhere in `pyproject.toml`'s `[project.optional-dependencies]`. | `pip install -e ".[<extra>]"` is sufficient to run the example. The scanner (`scripts/direct_import_scan.py`) treats this root's imports as core-strict: any newly-introduced undeclared import fails CI. |
| `externally-provisioned` | At least one third-party import used by the root does NOT resolve to any declared distribution. | The root requires manual/external provisioning (e.g. a private SDK not on PyPI, or a package this FR's frozen table deliberately excludes from `pyproject.toml`). The scanner stays report-only for this root; its gap is cited by name, never silently declared. |

There is no middle ground: an example is either fully installable via a
declared extra, or it is explicitly and permanently flagged as needing
something outside the framework's dependency surface.

## The source of truth

`examples/dependency-taxonomy.yaml` is the single allowlist. It is
**generated, not hand-authored** — see `scripts/example_taxonomy_scan.py`.
Do not hand-edit it; regenerate after adding, removing, or renaming an
example root, or after changing `pyproject.toml`'s optional-dependency
groups:

```bash
python scripts/example_taxonomy_scan.py            # regenerate
python scripts/example_taxonomy_scan.py --check     # verify it is current (CI-safe, exits 1 on drift)
```

## Root discovery

An "example root" is a directory that is mechanically detected as
independently runnable, evaluated at **every nesting depth under
`examples/`** — a directory qualifies independently of whether its parent
or a child directory also qualifies (e.g. `examples/dungeon_master/` and
`examples/dungeon_master/api/` are both roots, each with their own row):

- A candidate directory becomes a root if it contains at least one of:
  a `*.yaml` file with a top-level `nodes:` key (a YAMLGraph graph), a
  `.py` file with an `if __name__ == "__main__":` guard, or a
  `README.md` containing a fenced code block whose first token is a
  recognized command (`python`, `yamlgraph`, `pytest`, `uvicorn`, `node`,
  `npm`, `docker`, `make`, `curl`, `go`). README.md merely *existing* is
  not sufficient — a fixture/data README with no runnable command (e.g.
  `examples/plot_modeller/fixtures/README.md`) does not make its
  directory a root.
- Pure tooling/VCS noise directories (`__pycache__`, hidden directories,
  etc.) are pruned from the walk and never considered.

## Classification method

For each discovered root, every third-party import (recursively, across
all `.py` files under the root) is resolved to a PyPI distribution name
using the same import→distribution mapping and PEP 503 normalization as
`scripts/direct_import_scan.py` (FR-761) — one resolver, reused, not
reimplemented (FR-762 R-3). Names that resolve to a file or directory
that exists locally within the same root, OR within any ancestor
directory up to `examples/` (the common
`sys.path.insert(...); import tools` example-fixture idiom, which is
often rooted at the parent example package rather than a nested root
itself), are treated as local, not third-party, and excluded from
classification.

If every remaining import resolves to a declared distribution, the root
is `extra-backed` and `extra` names the extra(s) that make
`pip install -e ".[<extra>]"` alone sufficient: a single extra whose
declared distributions are a **superset** of everything the root
imports, preferred over crediting any extra that only partially owns the
surface (e.g. `examples/openai_proxy/` names only `openai-proxy`, not
every extra that happens to also declare `fastapi`). Only when no single
extra covers the whole surface does `extra` list a minimal combination.

If any import remains undeclared, the root is `externally-provisioned`
and the specific undeclared distribution(s) are cited. Per FR-762's
frozen-table condition C-4, discovering a new gap here does not license
adding it to `pyproject.toml` outside the FR's approved table — it stays
flagged.
