"""The doc-free turn engine for DM v2 (FR-557, Contract B).

``turn_ops.invoke_turn`` does two jobs: it ASSEMBLES a turn (scope the roster to
the chapter cast, build the per-character bundles, gate memory/lifecycle) reading
the story ``doc``, and it RUNS the turn (call the turn graph, normalize intents,
apply the beat-FSM ledger, clean the recap) touching no ``doc`` at all. This
module owns the second job behind a typed request/result packet so the engine
core can be tested and reused without a ``doc``:

* :class:`TurnRequest` -- the doc-free inputs (cast bundles, scene, beats, the
  prior direction, and a CLOSED :class:`TurnExtras` set), built by the adapter.
* :func:`play_turn` -- graph invocation + intent normalization + the beat-FSM,
  returning a :class:`TurnResult`.
* the beat-FSM helpers (:func:`_phase_for_count`, :func:`_satisfied_indices`,
  :func:`_apply_beat_ledger`, :func:`_direction_dict`), moved verbatim from
  ``turn_ops`` -- pure functions over their arguments, never the ``doc``.

The ``doc`` reads (``chapter_beat_list``, ``turn_direction``, the gates, the
roster scope) stay in the :mod:`turn_ops` adapter; only their RESULTS cross into
the request. No behavior changes -- a golden characterization test pins the
byte-identical turn record and recap across the extraction (FR-557 J3).
"""

from __future__ import annotations

from pydantic import BaseModel

from examples.dungeon_master.api.graph_app import clean_text, field, get_app
from examples.dungeon_master.api.tree import TURN_GRAPH


class TurnExtras(BaseModel):
    """The turn graph's two free-text cast annotations -- a CLOSED set (FR-557 J2).

    ``protected`` names the cast the chapter must not kill off; ``gone_this_chapter``
    names those who have already exited. A closed typed model (not an open ``dict``)
    so a new annotation is a deliberate field addition, never a silent key.
    """

    protected: str = ""
    gone_this_chapter: str = ""


class TurnRequest(BaseModel):
    """The doc-free inputs to one turn, assembled by the adapter (FR-557).

    ``cast`` is the ordered list of ``{name, sheet, previous, overlay}`` bundles
    (cast order is the writeback key order); ``beats`` is the chapter's enumerated
    beat ledger and ``prior_direction`` the previous turn's direction side-channel
    -- both already read from the ``doc`` by the adapter, so the engine stays
    doc-free.
    """

    cast: list[dict]
    scene: str
    turn_n: int
    instruction: str = ""
    beats: list[str]
    prior_direction: dict
    extras: TurnExtras


class TurnResult(BaseModel):
    """The doc-free outputs of one turn (FR-557).

    ``intents`` is the cast-ordered list of normalized ``{thinking, intent,
    dialogue, expression}`` bundles the adapter keys by character id; ``direction``
    is the computed beat-FSM ledger; ``recap`` is the cleaned recap text.
    """

    intents: list[dict]
    direction: dict
    recap: str


async def play_turn(req: TurnRequest) -> TurnResult:
    """Run the turn graph for ``req`` and return the normalized, FSM-resolved result.

    Builds the same doc-free payload ``invoke_turn`` built, runs ``turn.yaml`` once
    (map -> direct -> recap), normalizes each intent to the four-field bundle in
    cast order, computes the beat-FSM direction ledger from the prior direction and
    the chapter beats, and cleans the recap. Byte-identical to the pre-extraction
    ``invoke_turn`` engine core (FR-557 J3).
    """
    result = await get_app(TURN_GRAPH).ainvoke(
        {
            "cast": req.cast,
            "scene": req.scene,
            "turn_n": str(req.turn_n),
            "instruction": req.instruction,
            "protected": req.extras.protected,
            "gone_this_chapter": req.extras.gone_this_chapter,
            "intents": [],
            "direction": {},
            "recap": "",
        }
    )
    items = result.get("intents") or []
    intents = [
        {
            "thinking": field(item, "thinking"),
            "intent": field(item, "intent"),
            "dialogue": field(item, "dialogue"),
            "expression": field(item, "expression"),
        }
        for item in items
    ]
    direction = _direction_dict(result.get("direction"))
    _apply_beat_ledger(direction, req.beats, req.prior_direction)
    return TurnResult(
        intents=intents,
        direction=direction,
        recap=clean_text(result.get("recap")),
    )


