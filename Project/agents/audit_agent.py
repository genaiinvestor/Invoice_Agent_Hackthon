# """Audit Agent for Invoice Processing"""

# # TODO: Implement agent

# import os
# import json
# import pandas as pd
# from typing import Dict, Any, List, Optional
# from datetime import datetime, timedelta
# import google.generativeai as genai
# from dotenv import load_dotenv

# from agents.base_agent import BaseAgent
# from state import (
#     InvoiceProcessingState, ProcessingStatus, PaymentStatus,
#     ValidationStatus, RiskLevel
# )
# from utils.logger import StructuredLogger

# load_dotenv()


# class AuditAgent(BaseAgent):
#     """Agent responsible for audit trail generation, compliance tracking, and reporting"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def _generate_audit_record(self, state: InvoiceProcessingState) -> Dict[str, Any]:
#         pass

#     async def _perform_compliance_checks(self, state: InvoiceProcessingState,
#                                        audit_record: Dict[str, Any]) -> Dict[str, Any]:
#         pass

#     def _check_sox_compliance(self, state: InvoiceProcessingState,
#                             audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
#         pass

#     def _check_data_privacy_compliance(self, state: InvoiceProcessingState,
#                                      audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
#         pass

#     def _check_financial_controls(self, state: InvoiceProcessingState,
#                                 audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
#         pass

#     def _check_audit_trail_completeness(self, state: InvoiceProcessingState,
#                                       audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
#         pass

#     async def _generate_audit_summary(self, state: InvoiceProcessingState,
#                                     audit_record: Dict[str, Any],
#                                     compliance_results: Dict[str, Any]) -> str:
#         pass

#     async def _save_audit_records(self, state: InvoiceProcessingState,
#                                 audit_record: Dict[str, Any],
#                                 audit_summary: str,
#                                 compliance_results: Dict[str, Any]):
#         pass

#     async def _identify_reportable_events(self, state: InvoiceProcessingState,
#                                         audit_record: Dict[str, Any]) -> List[Dict[str, Any]]:
#         pass

#     async def _generate_audit_alerts(self, state: InvoiceProcessingState,
#                                    reportable_events: List[Dict[str, Any]]):
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass

"""Audit Agent for Invoice Processing"""
 
import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
 
from agents.base_agent import BaseAgent
from state import (
    InvoiceProcessingState, ProcessingStatus, PaymentStatus,
    ValidationStatus, RiskLevel
)
from utils.logger import StructuredLogger
 
