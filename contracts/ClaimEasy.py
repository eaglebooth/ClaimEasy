# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json


class ClaimEasy(gl.Contract):
    fund_owners: TreeMap[u256, str]
    fund_balance: u256
    fund_reserved: u256
    fund_paid: u256
    max_payout: u256
    min_confidence: u256
    claim_count: u256

    claim_order_ids: TreeMap[u256, str]
    claim_buyer_wallets: TreeMap[u256, str]
    claim_merchant_wallets: TreeMap[u256, str]
    claim_item_titles: TreeMap[u256, str]
    claim_order_values: TreeMap[u256, u256]
    claim_requested_refunds: TreeMap[u256, u256]
    claim_tracking_urls: TreeMap[u256, str]
    claim_unbox_urls: TreeMap[u256, str]
    claim_delivery_slip_urls: TreeMap[u256, str]
    claim_policy_urls: TreeMap[u256, str]
    claim_statuses: TreeMap[u256, str]
    claim_decisions: TreeMap[u256, str]
    claim_approved_refunds: TreeMap[u256, u256]
    claim_carrier_fault_scores: TreeMap[u256, u256]
    claim_packaging_integrity_scores: TreeMap[u256, u256]
    claim_confidence_scores: TreeMap[u256, u256]
    claim_ai_reports: TreeMap[u256, str]

    def __init__(self):
        self.fund_balance = u256(0)
        self.fund_reserved = u256(0)
        self.fund_paid = u256(0)
        self.max_payout = u256(0)
        self.min_confidence = u256(0)
        self.claim_count = u256(0)

    @gl.public.write
    def initialize_fund(
        self,
        owner_wallet: str,
        balance: u256,
        max_payout: u256,
        min_confidence: u256,
    ) -> str:
        if len(owner_wallet) == 0:
            return "EMPTY_OWNER"
        if balance == u256(0):
            return "ZERO_BALANCE"
        if max_payout == u256(0):
            return "ZERO_MAX_PAYOUT"
        if min_confidence > u256(100):
            return "CONFIDENCE_OUT_OF_RANGE"

        self.fund_owners[u256(0)] = owner_wallet
        self.fund_balance = balance
        self.max_payout = max_payout
        self.min_confidence = min_confidence
        return "FUND_READY"

    @gl.public.write
    def file_claim(
        self,
        order_id: str,
        buyer_wallet: str,
        merchant_wallet: str,
        item_title: str,
        order_value: u256,
        requested_refund: u256,
    ) -> typing.Any:
        if self.fund_balance == u256(0):
            return "FUND_NOT_READY"
        if len(order_id) == 0:
            return "EMPTY_ORDER_ID"
        if len(buyer_wallet) == 0:
            return "EMPTY_BUYER"
        if len(merchant_wallet) == 0:
            return "EMPTY_MERCHANT"
        if len(item_title) == 0:
            return "EMPTY_ITEM"
        if order_value == u256(0):
            return "ZERO_ORDER_VALUE"
        if requested_refund == u256(0):
            return "ZERO_REFUND"
        if requested_refund > order_value:
            return "REFUND_EXCEEDS_ORDER"
        if requested_refund > self.max_payout:
            return "REFUND_EXCEEDS_MAX_PAYOUT"

        claim_id = self.claim_count
        self.claim_order_ids[claim_id] = order_id
        self.claim_buyer_wallets[claim_id] = buyer_wallet
        self.claim_merchant_wallets[claim_id] = merchant_wallet
        self.claim_item_titles[claim_id] = item_title
        self.claim_order_values[claim_id] = order_value
        self.claim_requested_refunds[claim_id] = requested_refund
        self.claim_tracking_urls[claim_id] = ""
        self.claim_unbox_urls[claim_id] = ""
        self.claim_delivery_slip_urls[claim_id] = ""
        self.claim_policy_urls[claim_id] = ""
        self.claim_statuses[claim_id] = "FILED"
        self.claim_decisions[claim_id] = "PENDING"
        self.claim_approved_refunds[claim_id] = u256(0)
        self.claim_carrier_fault_scores[claim_id] = u256(0)
        self.claim_packaging_integrity_scores[claim_id] = u256(0)
        self.claim_confidence_scores[claim_id] = u256(0)
        self.claim_ai_reports[claim_id] = ""
        self.claim_count = claim_id + u256(1)
        return claim_id

    @gl.public.write
    def attach_evidence(
        self,
        claim_id: u256,
        tracking_url: str,
        unbox_url: str,
        delivery_slip_url: str,
        policy_url: str,
    ) -> str:
        if claim_id >= self.claim_count:
            return "CLAIM_NOT_FOUND"
        if self.claim_statuses[claim_id] != "FILED":
            return "CLAIM_NOT_FILED"
        if self._is_url(tracking_url) == u256(0):
            return "BAD_TRACKING_URL"
        if self._is_url(unbox_url) == u256(0):
            return "BAD_UNBOX_URL"
        if self._is_url(delivery_slip_url) == u256(0):
            return "BAD_DELIVERY_SLIP_URL"
        if self._is_url(policy_url) == u256(0):
            return "BAD_POLICY_URL"

        self.claim_tracking_urls[claim_id] = tracking_url
        self.claim_unbox_urls[claim_id] = unbox_url
        self.claim_delivery_slip_urls[claim_id] = delivery_slip_url
        self.claim_policy_urls[claim_id] = policy_url
        self.claim_statuses[claim_id] = "EVIDENCE_READY"
        return "EVIDENCE_READY"

    @gl.public.write
    def evaluate_claim(self, claim_id: u256) -> typing.Any:
        if claim_id >= self.claim_count:
            return "CLAIM_NOT_FOUND"
        if self.claim_statuses[claim_id] != "EVIDENCE_READY":
            return "EVIDENCE_NOT_READY"

        order_id = self.claim_order_ids[claim_id]
        item_title = self.claim_item_titles[claim_id]
        order_value = self.claim_order_values[claim_id]
        requested_refund = self.claim_requested_refunds[claim_id]
        tracking_url = self.claim_tracking_urls[claim_id]
        unbox_url = self.claim_unbox_urls[claim_id]
        delivery_slip_url = self.claim_delivery_slip_urls[claim_id]
        policy_url = self.claim_policy_urls[claim_id]
        min_confidence = self.min_confidence
        max_payout = self.max_payout

        def run_review() -> str:
            tracking = self._render_evidence(tracking_url)
            unbox = self._render_evidence(unbox_url)
            delivery = self._render_evidence(delivery_slip_url)
            policy = self._render_evidence(policy_url)
            prompt = f"""You are ClaimEasy, an on-chain shipping damage claims jury.

Claim:
- order_id: {order_id}
- item: {item_title}
- order_value_cents: {order_value}
- requested_refund_cents: {requested_refund}
- max_payout_cents: {max_payout}
- minimum_confidence: {min_confidence}

Evidence read on-chain:
TRACKING PAGE:
{tracking}

UNBOX VIDEO OR PAGE:
{unbox}

DELIVERY SLIP / SHIPPER PHOTO:
{delivery}

MERCHANT SHIPPING INSURANCE POLICY:
{policy}

Judge whether the damage happened during shipping.
Score exactly:
- packaging_integrity_score 0-100: higher means seal/tape/box looked intact before unboxing.
- carrier_fault_score 0-100: higher means shipping damage is the likely cause.
- confidence_score 0-100: confidence in the final decision.

Decision rules:
- APPROVED if carrier_fault_score >= 75, packaging_integrity_score >= 65, confidence_score >= minimum_confidence.
- PARTIAL_REFUND if carrier_fault_score is 55-74 and confidence_score >= minimum_confidence.
- NEEDS_REVIEW if evidence is missing, unreadable, contradictory, or confidence_score < minimum_confidence.
- REJECTED if damage appears caused after delivery, product defect unrelated to shipping, or the seal was already broken before proof.

Refund rules:
- APPROVED may refund up to requested_refund_cents but never above max_payout_cents.
- PARTIAL_REFUND should be a fair smaller amount, never above requested_refund_cents.
- NEEDS_REVIEW and REJECTED must set approved_refund_cents to 0.

Respond with ONLY this JSON, no markdown:
{{
  "decision": "APPROVED|PARTIAL_REFUND|NEEDS_REVIEW|REJECTED",
  "approved_refund_cents": 0,
  "carrier_fault_score": 0,
  "packaging_integrity_score": 0,
  "confidence_score": 0,
  "reason": "one concise sentence citing the evidence"
}}"""
            return gl.nondet.exec_prompt(prompt)

        principle = """Two ClaimEasy AI reviews are equivalent when they agree on the substantive outcome:
the same decision label among APPROVED, PARTIAL_REFUND, NEEDS_REVIEW, REJECTED; the same conclusion about whether
shipping/carrier fault caused the damage; the same refund amount or a materially identical refund bucket; and similar
carrier fault, package integrity, and confidence score bands. Ignore wording differences in the reason field, JSON key
order, punctuation, capitalization, or harmless phrasing. Reject equivalence if one result pays while the other denies,
if one result says the seal was intact and the other says it was broken, or if the refund amount changes the payout."""

        consensus = gl.eq_principle.prompt_comparative(run_review, principle)
        parsed = self._parse_review(consensus, requested_refund, max_payout)
        decision = parsed["decision"]
        approved_refund = u256(int(parsed["approved_refund_cents"]))
        carrier_fault = u256(int(parsed["carrier_fault_score"]))
        packaging_integrity = u256(int(parsed["packaging_integrity_score"]))
        confidence = u256(int(parsed["confidence_score"]))
        reason = str(parsed["reason"])[:900]

        if decision == "APPROVED" or decision == "PARTIAL_REFUND":
            if confidence < min_confidence:
                decision = "NEEDS_REVIEW"
                approved_refund = u256(0)
            if approved_refund == u256(0):
                decision = "NEEDS_REVIEW"
            if approved_refund > requested_refund:
                approved_refund = requested_refund
            if approved_refund > max_payout:
                approved_refund = max_payout
            available = self.fund_balance - self.fund_reserved
            if approved_refund > available:
                decision = "NEEDS_REVIEW"
                approved_refund = u256(0)

        if decision != "APPROVED" and decision != "PARTIAL_REFUND":
            approved_refund = u256(0)

        self.claim_decisions[claim_id] = decision
        self.claim_approved_refunds[claim_id] = approved_refund
        self.claim_carrier_fault_scores[claim_id] = carrier_fault
        self.claim_packaging_integrity_scores[claim_id] = packaging_integrity
        self.claim_confidence_scores[claim_id] = confidence
        self.claim_ai_reports[claim_id] = reason

        if decision == "APPROVED" or decision == "PARTIAL_REFUND":
            self.fund_reserved = self.fund_reserved + approved_refund
            self.claim_statuses[claim_id] = "APPROVED"
        else:
            self.claim_statuses[claim_id] = decision
        return self.get_decision(claim_id)

    @gl.public.write
    def release_compensation(self, claim_id: u256) -> str:
        if claim_id >= self.claim_count:
            return "CLAIM_NOT_FOUND"
        if self.claim_statuses[claim_id] != "APPROVED":
            return "NOT_APPROVED"

        approved_refund = self.claim_approved_refunds[claim_id]
        if approved_refund == u256(0):
            return "ZERO_APPROVED_REFUND"
        if approved_refund > self.fund_reserved:
            return "RESERVE_MISMATCH"
        if approved_refund > self.fund_balance:
            return "INSUFFICIENT_FUND"

        self.fund_balance = self.fund_balance - approved_refund
        self.fund_reserved = self.fund_reserved - approved_refund
        self.fund_paid = self.fund_paid + approved_refund
        self.claim_statuses[claim_id] = "PAID"
        return "PAID"

    @gl.public.view
    def get_claim_count(self) -> u256:
        return self.claim_count

    @gl.public.view
    def get_fund_state(self) -> str:
        return json.dumps(
            {
                "balance": int(self.fund_balance),
                "max_payout": int(self.max_payout),
                "min_confidence": int(self.min_confidence),
                "owner": self.fund_owners[u256(0)],
                "paid": int(self.fund_paid),
                "reserved": int(self.fund_reserved),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @gl.public.view
    def get_claim(self, claim_id: u256) -> str:
        if claim_id >= self.claim_count:
            return "CLAIM_NOT_FOUND"
        return json.dumps(
            {
                "approved_refund": int(self.claim_approved_refunds[claim_id]),
                "buyer_wallet": self.claim_buyer_wallets[claim_id],
                "carrier_fault_score": int(self.claim_carrier_fault_scores[claim_id]),
                "confidence_score": int(self.claim_confidence_scores[claim_id]),
                "decision": self.claim_decisions[claim_id],
                "delivery_slip_url": self.claim_delivery_slip_urls[claim_id],
                "item_title": self.claim_item_titles[claim_id],
                "merchant_wallet": self.claim_merchant_wallets[claim_id],
                "order_id": self.claim_order_ids[claim_id],
                "order_value": int(self.claim_order_values[claim_id]),
                "packaging_integrity_score": int(self.claim_packaging_integrity_scores[claim_id]),
                "policy_url": self.claim_policy_urls[claim_id],
                "reason": self.claim_ai_reports[claim_id],
                "requested_refund": int(self.claim_requested_refunds[claim_id]),
                "status": self.claim_statuses[claim_id],
                "tracking_url": self.claim_tracking_urls[claim_id],
                "unbox_url": self.claim_unbox_urls[claim_id],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @gl.public.view
    def get_decision(self, claim_id: u256) -> str:
        if claim_id >= self.claim_count:
            return "CLAIM_NOT_FOUND"
        return json.dumps(
            {
                "approved_refund": int(self.claim_approved_refunds[claim_id]),
                "carrier_fault_score": int(self.claim_carrier_fault_scores[claim_id]),
                "confidence_score": int(self.claim_confidence_scores[claim_id]),
                "decision": self.claim_decisions[claim_id],
                "packaging_integrity_score": int(self.claim_packaging_integrity_scores[claim_id]),
                "reason": self.claim_ai_reports[claim_id],
                "status": self.claim_statuses[claim_id],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def _is_url(self, value: str) -> u256:
        if len(value) < 8:
            return u256(0)
        if value[:7] == "http://":
            return u256(1)
        if value[:8] == "https://":
            return u256(1)
        return u256(0)

    def _render_evidence(self, url: str) -> str:
        try:
            response = gl.nondet.web.render(url, media_type="html")
            return str(response)[:3500]
        except Exception:
            return "WEB_RENDER_FAILED"

    def _clamp_score(self, value: typing.Any):
        number = int(value)
        if number < 0:
            return 0
        if number > 100:
            return 100
        return number

    def _parse_review(self, raw: str, requested_refund: u256, max_payout: u256) -> typing.Any:
        try:
            data = json.loads(raw)
        except Exception:
            return {
                "approved_refund_cents": 0,
                "carrier_fault_score": 0,
                "confidence_score": 0,
                "decision": "NEEDS_REVIEW",
                "packaging_integrity_score": 0,
                "reason": "AI returned malformed JSON; human review required.",
            }

        decision = str(data.get("decision", "NEEDS_REVIEW"))
        if decision != "APPROVED" and decision != "PARTIAL_REFUND" and decision != "REJECTED":
            decision = "NEEDS_REVIEW"

        approved = int(data.get("approved_refund_cents", 0))
        if approved < 0:
            approved = 0
        if approved > int(requested_refund):
            approved = int(requested_refund)
        if approved > int(max_payout):
            approved = int(max_payout)

        return {
            "approved_refund_cents": approved,
            "carrier_fault_score": self._clamp_score(data.get("carrier_fault_score", 0)),
            "confidence_score": self._clamp_score(data.get("confidence_score", 0)),
            "decision": decision,
            "packaging_integrity_score": self._clamp_score(data.get("packaging_integrity_score", 0)),
            "reason": str(data.get("reason", "No reason provided.")),
        }
