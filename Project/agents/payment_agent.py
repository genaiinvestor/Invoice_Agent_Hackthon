# """Payment Agent for Invoice Processing"""

# # TODO: Implement agent

# import os
# import json
# import requests
# from typing import Dict, Any, Optional
# from datetime import datetime, timedelta
# import google.generativeai as genai
# from dotenv import load_dotenv

# from agents.base_agent import BaseAgent
# from state import (
#     InvoiceProcessingState, PaymentDecision, PaymentStatus,
#     RiskLevel, ValidationStatus, ProcessingStatus
# )
# from utils.logger import StructuredLogger

# load_dotenv()


# class PaymentAgent(BaseAgent):
#     """Agent responsible for payment processing decisions and execution"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _make_payment_decision(self, invoice_data, validation_result,
#                                    risk_assessment, state: InvoiceProcessingState) -> PaymentDecision:
#         pass

#     def _select_payment_method(self, amount: float) -> str:
#         pass

#     def _calculate_payment_date(self, due_date_str: Optional[str], payment_method: str) -> datetime:
#         pass

#     def _parse_date(self, date_str: str) -> Optional[datetime.date]:
#         pass

#     async def _execute_payment(self, invoice_data, payment_decision: PaymentDecision) -> Dict[str, Any]:
#         pass

#     async def _async_sleep(self, seconds: int):
#         pass

#     def _update_payment_decision(self, payment_decision: PaymentDecision,
#                                payment_result: Dict[str, Any]) -> PaymentDecision:
#         pass

#     async def _generate_payment_justification(self, invoice_data, payment_decision: PaymentDecision,
#                                             validation_result, risk_assessment) -> str:
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass

"""Payment Agent for Invoice Processing"""
 
import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
 
from agents.base_agent import BaseAgent
from state import (
    InvoiceProcessingState, PaymentDecision, PaymentStatus,
    RiskLevel, ValidationStatus, ProcessingStatus
)
from utils.logger import StructuredLogger
 
