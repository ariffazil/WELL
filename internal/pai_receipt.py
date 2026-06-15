"""
PAI Receipt — Provenance + Authority + Intent
═══════════════════════════════════════════════════════════════════
WELL local mirror of the canonical PAI Receipt schema.

CANONICAL SOURCE: arifOS/arifosmcp/schemas/pai_receipt.py (Ratified 2026-06-06)
                 This file is the WELL-local copy. Same schema, same contract.

WELL-SPECIFIC CONTRACT — DIGNITY & COERCION GATE
------------------------------------------------
WELL is REFLECT_ONLY. It never authorizes action. It signals readiness and
dignity preservation; the human (F13) and arifOS judge remain final authority.

Non-negotiables (per F13 + Scar Human Paradox doctrine):
  - Behavioral biometrics = signal only. NEVER identity root, NEVER sovereign
    proof, NEVER final authority.
  - WELL outputs carry a PAI receipt marked as ADVISORY tier (T2 INTERNAL)
    with `requires_human_intent=True` if the assessment flags coercion risk.
  - Coercion / dignity violations are SURFACED via the PAI's
    evidence.confidence and a coercion_dignity flag — not via escalation.
  - If WELL state is stale (no recent biometric injection), the PAI
    evidence.confidence = "EXPIRED" and the federation must treat WELL output
    as UNVERIFIED, regardless of well_score.

DITEMPA BUKAN DIBEI — the boundary object, forged.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class ProducerType(StrEnum):
    HUMAN = "human"
    AI = "ai"
    HUMAN_ASSISTED_AI = "human_assisted_ai"
    TOOL = "tool"
    UNKNOWN = "unknown"
    MIXED = "mixed"


class Organ(StrEnum):
    ARIFOS = "arifOS"
    GEOX = "GEOX"
    WEALTH = "WEALTH"
    WELL = "WELL"
    A_FORGE = "A-FORGE"
    APEX = "APEX"
    AAA = "AAA"
    EXTERNAL = "EXTERNAL"


class IntentAction(StrEnum):
    DRAFT = "draft"
    ANALYZE = "analyze"
    PUBLISH = "publish"
    SPEND = "spend"
    TRADE = "trade"
    ALLOCATE = "allocate"
    INVEST = "invest"
    PRICE = "price"
    TRANSFER = "transfer"
    DELETE = "delete"
    DEPLOY = "deploy"
    SEAL = "seal"
    MODIFY_TREASURY = "modify_treasury"
    ADVISORY = "advisory"


class RiskClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ATOMIC = "atomic"


class Reversibility(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class Tier(StrEnum):
    DRAFT = "draft"
    INTERNAL = "internal"
    EXTERNAL_CLAIM = "external_claim"
    CONSEQUENTIAL = "consequential"
    ATOMIC = "atomic"


PAI_RECEIPT_TYPE = "arifOS.PAI.v1"
CANONICAL_HUMAN_ROOT = "did:web:arif-fazil.com"

RISK_TO_TIER: dict[RiskClass, Tier] = {
    RiskClass.LOW: Tier.DRAFT,
    RiskClass.MEDIUM: Tier.EXTERNAL_CLAIM,
    RiskClass.HIGH: Tier.CONSEQUENTIAL,
    RiskClass.ATOMIC: Tier.ATOMIC,
}

INTENT_MIN_TIER: dict[IntentAction, Tier] = {
    IntentAction.DRAFT: Tier.DRAFT,
    IntentAction.ANALYZE: Tier.INTERNAL,
    IntentAction.ADVISORY: Tier.INTERNAL,
    IntentAction.PUBLISH: Tier.EXTERNAL_CLAIM,
    IntentAction.PRICE: Tier.EXTERNAL_CLAIM,
    IntentAction.SEAL: Tier.EXTERNAL_CLAIM,
    IntentAction.SPEND: Tier.CONSEQUENTIAL,
    IntentAction.TRADE: Tier.CONSEQUENTIAL,
    IntentAction.ALLOCATE: Tier.CONSEQUENTIAL,
    IntentAction.INVEST: Tier.CONSEQUENTIAL,
    IntentAction.TRANSFER: Tier.CONSEQUENTIAL,
    IntentAction.MODIFY_TREASURY: Tier.ATOMIC,
    IntentAction.DEPLOY: Tier.CONSEQUENTIAL,
    IntentAction.DELETE: Tier.ATOMIC,
}


class PAIOrigin(BaseModel):
    producer_type: ProducerType
    producer_id: str
    organ: Organ
    model_id: Optional[str] = None
    tool_id: Optional[str] = None


class PAIAuthority(BaseModel):
    human_root: str = CANONICAL_HUMAN_ROOT
    delegate: str
    authority_chain: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    subdelegation_allowed: bool = False


class PAIIntent(BaseModel):
    action: IntentAction
    scope: str
    risk_class: RiskClass
    external_effect: bool
    reversibility: Reversibility = Reversibility.FULL
    requires_human_intent: bool = False
    requires_888_hold: bool = False

    @model_validator(mode="after")
    def _enforce_intent_floor(self) -> "PAIIntent":
        tier = RISK_TO_TIER[self.risk_class]
        if tier in (Tier.CONSEQUENTIAL, Tier.ATOMIC) and not self.requires_human_intent:
            object.__setattr__(self, "requires_human_intent", True)
        if tier == Tier.ATOMIC and not self.requires_888_hold:
            object.__setattr__(self, "requires_888_hold", True)
        if self.requires_888_hold and self.reversibility == Reversibility.FULL:
            object.__setattr__(self, "reversibility", Reversibility.NONE)
        return self


class PAIEvidence(BaseModel):
    sources: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    confidence: str = "unknown"
    human_reviewed: bool = False
    reviewer_id: Optional[str] = None


class PAIAudit(BaseModel):
    destination: str = "VAULT999"
    previous_receipt: Optional[str] = None
    receipt_hash: Optional[str] = None
    signature: Optional[str] = None
    vault_ref: Optional[str] = None


class PAIReceipt(BaseModel):
    receipt_type: str = PAI_RECEIPT_TYPE
    object_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    origin: PAIOrigin
    authority: PAIAuthority
    intent: PAIIntent
    evidence: PAIEvidence = Field(default_factory=PAIEvidence)
    audit: PAIAudit = Field(default_factory=PAIAudit)

    @model_validator(mode="after")
    def _enforce_receipt_type(self) -> "PAIReceipt":
        if self.receipt_type != PAI_RECEIPT_TYPE:
            raise ValueError(
                f"receipt_type must be '{PAI_RECEIPT_TYPE}', got {self.receipt_type!r}"
            )
        return self


def tier_of(receipt: PAIReceipt | dict[str, Any]) -> Tier:
    if isinstance(receipt, dict):
        risk = receipt.get("intent", {}).get("risk_class", "low")
        action = receipt.get("intent", {}).get("action", "draft")
    else:
        risk = receipt.intent.risk_class
        action = receipt.intent.action
    declared_tier = RISK_TO_TIER[RiskClass(risk)]
    min_tier = INTENT_MIN_TIER[IntentAction(action)]
    tier_order = [Tier.DRAFT, Tier.INTERNAL, Tier.EXTERNAL_CLAIM, Tier.CONSEQUENTIAL, Tier.ATOMIC]
    if tier_order.index(min_tier) > tier_order.index(declared_tier):
        return min_tier
    return declared_tier


def content_hash(obj: Any) -> str:
    canonical = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mint_pai_receipt(
    *,
    object_id: str,
    producer_type: ProducerType,
    producer_id: str,
    organ: Organ,
    action: IntentAction,
    scope: str,
    risk_class: RiskClass,
    external_effect: bool = False,
    reversibility: Reversibility = Reversibility.FULL,
    delegate: str = "anonymous",
    authority_chain: Optional[list[str]] = None,
    expires_at: Optional[datetime] = None,
    subdelegation_allowed: bool = False,
    sources: Optional[list[str]] = None,
    tool_calls: Optional[list[str]] = None,
    confidence: str = "unknown",
    human_reviewed: bool = False,
    reviewer_id: Optional[str] = None,
    model_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    previous_receipt: Optional[str] = None,
    destination: str = "VAULT999",
    signature: Optional[str] = None,
) -> PAIReceipt:
    intent = PAIIntent(
        action=action, scope=scope, risk_class=risk_class,
        external_effect=external_effect, reversibility=reversibility,
    )
    authority = PAIAuthority(
        delegate=delegate,
        authority_chain=authority_chain or ["root"],
        expires_at=expires_at,
        subdelegation_allowed=subdelegation_allowed,
    )
    evidence = PAIEvidence(
        sources=sources or [], tool_calls=tool_calls or [],
        confidence=confidence, human_reviewed=human_reviewed, reviewer_id=reviewer_id,
    )
    audit = PAIAudit(destination=destination, previous_receipt=previous_receipt, signature=signature)
    origin = PAIOrigin(
        producer_type=producer_type, producer_id=producer_id, organ=organ,
        model_id=model_id, tool_id=tool_id,
    )
    receipt = PAIReceipt(
        object_id=object_id, origin=origin, authority=authority, intent=intent,
        evidence=evidence, audit=audit,
    )
    receipt.audit.receipt_hash = content_hash(receipt.model_dump(exclude={"audit"}))
    return receipt


def attach_pai_to_payload(
    payload: dict[str, Any], receipt: PAIReceipt
) -> dict[str, Any]:
    out = dict(payload)
    out["_pai_receipt"] = receipt.model_dump()
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  WELL-SPECIFIC HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def well_dignity_receipt(
    *,
    assessment_id: str,
    well_score: float,
    coercion_signals: Optional[list[str]] = None,
    dignity_preservation: float = 1.0,
    state_age_hours: Optional[float] = None,
    tool_id: str = "well_assess_homeostasis",
    model_id: Optional[str] = None,
) -> PAIReceipt:
    """Standard PAI receipt for a WELL readiness/dignity assessment.

    Coercion/dignity routing:
      - No coercion signals + state fresh (age_hours < 24):
          T2 INTERNAL, LOW, ANALYZE, confidence = current well_score tier
      - Coercion signals OR state stale (age_hours >= 24):
          T2 INTERNAL, MEDIUM, ADVISORY, confidence = "EXPIRED" (if stale)
          OR confidence = "HYPOTHESIS" (if coercion)
          requires_human_intent = True
    """
    coercion_signals = coercion_signals or []
    is_stale = state_age_hours is not None and state_age_hours >= 24.0
    has_coercion = len(coercion_signals) > 0

    if is_stale:
        risk_class, confidence = RiskClass.MEDIUM, "EXPIRED"
        requires_human_intent = True
    elif has_coercion:
        risk_class, confidence = RiskClass.MEDIUM, "HYPOTHESIS"
        requires_human_intent = True
    elif well_score < 50.0:
        risk_class, confidence = RiskClass.MEDIUM, "HYPOTHESIS"
        requires_human_intent = True
    else:
        risk_class, confidence = RiskClass.LOW, "PLAUSIBLE" if well_score >= 70 else "ESTIMATE"
        requires_human_intent = False

    return mint_pai_receipt(
        object_id=assessment_id,
        producer_type=ProducerType.AI,
        producer_id=f"well-mcp:{tool_id}",
        organ=Organ.WELL,
        action=IntentAction.ADVISORY,
        scope=f"well_assessment:{assessment_id}",
        risk_class=risk_class,
        external_effect=False,  # WELL is REFLECT_ONLY, no external effect
        reversibility=Reversibility.FULL,
        delegate=f"well-mcp:{tool_id}",
        sources=coercion_signals,  # surface coercion as evidence sources
        tool_calls=[tool_id],
        confidence=confidence,
        human_reviewed=False,
        reviewer_id=None,
        model_id=model_id,
        tool_id=tool_id,
        requires_human_intent=requires_human_intent,
    )


__all__ = [
    "PAI_RECEIPT_TYPE", "CANONICAL_HUMAN_ROOT", "RISK_TO_TIER", "INTENT_MIN_TIER",
    "ProducerType", "Organ", "IntentAction", "RiskClass", "Reversibility", "Tier",
    "PAIOrigin", "PAIAuthority", "PAIIntent", "PAIEvidence", "PAIAudit", "PAIReceipt",
    "tier_of", "content_hash", "mint_pai_receipt", "attach_pai_to_payload",
    "well_dignity_receipt",
]
