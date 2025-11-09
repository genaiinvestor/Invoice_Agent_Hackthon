# """Risk Assessment Agent for Invoice Processing"""

# # TODO: Implement agent

# import os
# import json
# import re
# from typing import Dict, Any, List
# import google.generativeai as genai
# from dotenv import load_dotenv
# import numpy as np
# from datetime import datetime, timedelta

# from agents.base_agent import BaseAgent
# from state import (
#     InvoiceProcessingState, RiskAssessment, RiskLevel,
#     ValidationStatus, ProcessingStatus
# )
# from utils.logger import StructuredLogger

# load_dotenv()


# class RiskAgent(BaseAgent):
#     """Agent responsible for risk assessment, fraud detection, and compliance checking"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _calculate_base_risk_score(self, invoice_data, validation_result) -> float:
#         pass

#     def _calculate_due_date_risk(self, due_date_str: str) -> float:
#         pass

#     def _parse_date(self, date_str: str) -> datetime.date:
#         pass

#     async def _detect_fraud_indicators(self, invoice_data, validation_result) -> List[str]:
#         pass

#     async def _check_compliance(self, invoice_data, state: InvoiceProcessingState) -> List[str]:
#         pass

#     async def _ai_risk_assessment(self, invoice_data, validation_result, fraud_indicators: List[str]) -> Dict[str, Any]:
#         pass

#     def _clean_json_response(self, text: str) -> str:
#         pass

#     def _combine_risk_factors(self, base_score: float, fraud_indicators: List[str],
#                             compliance_issues: List[str], ai_assessment: Dict[str, Any]) -> float:
#         pass

#     def _determine_risk_level(self, risk_score: float) -> RiskLevel:
#         pass

#     def _generate_recommendation(self, risk_level: RiskLevel, fraud_indicators: List[str],
#                                compliance_issues: List[str], validation_result) -> Dict[str, Any]:
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass


"""Risk Assessment Agent for Invoice Processing"""

# Implemented agent

import os
import json
import re
from typing import Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

from agents.base_agent import BaseAgent
from state import (
    InvoiceProcessingState, RiskAssessment, RiskLevel,
    ValidationStatus, ProcessingStatus
)
from utils.logger import StructuredLogger

load_dotenv()