def _phase_for_count(satisfied: int, total: int) -> str:
    """Map a satisfied-beat count to the arc phase (FR-503 J3 truth table).

    ``opening`` at zero, ``resolved`` only once every beat is satisfied, ``climax``
    on the final beat, ``rising`` while partway. Because the satisfied set is
    accumulated monotonically (``_apply_beat_ledger`` unions with the prior turn),
    the computed phase is monotonic by construction — subsuming the retired FR-481
    ``_clamp_phase`` (FR-504).
    """
    if total >= 1 and satisfied >= total:
        return "resolved"
    if satisfied <= 0:
        return "opening"
    if satisfied >= total - 1:
        return "climax"
    return "rising"


def _satisfied_indices(raw: object, beats: list[str]) -> set[int]:
    """Parse the director's satisfied-beat selection into 0-based indices (FR-503).

    The scene presents the beats as a 1-based numbered list, so the director
    returns those numbers; this maps them to 0-based indices, ignoring anything
    out of range or unparseable (boundary: trust no provider's type). A model that
    echoes the beat TEXT instead of its number still resolves via a match against
    the enumerated list, so a disobedient provider does not silently drop a beat.
    """
    n = len(beats)
    lowered = [b.lower() for b in beats]
    out: set[int] = set()
    for v in raw or []:
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            i = v - 1
            if 0 <= i < n:
                out.add(i)
            continue
        s = str(v).strip()
        if not s:
            continue
        token = s.lstrip("Bb#").strip()
        if token.isdigit():
            i = int(token) - 1
            if 0 <= i < n:
                out.add(i)
            continue
        sl = s.lower()
        for i, b in enumerate(lowered):
            if sl == b or sl in b or b in sl:
                out.add(i)
                break
    return out


def _apply_beat_ledger(direction: dict, beats: list[str], prior: dict) -> None:
    """Resolve satisfied-beat indices to text, accumulate, and compute phase (FR-503).

    The director selects from a finite, enumerated beat list rather than inventing
    free-text phrases, so the satisfied set is bounded and ``beats_satisfied`` can
    no longer inflate past ``len(beats)``. The returned indices are unioned with
    the prior turn's satisfied set (cumulative), resolved back to canonical beat
    TEXT so every downstream consumer reads the same ``list[str]`` shape (J1), and
    ``phase`` / ``scene_complete`` are COMPUTED from k / N (J3) — the rails are
    code, the model judges only WHICH enumerated beats are now true. ``beats`` is a
    non-empty boundary contract (FR-504 ``_require_beats``); the FR-491 free-text
    ``N == 0`` fallback has been retired.
    """
    n = len(beats)
    cur = _satisfied_indices(direction.get("beats_satisfied"), beats)
    prior_text = (prior or {}).get("beats_satisfied") or []
    prior_idx = {beats.index(t) for t in prior_text if t in beats}
    satisfied = sorted(prior_idx | cur)
    k = len(satisfied)
    direction["beats_satisfied"] = [beats[i] for i in satisfied]
    direction["beats_total"] = n
    direction["phase"] = _phase_for_count(k, n)
    direction["scene_complete"] = k == n


def _direction_dict(raw: object) -> dict:
    """Normalise the director's output (dict or pydantic) to a typed dict (J4).

    Unlike ``field`` (which coerces to ``str``), this preserves ``scene_complete``
    as a bool and the list fields as lists, since the session and UI branch on them.
    """
    if not raw:
        return {}

    def _get(key: str, default: object) -> object:
        val = (
            raw.get(key, default)
            if isinstance(raw, dict)
            else getattr(raw, key, default)
        )
        return default if val is None else val

    return {
        "phase": str(_get("phase", "")),
        "establishing": str(_get("establishing", "")),
        "beats_satisfied": list(_get("beats_satisfied", []) or []),
        "scene_complete": bool(_get("scene_complete", False)),
        "steer": str(_get("steer", "")),
        "continuity": list(_get("continuity", []) or []),
        "cast_exits": list(_get("cast_exits", []) or []),
    }
