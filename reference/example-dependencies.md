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
independently runnable:

- Every direct child directory of `examples/` is a root, **except**
  `examples/demos/`, whose own direct children are each roots instead
  (`examples/demos/chatterbox`, `examples/demos/hello`, ...). This keeps
  one row per independently-runnable unit rather than treating the
  `demos/` umbrella as a single root.
- A candidate directory becomes a root if it contains at least one of:
  a `*.yaml` file with a top-level `nodes:` key (a YAMLGraph graph), a
  `.py` file with an `if __name__ == "__main__":` guard, or a
  `README.md`.
- `examples/shared/` is excluded from discovery: it is a support library
  imported by many other roots, not itself independently runnable.
- Loose top-level files directly under `examples/` (not inside a
  directory) are not discovered as roots by this mechanical definition;
  none currently carry third-party imports requiring taxonomy tracking.

## Classification method

For each discovered root, every third-party import (recursively, across
all `.py` files under the root) is resolved to a PyPI distribution name
using the same import→distribution mapping and PEP 503 normalization as
`scripts/direct_import_scan.py` (FR-761) — one resolver, reused, not
reimplemented (FR-762 R-3). Names that resolve to a file or directory
that exists locally within the same root (the common
`sys.path.insert(...); import tools` example-fixture idiom) are treated
as local, not third-party, and excluded from classification.

If every remaining import resolves to a declared distribution, the root
is `extra-backed` and its owning extra(s) are recorded. Multiple example
roots frequently list the same extra (or several) because dependencies
like `fastapi`/`uvicorn` are intentionally declared in more than one
optional-dependency group for independent installability — this is
existing repo practice, not a taxonomy artifact.

If any import remains undeclared, the root is `externally-provisioned`
and the specific undeclared distribution(s) are cited. Per FR-762's
frozen-table condition C-4, discovering a new gap here does not license
adding it to `pyproject.toml` outside the FR's approved table — it stays
flagged.
