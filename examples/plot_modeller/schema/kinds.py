"""FR-571 — 17-kind Propp-derived action alphabet."""

from __future__ import annotations

from enum import Enum


class FunctionKind(str, Enum):
    villainy = "villainy"
    lack = "lack"
    mediation = "mediation"
    departure = "departure"
    donor_test = "donor_test"
    provision = "provision"
    struggle = "struggle"
    victory = "victory"
    liquidation = "liquidation"
    return_ = "return"
    pursuit = "pursuit"
    rescue = "rescue"
    recognition = "recognition"
    exposure = "exposure"
    punishment = "punishment"
    reconciliation = "reconciliation"
    death = "death"
