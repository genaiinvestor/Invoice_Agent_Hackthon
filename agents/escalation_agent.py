# """Escalation Agent for Invoice Processing"""

# # TODO: Implement agent

# import os
# import json
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from typing import Dict, Any, List, Optional
# from datetime import datetime, timedelta
# import google.generativeai as genai
# from dotenv import load_dotenv

# from agents.base_agent import BaseAgent
# from state import (
#     InvoiceProcessingState, ProcessingStatus, PaymentStatus,
#     RiskLevel, ValidationStatus
# )
# from utils.logger import StructuredLogger

# load_dotenv()


# class EscalationAgent(BaseAgent):
#     """Agent responsible for escalation management and human-in-the-loop workflows"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     def _determine_escalation_type(self, state: InvoiceProcessingState) -> str:
#         pass

#     def _calculate_priority_level(self, state: InvoiceProcessingState) -> str:
#         pass

#     def _route_to_approver(self, state: InvoiceProcessingState,
#                           escalation_type: str, priority_level: str) -> Dict[str, Any]:
#         pass

#     def _parse_date(self, date_str: str) -> Optional[datetime.date]:
#         pass

#     async def _generate_escalation_summary(self, state: InvoiceProcessingState,
#                                          escalation_type: str, approver_info: Dict[str, Any]) -> str:
#         pass

#     async def _create_escalation_record(self, state: InvoiceProcessingState,
#                                       escalation_type: str, priority_level: str,
#                                       approver_info: Dict[str, Any], summary: str) -> Dict[str, Any]:
#         pass

#     async def _send_escalation_notifications(self, state: InvoiceProcessingState,
#                                            escalation_record: Dict[str, Any],
#                                            approver_info: Dict[str, Any]) -> Dict[str, Any]:
#         pass

#     def _send_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
#         pass

#     async def _setup_sla_monitoring(self, state: InvoiceProcessingState,
#                                   escalation_record: Dict[str, Any], priority_level: str):
#         pass

#     async def resolve_escalation(self, escalation_id: str, resolution: str,
#                                resolver: str) -> Dict[str, Any]:
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass



"""Escalation Agent for Invoice Processing"""

import os
import json
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from state import (
    InvoiceProcessingState, ProcessingStatus, PaymentStatus,
    RiskLevel, ValidationStatus
)
from utils.logger import StructuredLogger

load_dotenv()


