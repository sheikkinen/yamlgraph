# CWE Vulnerability Classifier (FR-733 — judged, implementation pending)

> **Purpose: YAMLGraph demo and research vehicle** — the second
> instance of the
> [Coded-Classification Pattern](../../reference/patterns/coded-classification.md)
> (the first is [icpc-2-rfe](../icpc-2-rfe/README.md)). Classifies
> free-text vulnerability descriptions into CWE weakness codes with
> quoted evidence — analyst assistance for CVE→CWE assignment, never
> autonomous. Not a security-decision tool.

**Status:** scope frozen and fixtures gathered; builder/graph/reducer
land with the FR-733 enforcement. See
[FR-733](../../feature-requests/FR-733-cwe-classifier-second-instance.md)
for the judged plan (candidate population 399 view-699 members,
usage-based caps from MITRE's own `Mapping_Notes`, lowest-abstraction
guard, NVD-labeled harness).

## What exists today

`data/labeled/` — eleven NVD-labeled CVE fixtures (US-government public
data, provenance-stamped, fetched live 2026-07-15): XSS, OS command
injection, path traversal, OOB read/write, off-by-one, code injection,
two multi-label cases (Log4Shell, PHP-FPM), one terse
near-underdetermined description (Citrix), and **two fixtures whose NVD
gold label is a MITRE Mapping-Discouraged code** (Drupalgeddon2→CWE-20,
Struts→CWE-755) — the pre-baked label-vs-guidance conflicts that
AC-04's disagreement protocol scores as first-class outcomes.