load_dotenv()
 
 
class PaymentAgent(BaseAgent):
    """Agent responsible for payment processing decisions and execution"""
 
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_name="payment_agent")
        self.logger = StructuredLogger("PaymentAgent")
        self.config = config or {}
 
        # Thresholds
        self.auto_payment_threshold = float(self.config.get("auto_payment_threshold", 5000))
        self.manual_approval_threshold = float(self.config.get("manual_approval_threshold", 25000))
 
        # API config
        self.payment_api_url = os.getenv("PAYMENT_API_URL", "http://localhost:8000/initiate_payment")
        self.payment_api_key = os.getenv("PAYMENT_API_KEY", "")
 
        # Gemini optional
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY_4")
            or os.getenv("GEMINI_API_KEY")
        )
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
            except Exception:
                pass
 
        self.retry_attempts = 3
        self.retry_delay_seconds = 2
 
       
 
        self.payment_rules = {
            # ✅ Auto payment for low risk, small amount, valid or partial match invoices
            "auto_payment": {
                "conditions": [
                    "risk_level equals low",
                    "amount less than 5000",
                    "validation_status equals valid or partial_match",
                    "vendor in approved_list"
                ],
                "action": "process_immediately"
            },
 
            # ✅ Manager approval for medium risk or partial match
            "manager_approval": {
                "conditions": [
                    "risk_level equals medium",
                    "amount between 5000 and 25000",
                    "validation_status equals partial_match"
                ],
                "action": "route_to_manager"
            },
 
            # ✅ Executive approval for high or critical risk
            "executive_approval": {
                "conditions": [
                    "risk_level is high or critical",
                    "amount 25000 or higher",
                    "validation_status equals requires_approval"
                ],
                "action": "route_to_executive"
            },
 
            # ✅ Reject for critical or fraud-heavy cases
            "reject": {
                "conditions": [
                    "risk_level equals critical",
                    "fraud_indicators greater than 3",
                    "validation_status equals invalid"
                ],
                "action": "reject_payment"
            },
        }
 
    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        if not state.invoice_data:
            self.logger.error("PaymentAgent: Missing invoice data.")
            return False
        if not state.validation_result:
            self.logger.error("PaymentAgent: Validation result missing.")
            return False
        if not state.risk_assessment:
            self.logger.error("PaymentAgent: Risk assessment missing.")
            return False
        return True
 
    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        return bool(state.payment_decision and state.payment_decision.payment_status)
   
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
            risk = state.risk_assessment
 
            decision = await self._make_payment_decision(inv, val, risk, state)
            # state.payment_decision = decision
            state.payment_decision = (
                decision.__dict__ if hasattr(decision, "__dict__") else decision
            )
            if decision.payment_status == PaymentStatus.APPROVED:
                result = await self._execute_payment(inv, decision)
                decision = self._update_payment_decision(decision, result)
                # state.payment_decision = decision
                state.payment_decision = (
                    decision.__dict__ if hasattr(decision, "__dict__") else decision
                )
            # ✅ Explicit log for visibility
            self.logger.info(
                f"PaymentAgent Output: status={decision.payment_status}, "
                f"approved_amount={decision.approved_amount}, "
                f"method={decision.payment_method}, "
                f"scheduled={decision.scheduled_date}"
            )
 
            # ✅ Audit trail
            state.log_action(
                agent_name=self.agent_name,
                action="payment_decision",
                status="completed",
                details={
                    "payment_status": str(decision.payment_status),
                    "amount": getattr(decision, "approved_amount", 0.0),
                    "method": decision.payment_method,
                },
                duration_ms=self._stop_timer(start)
            )
 
            # ✅ Mark workflow status
            state.overall_status = ProcessingStatus.COMPLETED
 
        except Exception as e:
            self.logger.error(f"PaymentAgent failed: {e}")
            state.log_action(
                agent_name=self.agent_name,
                action="payment_decision",
                status="failed",
                details={"error": str(e)},
                duration_ms=self._stop_timer(start),
                error_message=str(e)
            )
            state.overall_status = ProcessingStatus.FAILED
 
        return state
 
 
 
 
 
    # ------------------------------------------------------------------
    # Decision Logic
    # ------------------------------------------------------------------
    async def _make_payment_decision(self, invoice_data, validation_result,
                                     risk_assessment, state: InvoiceProcessingState) -> PaymentDecision:
        amount = float(invoice_data.total or 0.0)
        # risk_level = str(risk_assessment.risk_level).lower()
        # val_status = str(validation_result.validation_status).lower()
        risk_level = getattr(risk_assessment.risk_level, "value", str(risk_assessment.risk_level)).lower()
        val_status = getattr(validation_result.validation_status, "value", str(validation_result.validation_status)).lower()
 
        fraud_indicators = risk_assessment.fraud_indicators or []
        vendor = getattr(invoice_data, "customer_name", "").lower()
        approved_vendors = ["Alan Haines", "Ralph Arnett","maria zettner"]
 
        # approved_vendors = ["test customer", "acme corp", "approved vendor", "maria zettner"]
 
        # approved_vendors = ["test customer", "acme corp", "approved vendor"]
 
        # Match rules dynamically
        action = None
        for rule_name, rule_data in self.payment_rules.items():
            conditions = rule_data["conditions"]
 
            if self._match_conditions(conditions, amount, risk_level, val_status, vendor, fraud_indicators, approved_vendors):
                action = rule_data["action"]
                self.logger.info(f"Checking conditions: {conditions}")
                self.logger.info(f"Values → risk_level={risk_level}, val_status={val_status}, amount={amount}, vendor={vendor}")
 
                break
 
        payment_method = self._select_payment_method(amount)
        scheduled_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
 
        if action == "reject_payment":
            # return PaymentDecision(
            #     payment_status=PaymentStatus.REJECTED,
            #     approved_amount=0.0,
            #     transaction_id=None,
            #     payment_method=payment_method,
            #     approval_chain=[],
            #     rejection_reason="Rejected due to rule-based high risk or fraud suspicion",
            #     scheduled_date=None
            # )
            pd = PaymentDecision(
                payment_status=PaymentStatus.REJECTED,
                approved_amount=0.0,
                transaction_id=None,
                payment_method=payment_method,
                approval_chain=[],
                rejection_reason="Rejected due to rule-based high risk or fraud suspicion",
                scheduled_date=None
            )
            return pd.__dict__
        if action == "route_to_executive":
            # return PaymentDecision(
            #     payment_status=PaymentStatus.PENDING_APPROVAL,
            #     approved_amount=0.0,
            #     transaction_id=None,
            #     payment_method=payment_method,
            #     approval_chain=["finance_manager_approval", "cfo_approval"],
            #     rejection_reason=None,
            #     scheduled_date=scheduled_date
            # )
            pd = PaymentDecision(
                payment_status=PaymentStatus.PENDING_APPROVAL,
                approved_amount=0.0,
                transaction_id=None,
                payment_method=payment_method,
                approval_chain=["finance_manager_approval", "cfo_approval"],
                rejection_reason=None,
                scheduled_date=scheduled_date
            )
            return pd.__dict__
 
        if action == "route_to_manager":
            # return PaymentDecision(
            #     payment_status=PaymentStatus.PENDING_APPROVAL,
            #     approved_amount=amount,
            #     transaction_id=None,
            #     payment_method=payment_method,
            #     approval_chain=["finance_manager_approval"],
            #     rejection_reason=None,
            #     scheduled_date=scheduled_date
            # )
            pd = PaymentDecision(
                payment_status=PaymentStatus.PENDING_APPROVAL,
                approved_amount=amount,
                transaction_id=None,
                payment_method=payment_method,
                approval_chain=["finance_manager_approval"],
                rejection_reason=None,
                scheduled_date=scheduled_date
            )
            return pd.__dict__
 
        if action == "process_immediately":
            # return PaymentDecision(
            #     payment_status=PaymentStatus.APPROVED,
            #     approved_amount=amount,
            #     transaction_id=None,
            #     payment_method=payment_method,
            #     approval_chain=["system_auto_approval"],
            #     rejection_reason=None,
            #     scheduled_date=scheduled_date
            # )
            pd = PaymentDecision(
                payment_status=PaymentStatus.APPROVED,
                approved_amount=amount,
                transaction_id=None,
                payment_method=payment_method,
                approval_chain=["system_auto_approval"],
                rejection_reason=None,
                scheduled_date=scheduled_date
            )
            return pd.__dict__
 
        # Default fallback
        # return PaymentDecision(
        #     payment_status=PaymentStatus.PENDING_APPROVAL,
        #     approved_amount=amount,
        #     transaction_id=None,
        #     payment_method=payment_method,
        #     approval_chain=["finance_manager_approval"],
        #     rejection_reason=None,
        #     scheduled_date=scheduled_date
        # )
        pd = PaymentDecision(
            payment_status=PaymentStatus.PENDING_APPROVAL,
            approved_amount=amount,
            transaction_id=None,
            payment_method=payment_method,
            approval_chain=["finance_manager_approval"],
            rejection_reason=None,
            scheduled_date=scheduled_date
        )
        return pd.__dict__
   
    def _match_conditions(
        self,
        conditions,
        amount,
        risk_level,
        val_status,
        vendor,
        fraud_indicators,
        approved_vendors
    ):
        """
        Evaluates whether the provided attributes satisfy all rule conditions.
        Supports multiple acceptable values via 'or' (e.g. 'valid or partial_match').
        Logs mismatches clearly for debugging.
        """
        for cond in conditions:
            c = cond.lower().strip()
 
            # 🧩 Risk Level Checks
            if "risk_level equals" in c:
                allowed = [s.strip() for s in c.split("equals")[-1].split("or")]
                if risk_level not in allowed:
                    self.logger.info(f"❌ Risk level mismatch: expected one of {allowed}, got={risk_level}")
                    return False
 
            elif "risk_level is" in c:
                allowed = [s.strip() for s in c.split("is")[-1].split("or")]
                if risk_level not in allowed:
                    self.logger.info(f"❌ Risk level not in {allowed}, got={risk_level}")
                    return False
 
            # 🧩 Amount Rules
            elif "amount less than" in c:
                limit = float(c.split("less than")[-1].strip())
                if not amount < limit:
                    self.logger.info(f"❌ Amount {amount} >= limit {limit}")
                    return False
 
            elif "amount between" in c:
                try:
                    nums = c.replace("amount between", "").strip().split("and")
                    low, high = map(float, [n.strip() for n in nums])
                    if not (low <= amount <= high):
                        self.logger.info(f"❌ Amount {amount} not between {low}-{high}")
                        return False
                except Exception as e:
                    self.logger.error(f"Error parsing 'amount between' condition: {e}")
                    return False
 
            elif "amount" in c and "or higher" in c:
                try:
                    limit = float(c.split("amount")[1].split("or higher")[0].strip())
                    if amount < limit:
                        self.logger.info(f"❌ Amount {amount} < {limit}")
                        return False
                except Exception as e:
                    self.logger.error(f"Error parsing 'amount or higher' condition: {e}")
                    return False
 
            # 🧩 Validation Status Rules
            elif "validation_status equals" in c:
                allowed = [s.strip() for s in c.split("equals")[-1].split("or")]
                if val_status not in allowed:
                    self.logger.info(f"❌ Validation status mismatch: expected one of {allowed}, got={val_status}")
                    return False
 
            # 🧩 Fraud Indicator Count
            elif "fraud_indicators greater than" in c:
                try:
                    limit = int(c.split("greater than")[-1].strip())
                    if len(fraud_indicators) <= limit:
                        self.logger.info(f"❌ Fraud indicators {len(fraud_indicators)} <= limit {limit}")
                        return False
                except Exception as e:
                    self.logger.error(f"Error parsing 'fraud_indicators greater than': {e}")
                    return False
 
            # 🧩 Vendor Whitelist Check
            elif "vendor in approved_list" in c:
                if vendor not in approved_vendors:
                    self.logger.info(f"❌ Vendor '{vendor}' not in approved list {approved_vendors}")
                    return False
 
            else:
                self.logger.info(f"⚠️ Unknown condition format: {c}")
 
        # ✅ All conditions passed
        self.logger.info("✅ All rule conditions matched successfully.")
        return True
 
 
   
 
    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------
    def _select_payment_method(self, amount: float) -> str:
        if amount <= 2000:
            return "CARD"
        if amount <= 10000:
            return "ACH"
        return "WIRE"
 
    def _calculate_payment_date(self, due_date_str: Optional[str], payment_method: str) -> datetime:
        try:
            due_date = self._parse_date(due_date_str)
            if due_date:
                return due_date
        except Exception:
            pass
        return datetime.utcnow() + timedelta(days=1)
 
    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return None
 
    async def _execute_payment(self, invoice_data, payment_decision: PaymentDecision) -> Dict[str, Any]:
        txn_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return {"status": "success", "transaction_id": txn_id}
 
    async def _async_sleep(self, seconds: int):
        await asyncio.sleep(seconds)
 
    def _update_payment_decision(self, payment_decision: PaymentDecision,
                                 payment_result: Dict[str, Any]) -> PaymentDecision:
        if payment_result.get("status") == "success":
            payment_decision.transaction_id = payment_result["transaction_id"]
        return payment_decision.__dict__ if hasattr(payment_decision, "__dict__") else payment_decision

        # return payment_decision
 
    async def _generate_payment_justification(self, invoice_data, payment_decision: PaymentDecision,
                                              validation_result, risk_assessment) -> str:
        if not self.gemini_key:
            return f"Payment decision: {payment_decision.payment_status}. Risk: {risk_assessment.risk_level}."
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""
            Generate a short justification for the following payment:
            Invoice: {invoice_data.invoice_number}, Amount: {invoice_data.total},
            Risk Level: {risk_assessment.risk_level}, Decision: {payment_decision.payment_status}.
            """
            resp = model.generate_content(prompt)
            return resp.text.strip()
        except Exception:
            return "AI justification unavailable."
 
    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "api_url": self.payment_api_url,
            "gemini_enabled": bool(self.gemini_key)
        }
 
