class EscalationAgent(BaseAgent):
    """Agent responsible for escalation management and human-in-the-loop workflows."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_name="escalation_agent")
        self.config = config or {}
        self.logger = StructuredLogger("EscalationAgent")

        # SMTP & Notification setup
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER", "no-reply@invoicesystem.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.manager_email = os.getenv("MANAGER_EMAIL", "manager@enterprise.com")
        self.executive_email = os.getenv("EXECUTIVE_EMAIL", "cfo@enterprise.com")
        self.fraud_email = os.getenv("FRAUD_EMAIL", "fraud@enterprise.com")
        self.procurement_email = os.getenv("PROCUREMENT_EMAIL", "procurement@enterprise.com")

        # Gemini optional setup
        self.gemini_key = os.getenv("GEMINI_API_KEY_5") or os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
            except Exception:
                pass

        # SLA configurations
        self.sla_hours = {"low": 24, "medium": 12, "high": 6, "critical": 3}

    # ------------------------------------------------------------
    # Preconditions
    # ------------------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        if not state.risk_assessment:
            self.logger.error("Escalation precondition failed: missing risk assessment.")
            return False
        return True

    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        return hasattr(state, "escalation_record") and state.escalation_record is not None

    # ------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------
    async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        start = self._start_timer()
        state.current_agent = "escalation_agent"
        state.overall_status = ProcessingStatus.IN_PROGRESS

        if not self._validate_preconditions(state):
            state.overall_status = ProcessingStatus.FAILED
            return state

        try:
            escalation_type = self._determine_escalation_type(state)
            priority_level = self._calculate_priority_level(state)
            approver_info = self._route_to_approver(state, escalation_type, priority_level)
            summary = await self._generate_escalation_summary(state, escalation_type, approver_info)
            record = await self._create_escalation_record(state, escalation_type, priority_level, approver_info, summary)

            # await self._send_escalation_notifications(state, record, approver_info)
            # await self._setup_sla_monitoring(state, record, priority_level)

            notify_result = await self._send_escalation_notifications(state, record, approver_info)
            await self._setup_sla_monitoring(state, record, priority_level)

            # 🧩 Attach notification info to state for Streamlit toast
            state.notification_info = {
                "status": notify_result.get("status"),
                "recipient": notify_result.get("recipient"),
                "escalation_type": escalation_type,
                "invoice": getattr(state.invoice_data, "invoice_number", "N/A"),
            }

            # Log structured output for dashboard
            output_json = {
                "escalation_record": record,
                "overall_status": state.overall_status.value,
                "current_agent": "escalation_agent",
            }

            self.logger.info(f"EscalationAgent Output: {json.dumps(output_json, indent=2)}")

            # Log audit trail
            state.log_action(
                agent_name="escalation_agent",
                action="initiate_escalation",
                status="completed",
                details=record,
                duration_ms=self._stop_timer(start),
            )

            state.escalation_record = record
            await self._save_escalation_files(record)

            state.overall_status = ProcessingStatus.IN_PROGRESS

        except Exception as e:
            self.logger.error(f"EscalationAgent failed: {e}")
            state.log_action(
                agent_name="escalation_agent",
                action="initiate_escalation",
                status="failed",
                details={"error": str(e)},
                duration_ms=self._stop_timer(start),
                error_message=str(e)
            )
            state.overall_status = ProcessingStatus.FAILED

        return state

    # ------------------------------------------------------------
    # Escalation logic
    # ------------------------------------------------------------
    def _determine_escalation_type(self, state: InvoiceProcessingState) -> str:
        """Determine the type of escalation based on risk, validation, and fraud."""
        risk = state.risk_assessment
        val = state.validation_result
        inv = state.invoice_data

        if risk.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return "high_risk"
        if val and val.validation_status == ValidationStatus.REQUIRES_APPROVAL:
            return "validation_failure"
        if inv and float(inv.total or 0) > 25000:
            return "high_value"
        if len(risk.fraud_indicators or []) > 3:
            return "fraud_suspicion"
        return "new_vendor"

    def _calculate_priority_level(self, state: InvoiceProcessingState) -> str:
        rl = state.risk_assessment.risk_level
        if rl == RiskLevel.CRITICAL:
            return "critical"
        if rl == RiskLevel.HIGH:
            return "high"
        if rl == RiskLevel.MEDIUM:
            return "medium"
        return "low"

    def _route_to_approver(self, state: InvoiceProcessingState,
                           escalation_type: str, priority_level: str) -> Dict[str, Any]:
        """Routes escalation based on its type."""
        if escalation_type == "high_risk":
            return {"name": "Risk Manager", "email": self.manager_email}
        if escalation_type == "validation_failure":
            return {"name": "Finance Manager", "email": self.manager_email}
        if escalation_type == "high_value":
            return {"name": "CFO", "email": self.executive_email}
        if escalation_type == "fraud_suspicion":
            return {"name": "Fraud Team Lead", "email": self.fraud_email}
        return {"name": "Procurement Lead", "email": self.procurement_email}

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        if not date_str:
            return None
        fmts = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]
        for f in fmts:
            try:
                return datetime.strptime(date_str.strip(), f).date()
            except Exception:
                continue
        return None

    # ------------------------------------------------------------
    # Escalation record creation
    # ------------------------------------------------------------
    async def _generate_escalation_summary(self, state: InvoiceProcessingState,
                                           escalation_type: str, approver_info: Dict[str, Any]) -> str:
        """Generate concise escalation summary (Gemini optional)."""
        try:
            if self.gemini_key:
                model = genai.GenerativeModel(self.gemini_model)
                prompt = f"""
                Create a professional escalation summary (max 4 bullet points)
                explaining reason, risk level, total amount, and next approver.

                Escalation Type: {escalation_type}
                Risk Level: {getattr(state.risk_assessment, "risk_level", "")}
                Amount: {getattr(state.invoice_data, "total", "")}
                Invoice: {getattr(state.invoice_data, "invoice_number", "")}
                Approver: {approver_info.get("name")}
                """
                resp = await asyncio.to_thread(model.generate_content, prompt)
                return (resp.text or "").strip()
        except Exception:
            pass

        return (
            f"Escalation triggered for invoice {getattr(state.invoice_data, 'invoice_number', 'N/A')} "
            f"due to {escalation_type}. Approver: {approver_info.get('name')}."
        )

    async def _create_escalation_record(self, state: InvoiceProcessingState,
                                        escalation_type: str, priority_level: str,
                                        approver_info: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Create structured escalation record."""
        esc_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        record = {
            "escalation_id": esc_id,
            "timestamp": datetime.utcnow().isoformat(),
            "invoice_number": getattr(state.invoice_data, "invoice_number", "N/A"),
            "type": escalation_type,
            "priority": priority_level,
            "approver": approver_info,
            "summary": summary,
            "status": "pending_review",
        }
        state.escalation_record = record
        state.human_review_required = True
        state.overall_status = ProcessingStatus.IN_PROGRESS

        return record

    async def _send_escalation_notifications(self, state: InvoiceProcessingState,
                                             escalation_record: Dict[str, Any],
                                             approver_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send email or simulate notification."""
        subject = f"[Escalation] Invoice {escalation_record['invoice_number']} - {escalation_record['type'].title()}"
        body = (
            f"Dear {approver_info.get('name')},\n\n"
            f"An escalation has been triggered for invoice {escalation_record['invoice_number']}.\n\n"
            f"Summary:\n{escalation_record['summary']}\n\n"
            f"Priority: {escalation_record['priority'].upper()}\n\n"
            f"Please review within SLA: {self.sla_hours.get(escalation_record['priority'], 24)} hours.\n\n"
            f"Regards,\nInvoice Processing System"
        )

        try:
            if not self.smtp_password:
                self.logger.warning("SMTP password missing — simulating email send.")
                return {"status": "simulated", "recipient": approver_info.get("email")}

            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = approver_info.get("email")
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Escalation email sent to {approver_info.get('email')}")
            return {"status": "sent", "recipient": approver_info.get("email")}
        except Exception as e:
            self.logger.error(f"Email send failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _setup_sla_monitoring(self, state: InvoiceProcessingState,
                                    record: Dict[str, Any], priority_level: str):
        """Simulate SLA setup."""
        hours = self.sla_hours.get(priority_level, 24)
        due = datetime.utcnow() + timedelta(hours=hours)
        record["sla_due"] = due.isoformat()
        record["sla_status"] = "active"
        await asyncio.sleep(0.05)
        return record
    
 

    async def _save_escalation_files(self, record: Dict[str, Any]):
        """Save escalation record and summaries into output/escalations."""
        import pandas as pd

        # 1️⃣ Ensure output directory exists
        base_dir = os.path.join("output", "escalations")
        os.makedirs(base_dir, exist_ok=True)

        # 2️⃣ Save escalation record as a JSON file
        filename = f"escalation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(base_dir, filename)
        with open(path, "w") as f:
            json.dump(record, f, indent=2)

        # 3️⃣ Append to or create pending_approvals.csv
        csv_path = os.path.join(base_dir, "pending_approvals.csv")
        df_new = pd.DataFrame([{
            "escalation_id": record["escalation_id"],
            "invoice_number": record["invoice_number"],
            "priority": record["priority"],
            "approver": record["approver"]["name"],
            "status": record["status"],
            "sla_due": record.get("sla_due"),
        }])

        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.to_csv(csv_path, index=False)

        # 4️⃣ Maintain an empty SLA violations tracker if not present
        sla_path = os.path.join(base_dir, "sla_violations.json")
        if not os.path.exists(sla_path):
            with open(sla_path, "w") as f:
                json.dump([], f)

    async def resolve_escalation(self, escalation_id: str, resolution: str,
                                 resolver: str) -> Dict[str, Any]:
        record = {
            "escalation_id": escalation_id,
            "resolved_by": resolver,
            "resolution": resolution,
            "resolved_at": datetime.utcnow().isoformat(),
            "status": "resolved",
        }
        self.logger.info(f"Escalation {escalation_id} resolved by {resolver}: {resolution}")
        return record

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "smtp_configured": bool(self.smtp_password),
            "gemini_enabled": bool(self.gemini_key),
            "sla_hours": self.sla_hours,
        }