class RiskAgent(BaseAgent):
    """Agent responsible for risk assessment, fraud detection, and compliance checking"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_name="risk_agent")
        self.config = config or {}
        self.logger = StructuredLogger("RiskAgent")

        # Gemini config
        self.api_key = (
            os.getenv("GEMINI_API_KEY_3")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY_1")
        )
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if self.api_key:
            genai.configure(api_key=self.api_key)

        # Thresholds from config (with sensible defaults)
        thresholds = self.config.get("risk_thresholds", {})
        self.low_th = float(thresholds.get("low", 0.3))
        self.med_th = float(thresholds.get("medium", 0.6))
        self.high_th = float(thresholds.get("high", 0.8))
        self.critical_th = float(thresholds.get("critical", 0.9))

        self.amount_tolerance = float(self.config.get("amount_tolerance", 0.05))
        self.high_value_threshold = float(self.config.get("high_value_threshold", 25000))
        self.unusual_amount_multiplier = float(self.config.get("unusual_amount_multiplier", 3.0))

        self.fraud_detection_enabled = bool(self.config.get("fraud_detection_enabled", True))
        self.compliance_checks = self.config.get("compliance_checks", ["SOX", "GDPR"])

    # -----------------------------------------------------
    # Preconditions / Postconditions
    # -----------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        if not state.invoice_data:
            self.logger.error("RiskAgent precondition failed: invoice_data missing.")
            return False
        if not state.validation_result:
            self.logger.error("RiskAgent precondition failed: validation_result missing.")
            return False
        return True

    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        return bool(state.risk_assessment and state.risk_assessment.risk_level is not None)

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------
    # async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
    #     start = self._start_timer()
    #     state.current_agent = self.agent_name
    #     state.overall_status = ProcessingStatus.IN_PROGRESS

    #     if not self._validate_preconditions(state):
    #         state.overall_status = ProcessingStatus.FAILED
    #         return state

    #     try:
    #         inv = state.invoice_data
    #         val = state.validation_result

    #         # 1) Fraud indicators (rule-based)
    #         fraud_indicators = await self._detect_fraud_indicators(inv, val)

    #         # 2) Compliance issues (SOX/GDPR)
    #         compliance_issues = await self._check_compliance(inv, state)

    #         # 3) Base risk score (deterministic rules)
    #         base_score = await self._calculate_base_risk_score(inv, val)

    #         # 4) AI assist (optional / best-effort)
    #         ai_assessment = await self._ai_risk_assessment(inv, val, fraud_indicators)

    #         # 5) Combine all
    #         risk_score = self._combine_risk_factors(base_score, fraud_indicators, compliance_issues, ai_assessment)
    #         risk_level = self._determine_risk_level(risk_score)

    #         # 6) Recommendation
    #         rec = self._generate_recommendation(risk_level, fraud_indicators, compliance_issues, val)

    #         state.risk_assessment = RiskAssessment(
    #             risk_level=risk_level,
    #             risk_score=round(min(max(risk_score, 0.0), 1.0), 2),
    #             fraud_indicators=fraud_indicators,
    #             compliance_issues=compliance_issues,
    #             recommendation=rec.get("recommendation"),
    #             reason=rec.get("reason"),
    #             requires_human_review=rec.get("requires_human_review", False)
    #         )

    #         state.log_action(
    #             agent_name=self.agent_name,
    #             action="risk_assessment",
    #             status="completed",
    #             details={
    #                 "risk_level": state.risk_assessment.risk_level,
    #                 "risk_score": state.risk_assessment.risk_score,
    #                 "fraud_indicators": state.risk_assessment.fraud_indicators,
    #                 "compliance_issues": state.risk_assessment.compliance_issues,
    #                 "recommendation": state.risk_assessment.recommendation
    #             },
    #             duration_ms=self._stop_timer(start)
    #         )
    #         state.overall_status = ProcessingStatus.IN_PROGRESS

    #     except Exception as e:
    #         self.logger.error(f"Risk assessment failed: {e}")
    #         state.log_action(
    #             agent_name=self.agent_name,
    #             action="risk_assessment",
    #             status="failed",
    #             details={"error": str(e)},
    #             duration_ms=self._stop_timer(start),
    #             error_message=str(e)
    #         )
    #         state.overall_status = ProcessingStatus.FAILED

    #     return state

    async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        start = self._start_timer()
        state.current_agent = self.agent_name
        state.overall_status = ProcessingStatus.IN_PROGRESS

        if not self._validate_preconditions(state):
            state.overall_status = ProcessingStatus.FAILED
            return state

        try:
            inv = state.invoice_data
            val = state.validation_result

            # 1️⃣ Fraud indicators (rule-based)
            fraud_indicators = await self._detect_fraud_indicators(inv, val)

            # 2️⃣ Compliance issues (SOX/GDPR)
            compliance_issues = await self._check_compliance(inv, state)

            # 3️⃣ Base risk score (deterministic rules)
            base_score = await self._calculate_base_risk_score(inv, val)

            # 4️⃣ AI assist (optional)
            ai_assessment = await self._ai_risk_assessment(inv, val, fraud_indicators)

            # 5️⃣ Combine all factors
            risk_score = self._combine_risk_factors(
                base_score, fraud_indicators, compliance_issues, ai_assessment
            )
            risk_level = self._determine_risk_level(risk_score)

            # 6️⃣ Recommendation & reason
            recommendation_data = self._generate_recommendation(
                risk_level, fraud_indicators, compliance_issues, val
            )

            # 7️⃣ Build RiskAssessment object
            risk_assessment = RiskAssessment(
                risk_level=risk_level,
                risk_score=round(min(max(risk_score, 0.0), 1.0), 2),
                fraud_indicators=fraud_indicators,
                compliance_issues=compliance_issues,
                recommendation=recommendation_data.get("recommendation"),
                reason=recommendation_data.get("reason"),
                requires_human_review=recommendation_data.get("requires_human_review", False),
            )

            state.risk_assessment = risk_assessment
            state.overall_status = ProcessingStatus.IN_PROGRESS

            # 8️⃣ Log structured output
            output_json = {
                "risk_assessment": {
                    "risk_level": risk_assessment.risk_level.value,
                    "risk_score": risk_assessment.risk_score,
                    "fraud_indicators": risk_assessment.fraud_indicators,
                    "compliance_issues": risk_assessment.compliance_issues,
                    "recommendation": risk_assessment.recommendation,
                    "reason": risk_assessment.reason,
                    "requires_human_review": risk_assessment.requires_human_review,
                },
                "overall_status": state.overall_status.value,
                "current_agent": self.agent_name,
            }

            # 9️⃣ Log for visibility
            self.logger.info(f"RiskAgent Output: {json.dumps(output_json, indent=2)}")

            # 10️⃣ Audit trail entry
            state.log_action(
                agent_name=self.agent_name,
                action="risk_assessment",
                status="completed",
                details=output_json["risk_assessment"],
                duration_ms=self._stop_timer(start),
            )

        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            state.log_action(
                agent_name=self.agent_name,
                action="risk_assessment",
                status="failed",
                details={"error": str(e)},
                duration_ms=self._stop_timer(start),
                error_message=str(e),
            )
            state.overall_status = ProcessingStatus.FAILED

        return state


    # -----------------------------------------------------
    # Base risk score (rule-based)
    # -----------------------------------------------------
    async def _calculate_base_risk_score(self, invoice_data, validation_result) -> float:
        score = 0.0
        total = float(invoice_data.total or 0.0)
        expected = float(validation_result.expected_amount or 0.0)

        # Missing PO (critical signal)
        if not validation_result.po_found or validation_result.validation_status == ValidationStatus.MISSING_PO:
            score += 0.40

        # Amount discrepancy (beyond tolerance)
        if expected > 0:
            diff_ratio = abs(expected - total) / (expected or 1.0)
            if diff_ratio > self.amount_tolerance:
                score += 0.30

        # Unusual amount (heuristic — no history provided)
        anchor = max(1.0, self.high_value_threshold / 5.0)
        if total >= self.unusual_amount_multiplier * anchor:
            score += 0.25

        # Due date risk (overdue or near due)
        score += self._calculate_due_date_risk(invoice_data.due_date or "")

        return min(max(score, 0.0), 1.0)

    def _calculate_due_date_risk(self, due_date_str: str) -> float:
        if not due_date_str:
            return 0.0
        try:
            d = self._parse_date(due_date_str)
            today = datetime.utcnow().date()
            if d < today:
                return 0.10  # overdue bump
            if (d - today).days <= 2:
                return 0.05  # urgent bump
        except Exception:
            return 0.0
        return 0.0

    def _parse_date(self, date_str: str):
        fmts = [
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%b %d %Y", "%b %d, %Y", "%d %b %Y", "%d %b, %Y",
            "%Y/%m/%d"
        ]
        s = (date_str or "").strip()
        for f in fmts:
            try:
                return datetime.strptime(s, f).date()
            except Exception:
                continue
        # relaxed fallback yyyy-mm or yyyy/mm
        m = re.search(r"(\d{4})[-/](\d{1,2})(?:[-/](\d{1,2}))?", s)
        if m:
            y = int(m.group(1)); mo = int(m.group(2)); d = int(m.group(3) or 28)
            return datetime(y, mo, d).date()
        raise ValueError(f"Unrecognized date format: {date_str}")

    # -----------------------------------------------------
    # Fraud indicators (rule-based)
    # -----------------------------------------------------
    async def _detect_fraud_indicators(self, invoice_data, validation_result) -> List[str]:
        indicators: List[str] = []

        total = float(invoice_data.total or 0.0)
        expected = float(validation_result.expected_amount or 0.0)
        if expected > 0:
            diff_ratio = abs(expected - total) / (expected or 1.0)
            if diff_ratio > self.amount_tolerance:
                indicators.append("Amount discrepancy detected")

        # Discount without PO basis
        if (getattr(invoice_data, "discount", 0) or 0) > 0:
            indicators.append("Discount not in original PO")

        # Missing PO
        if not validation_result.po_found or validation_result.validation_status == ValidationStatus.MISSING_PO:
            indicators.append("Missing purchase order")

        # Line-level mismatches from discrepancies
        for d in (validation_result.discrepancies or []):
            low = d.lower()
            if "quantity mismatch" in low:
                indicators.append("Quantity mismatch")
            if "rate mismatch" in low or "rate mismatch beyond tolerance" in low:
                indicators.append("Rate mismatch")
            if "item name mismatch" in low:
                indicators.append("Item mismatch")

        # New vendor heuristic (no vendor master provided)
        if invoice_data.customer_name and "new" in invoice_data.customer_name.lower():
            indicators.append("First-time vendor")

        # De-duplicate while preserving order
        seen = set()
        result = []
        for i in indicators:
            if i not in seen:
                result.append(i)
                seen.add(i)
        return result

    # -----------------------------------------------------
    # Compliance checks (SOX/GDPR-lite)
    # -----------------------------------------------------
    async def _check_compliance(self, invoice_data, state: InvoiceProcessingState) -> List[str]:
        issues: List[str] = []
        checks = [c.upper() for c in (self.compliance_checks or [])]

        if "SOX" in checks:
            if not invoice_data.invoice_number:
                issues.append("SOX: Missing invoice number")
            if invoice_data.total is None:
                issues.append("SOX: Missing total amount")
            if not state.audit_trail:
                issues.append("SOX: Audit trail not initialized")

        if "GDPR" in checks:
            raw = (invoice_data.raw_text or "")
            if not invoice_data.customer_name:
                issues.append("GDPR: Missing customer identifier")
            if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw):
                issues.append("GDPR: Raw text contains email addresses; mask before persistence")
            if re.search(r"\b\d{10}\b", raw):
                issues.append("GDPR: Raw text may contain phone numbers; mask before persistence")

        return issues

    # -----------------------------------------------------
    # Gemini assist (best-effort)
    # -----------------------------------------------------
    async def _ai_risk_assessment(self, invoice_data, validation_result, fraud_indicators: List[str]) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        try:
            prompt = f"""
            You are an AP risk analyst. Given invoice details and validation findings,
            respond with compact JSON: {{"risk_hint": "low|medium|high|critical", "notes": "short reason"}}.
            No prose, JSON only.

            Invoice:
            {json.dumps({
                "invoice_number": invoice_data.invoice_number,
                "order_id": invoice_data.order_id,
                "customer_name": invoice_data.customer_name,
                "total": invoice_data.total,
                "discount": invoice_data.discount,
                "due_date": invoice_data.due_date
            }, default=str)}

            Validation:
            {json.dumps({
                "po_found": validation_result.po_found,
                "status": str(validation_result.validation_status),
                "discrepancies": validation_result.discrepancies,
                "expected_amount": validation_result.expected_amount
            }, default=str)}

            Fraud indicators: {fraud_indicators}
            """

            model = genai.GenerativeModel(self.model_name)
            response = await asyncio.to_thread(model.generate_content, prompt)
            text = (response.text or "{}").strip()
            json_text = self._clean_json_response(text)
            data = json.loads(json_text)
            hint = (data.get("risk_hint") or "").lower().strip()
            if hint not in {"low", "medium", "high", "critical"}:
                data["risk_hint"] = ""
            return data

        except Exception as e:
            self.logger.warning(f"AI risk assist failed: {e}")
            return {}

    def _clean_json_response(self, text: str) -> str:
        # Strip code fences and pick first JSON object
        t = text
        if t.startswith("```"):
            t = t.strip("`")
        m = re.search(r"\{.*\}", t, flags=re.DOTALL)
        return m.group(0) if m else "{}"

    # -----------------------------------------------------
    # Combine risk factors
    # -----------------------------------------------------
    def _combine_risk_factors(
        self,
        base_score: float,
        fraud_indicators: List[str],
        compliance_issues: List[str],
        ai_assessment: Dict[str, Any]
    ) -> float:
        score = base_score

        if self.fraud_detection_enabled:
            score += min(0.05 * len(fraud_indicators), 0.20)  # cap +0.20

        score += min(0.05 * len(compliance_issues), 0.15)  # cap +0.15

        hint = (ai_assessment.get("risk_hint") or "").lower()
        if hint == "high":
            score = max(score, self.high_th + 0.05)
        elif hint == "critical":
            score = max(score, self.critical_th)
        elif hint == "medium":
            score = max(score, self.med_th - 0.05)
        elif hint == "low":
            score = min(score, (self.low_th + self.med_th) / 2)

        return min(max(score, 0.0), 1.0)

    # -----------------------------------------------------
    # Level mapping
    # -----------------------------------------------------
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        if risk_score >= self.critical_th:
            return RiskLevel.CRITICAL
        if risk_score >= self.high_th:
            return RiskLevel.HIGH
        if risk_score >= self.med_th:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    # -----------------------------------------------------
    # Recommendation
    # -----------------------------------------------------
    def _generate_recommendation(
        self,
        risk_level: RiskLevel,
        fraud_indicators: List[str],
        compliance_issues: List[str],
        validation_result
    ) -> Dict[str, Any]:
        reasons = [*fraud_indicators, *compliance_issues]
        reason_text = "; ".join(reasons) if reasons else None

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return {
                "recommendation": "escalate",
                "reason": reason_text or "High risk per policy.",
                "requires_human_review": True
            }

        if risk_level == RiskLevel.MEDIUM:
            if validation_result.validation_status in (
                ValidationStatus.REQUIRES_APPROVAL,
                ValidationStatus.MISSING_PO,
            ):
                return {
                    "recommendation": "escalate",
                    "reason": reason_text or "Medium risk with validation concerns.",
                    "requires_human_review": True
                }
            return {
                "recommendation": "proceed_with_caution",
                "reason": reason_text or "Medium risk; proceed with manager approval.",
                "requires_human_review": False
            }

        return {
            "recommendation": "proceed",
            "reason": "Low risk based on analysis.",
            "requires_human_review": False
        }

    # -----------------------------------------------------
    # Health check
    # -----------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "model": self.model_name,
            "api_key_loaded": bool(self.api_key),
            "thresholds": {
                "low": self.low_th,
                "medium": self.med_th,
                "high": self.high_th,
                "critical": self.critical_th
            }
        }

