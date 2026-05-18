# Feature Request: FR-370 Jaccard-based TTS echo cancellation filter

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-05-13

## Summary

Add a post-STT similarity filter that detects and discards acoustic echoes of the system's own TTS output picked up by the caller's microphone.

## Value Statement

Callers no longer waste a conversational turn on phantom "user" utterances that are actually the system hearing itself, eliminating echo-induced confusion and redundant graph processing.

## Problem

Production analysis on 2026-05-13 revealed that 3 of 11 calls (27%) had the STT engine transcribing the system's own TTS greeting as a "user" utterance. Evidence:

| Call | Gap from TTS start | User "said" | System said | Verdict |
|------|---------------------|-------------|-------------|---------|
| 4 | 4.5s (mid-playback) | "Olet soittanut tervolan terveysasemalle." | "Olet soittanut Tervolan terveysasemalle." | Echo (100% match) |
| 5 | 4.4s (mid-playback) | "Olet soittanut tervolan terveysasemalle." | "Olet soittanut Tervolan terveysasemalle." | Echo (100% match) |
| 7 | 3.6s (mid-playback) | "Olet soittanut **pervolan**." | "Olet soittanut Tervolan terveysasemalle." | Echo (garbled) |

Key observations:
- Echo arrives 3.6–4.5s after TTS **start**, while playback is still ongoing (~5–6s total)
- Only the first sentence is echoed, never the full multi-sentence greeting
- Call 7's "pervolan" garbling confirms degraded audio (phone speaker → microphone → STT), not human speech
- Affects 2 different callers — systematic, not behavioral

### Why not mute STT during TTS?

Muting the STT feed while `speaking=True` would kill barge-in — a real user interrupting during the greeting wouldn't be heard. The filter must operate **after** STT, not before.

## Proposed Solution

Add a similarity filter in the FSM's `transcribed` handler, before `accumulate_text`. When a user utterance is too similar to recently spoken system text, log and discard it.

### Algorithm: fuzzy word-level Jaccard

```python
from difflib import SequenceMatcher


def is_echo(
    user_text: str,
    recent_system_texts: list[str],
    *,
    coverage_threshold: float = 0.55,
    fuzzy_word_threshold: float = 0.75,
) -> bool:
    """Detect if user_text is an acoustic echo of recent system TTS output.

    Uses fuzzy word-level matching to handle STT transcription errors
    (e.g. "pervolan" ↔ "Tervolan").

    Args:
        user_text: The STT-transcribed user utterance.
        recent_system_texts: Last N system utterances (raw text with newlines).
        coverage_threshold: Fraction of user words that must match a system word.
        fuzzy_word_threshold: Per-word character similarity threshold.

    Returns:
        True if the utterance should be discarded as echo.
    """
    user_words = user_text.lower().strip().rstrip(".!?").split()
    if not user_words:
        return False

    for sys_text in recent_system_texts:
        for sentence in sys_text.replace("\n", ". ").split(". "):
            sys_words = [w.strip().rstrip(".!?,") for w in sentence.lower().split()]
            if not sys_words:
                continue
            matched = sum(
                1
                for uw in user_words
                if any(
                    SequenceMatcher(None, uw, sw).ratio() >= fuzzy_word_threshold
                    for sw in sys_words
                )
            )
            coverage = matched / len(user_words)
            if coverage >= coverage_threshold:
                return True
    return False
```

### Validation against 2026-05-13 corpus

| User text | Best system match | Coverage | Decision |
|-----------|------------------|----------|----------|
| "Olet soittanut tervolan terveysasemalle." | greeting sentence 1 | 4/4 = 1.0 | **Discard** ✓ |
| "Olet soittanut pervolan." | greeting sentence 1 | 3/3 = 1.0 (pervolan↔Tervolan=0.75) | **Discard** ✓ |
| "On oikein." | "Onko tämä oikein?" | 1/2 = 0.5 | **Keep** ✓ |
| "Kyllä." | any | 0/1 = 0.0 | **Keep** ✓ |
| "Olen julia ja minulla on kova päänsärky." | any | 0/7 = 0.0 | **Keep** ✓ |
| "Moi." | any | 0/1 = 0.0 | **Keep** ✓ |
| "Sattuu vatsaan." | any | 0/2 = 0.0 | **Keep** ✓ |

### Integration point

In the FSM engine's `transcribed` event handler (statemachine-engine), before `accumulate_text`:

```python
# In the transcribed handler
if is_echo(transcribed_text, self._recent_system_texts):
    logger.info("🔇 Echo discarded: %r", transcribed_text[:60])
    return  # Skip accumulation and graph processing

self._accumulate_text(transcribed_text)
```

The `_recent_system_texts` buffer holds the last 2–3 system utterances and is cleared/rotated on each new system utterance.

### Configuration

The filter should be toggleable via environment variable for safe rollout:

```
ECHO_FILTER_ENABLED=true          # default: true
ECHO_FILTER_COVERAGE=0.55         # default: 0.55
ECHO_FILTER_FUZZY_WORD=0.75       # default: 0.75
```

## Acceptance Criteria

- [ ] `is_echo()` function added to statemachine-engine with fuzzy word-level Jaccard matching
- [ ] Filter invoked in `transcribed` handler before `accumulate_text`
- [ ] Recent system texts buffer maintained (last 2–3 utterances)
- [ ] Echo discards logged at INFO level with the discarded text
- [ ] Filter toggleable via `ECHO_FILTER_ENABLED` env var
- [ ] Thresholds configurable via `ECHO_FILTER_COVERAGE` and `ECHO_FILTER_FUZZY_WORD` env vars
- [ ] Unit tests cover: exact echo, fuzzy echo ("pervolan"), legitimate short answers ("On oikein", "Kyllä"), legitimate long answers, empty input
- [ ] No false positives on the full 2026-05-13 transcript corpus (11 calls)
- [ ] Barge-in functionality unaffected (STT feed never muted)
- [ ] Documentation updated

## Alternatives Considered

1. **Mute STT during TTS playback** — Rejected: kills barge-in, which is essential for natural conversation flow.
2. **Exact string matching** — Rejected: fails on STT transcription errors ("pervolan" ≠ "Tervolan").
3. **Pure Jaccard (exact word match)** — Rejected: misses fuzzy cases. "pervolan" has 0 exact word matches against "Tervolan".
4. **SequenceMatcher on full text** — Works but less interpretable and harder to tune than word-level coverage.
5. **Twilio echo cancellation settings** — Worth investigating as complementary but not a substitute: we can't control all phone hardware, and the problem is in the STT processing of whatever audio arrives.

## Related

- `projects/ninchat_voice/docs/2026-05-13-summary.md` — production day analysis
- `projects/ninchat_voice/docs/2026-05-13-troubleshooting-calls-4-5-6-9.md` — call-level analysis
- FR-??? (FSM preemption race) — separate but related; echo + preemption can compound