load_dotenv()
 
 
class AuditAgent(BaseAgent):
    """Agent responsible for audit trail generation, compliance tracking, and reporting"""
 
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_name="audit_agent")
        self.config = config or {}
        self.logger = StructuredLogger("AuditAgent")
 
        # Storage paths
        self.audit_output_dir = os.path.join("output", "audit")
        os.makedirs(self.audit_output_dir, exist_ok=True)
 
        # Gemini model setup
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY_4")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY_1")
        )
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
            except Exception:
                pass
 
    # ----------------------------------------------------------------------
    # Preconditions / Postconditions
    # ----------------------------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        if not state.invoice_data:
            self.logger.error("AuditAgent precondition failed: invoice_data missing.")
            return False
        if not state.audit_trail:
            self.logger.warning("AuditAgent: No prior audit logs found; will generate minimal report.")
        return True
 
    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        return hasattr(state, "audit_report") and bool(state.audit_report)
 
    # ----------------------------------------------------------------------
    # Execute
    # ----------------------------------------------------------------------
    async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        start = self._start_timer()
        state.current_agent = self.agent_name
        state.overall_status = ProcessingStatus.IN_PROGRESS
 
        if not self._validate_preconditions(state):
            state.overall_status = ProcessingStatus.FAILED
            return state
 
        try:
            # Step 1: Generate full audit record
            audit_record = await self._generate_audit_record(state)
 
            # Step 2: Perform compliance checks (SOX, GDPR, etc.)
            compliance_results = await self._perform_compliance_checks(state, audit_record)
 
            # Step 3: AI summary generation
            summary_text = await self._generate_audit_summary(state, audit_record, compliance_results)
 
            # Step 4: Persist all audit files
            await self._save_audit_records(state, audit_record, summary_text, compliance_results)
 
            # Step 5: Identify reportable events
            reportable_events = await self._identify_reportable_events(state, audit_record)
 
            # Step 6: Notify if critical exceptions found
            await self._generate_audit_alerts(state, reportable_events)
 
            # Mark success
            # state.audit_report = {
            #     "audit_record": audit_record,
            #     "compliance": compliance_results,
            #     "summary": summary_text,
            #     "reportable_events": reportable_events,
            #     "status": "completed",
            # }
 
            try:
                state.audit_report = {
                    "audit_record": audit_record,
                    "compliance": compliance_results,
                    "summary": summary_text,
                    "reportable_events": reportable_events,
                    "status": "completed",
                }
            except AttributeError:
                setattr(state, "audit_report", {
                    "audit_record": audit_record,
                    "compliance": compliance_results,
                    "summary": summary_text,
                    "reportable_events": reportable_events,
                    "status": "completed",
                })
 
 
           
 
 
            state.log_action(
                agent_name=self.agent_name,
                action="generate_audit_report",
                status="completed",
                details={
                    "audit_record_id": audit_record.get("audit_id"),
                    "compliance_status": compliance_results.get("overall_status"),
                    "events_count": len(reportable_events),
                },
                duration_ms=self._stop_timer(start)
            )
 
            state.overall_status = ProcessingStatus.COMPLETED
 
        except Exception as e:
            self.logger.error(f"AuditAgent failed: {e}")
            state.log_action(
                agent_name=self.agent_name,
                action="generate_audit_report",
                status="failed",
                details={"error": str(e)},
                duration_ms=self._stop_timer(start),
                error_message=str(e)
            )
            state.overall_status = ProcessingStatus.FAILED
 
        return state
 
    # ----------------------------------------------------------------------
    # Core Audit & Compliance Logic
    # ----------------------------------------------------------------------
    async def _generate_audit_record(self, state: InvoiceProcessingState) -> Dict[str, Any]:
        audit_id = f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        escalation_data = getattr(state, "escalation_record", {}) or {}
        record = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "invoice_number": getattr(state.invoice_data, "invoice_number", "N/A"),
            "workflow_type": getattr(state, "workflow_type", "standard"),
            "processing_status": str(state.overall_status),
            "agents_executed": getattr(state, "completed_agents", []),
            "risk_level": str(getattr(state.risk_assessment, "risk_level", "unknown")),
            "payment_status": str(getattr(state.payment_decision, "payment_status", "unknown")),
           
            "escalation_status": escalation_data.get("status", "none"),
            # "escalation_status": getattr(state, "escalation_record", {}).get("status", "none"),
            "human_review": getattr(state, "human_review_required", False),
            "total_amount": getattr(state.invoice_data, "total", 0.0),
        }
        return record
 
    async def _perform_compliance_checks(self, state: InvoiceProcessingState,
                                       audit_record: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            "sox": self._check_sox_compliance(state, audit_record),
            "gdpr": self._check_data_privacy_compliance(state, audit_record),
            "financial": self._check_financial_controls(state, audit_record),
            "trail": self._check_audit_trail_completeness(state, audit_record),
        }
        violations = sum(len(v.get("violations", [])) for v in results.values())
        results["overall_status"] = "compliant" if violations == 0 else "non_compliant"
        return results
 
    def _check_sox_compliance(self, state: InvoiceProcessingState,
                            audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
        violations = []
        if not state.invoice_data.invoice_number:
            violations.append("Missing invoice number.")
        if not state.audit_trail:
            violations.append("Missing audit trail entries.")
        # if state.payment_decision and not state.payment_decision.transaction_id:
        if state.payment_decision and not state.payment_decision.get("transaction_id"):
            violations.append("Missing transaction ID in payment record.")
        return {"standard": "SOX", "violations": violations}
 
    def _check_data_privacy_compliance(self, state: InvoiceProcessingState,
                                     audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
        violations = []
        raw = getattr(state.invoice_data, "raw_text", "")
        if "@" in raw:
            violations.append("Email address detected in raw text — mask required.")
        if any(char.isdigit() for char in raw[-10:]):
            violations.append("Potential phone number in raw text — mask required.")
        return {"standard": "GDPR", "violations": violations}
 
    def _check_financial_controls(self, state: InvoiceProcessingState,
                                audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
        violations = []
        if not state.validation_result or not state.validation_result.po_found:
            violations.append("PO matching missing or failed.")
        if state.payment_decision and state.payment_decision.get("payment_status") == PaymentStatus.REJECTED:
            violations.append("Rejected payment requires manual documentation.")
        return {"standard": "Financial Controls", "violations": violations}
 
    def _check_audit_trail_completeness(self, state: InvoiceProcessingState,
                                      audit_record: Dict[str, Any]) -> Dict[str, List[str]]:
        violations = []
        if not state.audit_trail or len(state.audit_trail) < 3:
            violations.append("Insufficient audit log entries — process incomplete.")
        required_agents = {"document_agent", "validation_agent", "risk_agent"}
        executed = set(getattr(state, "completed_agents", []))
        missing_agents = required_agents - executed
        if missing_agents:
            violations.append(f"Missing execution logs for agents: {', '.join(missing_agents)}.")
        return {"standard": "Audit Completeness", "violations": violations}
 
    # ----------------------------------------------------------------------
    # AI Summary, Storage, and Alerts
    # ----------------------------------------------------------------------
    async def _generate_audit_summary(self, state: InvoiceProcessingState,
                                    audit_record: Dict[str, Any],
                                    compliance_results: Dict[str, Any]) -> str:
        """Summarize audit report in human-readable form (Gemini optional)."""
        summary = ""
        try:
            if self.gemini_key:
                model = genai.GenerativeModel(self.gemini_model)
                prompt = f"""
                Generate a short professional audit report summary.
                Include compliance status, invoice number, risk level, and final payment outcome.
 
                Audit Record:
                {json.dumps(audit_record, indent=2)}
 
                Compliance:
                {json.dumps(compliance_results, indent=2)}
                """
                resp = await asyncio.to_thread(model.generate_content, prompt)
                summary = (resp.text or "").strip()
        except Exception as e:
            self.logger.warning(f"Gemini summary failed: {e}")
 
        if not summary:
            summary = (
                f"Audit Summary for Invoice {audit_record['invoice_number']}: "
                f"Risk level {audit_record['risk_level']}, Payment {audit_record['payment_status']}. "
                f"Compliance status: {compliance_results.get('overall_status', 'unknown')}."
            )
        return summary
 
    async def _save_audit_records(self, state: InvoiceProcessingState,
                                audit_record: Dict[str, Any],
                                audit_summary: str,
                                compliance_results: Dict[str, Any]):
        """Save audit artifacts to disk for compliance retention."""
        invoice_no = audit_record["invoice_number"]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
 
        base_path = os.path.join(self.audit_output_dir, f"audit_{invoice_no}_{timestamp}")
        os.makedirs(base_path, exist_ok=True)
 
        with open(os.path.join(base_path, "audit_record.json"), "w") as f:
            json.dump(audit_record, f, indent=2)
 
        with open(os.path.join(base_path, "compliance_report.json"), "w") as f:
            json.dump(compliance_results, f, indent=2)
 
        with open(os.path.join(base_path, "audit_summary.txt"), "w") as f:
            f.write(audit_summary)
 
        self.logger.info(f"Audit data saved to {base_path}")
 
    async def _identify_reportable_events(self, state: InvoiceProcessingState,
                                        audit_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify audit items that must be reported to compliance officers."""
        events = []
        if state.payment_decision and state.payment_decision.get("payment_status") == PaymentStatus.REJECTED:
            events.append({"event": "Payment Rejected", "severity": "high"})
        if state.risk_assessment and state.risk_assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            events.append({"event": "High Risk Invoice", "severity": "critical"})
        if audit_record.get("processing_status") == ProcessingStatus.FAILED:
            events.append({"event": "Processing Failure", "severity": "critical"})
        return events
 
    async def _generate_audit_alerts(self, state: InvoiceProcessingState,
                                   reportable_events: List[Dict[str, Any]]):
        """Simulate alert generation (to compliance team)."""
        if not reportable_events:
            return
        alerts_path = os.path.join(self.audit_output_dir, "audit_alerts.log")
        with open(alerts_path, "a") as f:
            for ev in reportable_events:
                f.write(f"[{datetime.utcnow().isoformat()}] {ev['event']} ({ev['severity']})\n")
        self.logger.warning(f"Audit alerts generated for {len(reportable_events)} event(s).")
 
    # ----------------------------------------------------------------------
    # Health Check
    # ----------------------------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "gemini_enabled": bool(self.gemini_key),
            "audit_output_dir": self.audit_output_dir,
        }
 
 
















