# FR-1129 evidence — Effort estimates vs. commit activity; audit-log operation counts

**Prior art:** see FR-1129's own Prior art field; this file is its evidence appendix and introduces no precedent.

Recorded 2026-09-28 on main at `3621fc45`. Both commands run from the
repository root of the main checkout. Output pasted verbatim.

## 1. Effort estimate vs. commit activity (FRs numbered 900+)

Active time = sum of gaps between consecutive commits whose subject names
the FR, each gap capped at 45 min. Span = first to last such commit.
Proxy caveat: time before the first commit (research, judge runs) is not
counted.

```python
import re,subprocess,glob,statistics as st,collections
rows=[]
for f in sorted(glob.glob('feature-requests/FR-*.md')):
    m=re.match(r'feature-requests/FR-(\d+)-[^.]*\.md$',f)
    if not m: continue
    n=int(m.group(1))
    if n<900: continue
    t=open(f).read()
    e=re.search(r'Effort:\*\*\s*~?([0-9.]+)(?:\s*[-–]\s*([0-9.]+))?\s*(min|minutes|h|hours?|days?)',t,re.I)
    if not e: continue
    v=float(e.group(2) or e.group(1)); u=e.group(3).lower()
    est_h = v/60 if u.startswith('min') else v if u.startswith('h') else v*8
    log=subprocess.run(['git','log','--all','--format=%at','-E','--grep',rf'FR-0*{n}([^0-9]|$)'],capture_output=True,text=True).stdout.split()
    if len(log)<2: continue
    ts=sorted(set(map(int,log))); span=(ts[-1]-ts[0])/3600
    act=sum(min(b-a,2700) for a,b in zip(ts,ts[1:]))/3600
    rows.append((n,est_h,span,act,len(ts)))
print(f"{'FR':>6} {'est_h':>6} {'span_h':>7} {'active_h':>8} commits")
for r in rows[-20:]: print(f"{r[0]:>6} {r[1]:6.1f} {r[2]:7.1f} {r[3]:8.2f} {r[4]:>4}")
ratios=[r[3]/r[1] for r in rows if r[1]>0 and r[3]>0]
print("\nN=",len(rows),"median est_h=",st.median(r[1] for r in rows),"median active_h=",round(st.median(r[3] for r in rows),2),"median span_h=",round(st.median(r[2] for r in rows),1))
s=sorted(ratios); print("active/est median",round(st.median(s),2),"p10",round(s[len(s)//10],2),"p90",round(s[9*len(s)//10],2))
print("est histogram:",collections.Counter(r[1] for r in rows).most_common(6))
print("within 2x:",round(sum(1 for x in s if 0.5<=x<=2)/len(s),2))
print("corr(est,active):",round(st.correlation([r[1] for r in rows],[r[3] for r in rows]),2))
print("corr(commits,active):",round(st.correlation([r[4] for r in rows],[r[3] for r in rows]),2))
```

Output (last 20 rows in glob order, then aggregates):

```text
    FR  est_h  span_h active_h commits
   956   12.0     0.8     0.79    4
   957   16.0     0.8     0.79    4
   958   12.0     1.4     0.90    3
   959   12.0   313.6     3.71    7
   960    4.0   323.9     5.54   11
   961   16.0    35.2     1.50    3
   962    6.0    37.0     1.90    4
   966    4.0     1.0     1.03    7
   967   16.0     1.0     1.03    4
   970    8.0    64.5     5.27   11
   975   16.0    63.3     1.69    4
   980   24.0    63.1     0.94    3
   981    8.0     1.2     1.21    7
   982    4.0     0.9     0.87    9
   983    8.0     0.6     0.60    3
   984    4.0     3.5     3.00   11
   985    4.0     3.5     1.86    6
   990   16.0    28.1     0.75    2
   995    8.0    28.2     4.32   12
   998    4.0     1.4     0.91    3

N= 92 median est_h= 4.0 median active_h= 1.29 median span_h= 7.4
active/est median 0.24 p10 0.05 p90 0.75
est histogram: [(4.0, 40), (8.0, 21), (16.0, 12), (2.0, 9), (12.0, 4), (24.0, 4)]
within 2x: 0.21
corr(est,active): 0.09
corr(commits,active): 0.86
```

`corr(commits,active)` is near-tautological (active time is built from
commit gaps) and is not used as evidence.

## 2. Operation counts in the hook audit log

`.github/hooks/logs/audit.jsonl` is untracked and local to the operator's
machine; these counts are reproducible only there.

```bash
for p in scripts/judge.sh scripts/author.sh scripts/review.sh scripts/research.sh runSubagent; do
  printf "%s " $p; grep -c "$p" .github/hooks/logs/audit.jsonl; done
```

```text
scripts/judge.sh 109
scripts/author.sh 45
scripts/review.sh 35
scripts/research.sh 63
runSubagent 61
```

Session/event totals (143 sessions, 65,192 events) from counting distinct
`session_id` values over the same file.

## 3. Does any code read `Effort`? (parser probe)

Run in the FR-1129 worktree at `ea76ecdd`, excluding the FR-1129 witness
test:

```bash
git grep -nE 'Effort' -- scripts yamlgraph .github/hooks tests ':!tests/unit/test_fr1129_planned_operations.py'
```

Output, verbatim:

```text
tests/fixtures/fr890/FR-998-fixture-missing-research.md:6:**Effort:** 0.5 days
tests/unit/test_fr735_webllm_evidence.py:95:class TestGpuInfoBestEffort:
```

Neither hit reads the field. The first is a fixture FR that contains the
line as data; the FR-890 gate it feeds checks `**Research:**`. The second
is an unrelated class name. Removing `**Effort:**` from the template
therefore needs no code change.
