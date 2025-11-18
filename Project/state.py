# """State models and enumerations"""
# # TODO: Define state models

# from typing import Dict, List, Optional, Any, Literal
# from pydantic import BaseModel, Field
# from datetime import datetime
# from enum import Enum


# class ProcessingStatus(str, Enum):
#     PENDING = "pending"
#     IN_PROGRESS = "in_progress"
#     ESCALATED = "escalated"
#     COMPLETED = "completed"
#     FAILED = "failed"

   


# class ValidationStatus(str, Enum):
#     VALID = "valid"
#     PARTIAL_MATCH = "partial_match"
#     INVALID = "invalid"
#     MISSING_PO = "missing_po"
#     REQUIRES_APPROVAL ="requires_approval"
    
#     # pass


# class RiskLevel(str, Enum):
#     LOW = "low"
#     MEDIUM = "medium"
#     HIGH = "high"
#     CRITICAL = "critical"
#     # pass


# class PaymentStatus(str, Enum):
#     APPROVED = "approved"
#     REJECTED = "rejected"
#     SCHEDULED = "scheduled"
#     PENDING_APPROVAL = "pending_approval"
#     # pass


# class ItemDetail(BaseModel):
#     item_name:Optional[str] = None
#     quanity:Optional[int] = None
#     rate:Optional[float] = None
#     amount:Optional[float] = None
#     category:Optional[str] = None
#     # pass


# class InvoiceData(BaseModel):
#     invoice_number:Optional[str] = None
#     order_id:Optional[str] = None
#     customer_name:Optional[str] = None
#     due_date:Optional[str] = None
#     ship_to:Optional[str] = None
#     ship_mode:Optional[str] = None
#     subtotal:Optional[float] = None
#     discount:Optional[float] = None
#     shipping_cost:Optional[float] = None
#     total:Optional[float] = None
#     item_details:Optional[List[ItemDetail]] = []
#     extraction_confidence:Optional[float] = None
#     raw_text:Optional[str]=None
#     # pass


# class ValidationResult(BaseModel):
#     po_found:Optional[bool] = False
#     quanity_match:Optional[bool] = None
#     rate_match:Optional[bool] = None
#     amount_match:Optional[bool] = None
#     validation_status:Optional[ValidationStatus] = None
#     validation_result:Optional[str] = None
#     discrepancies:Optional[List[str]] = []
#     confidence_score:Optional[float] = None
#     expected_amount:Optional[float] = None
#     po_data:Optional[Dict[str,Any]] = None

#     # pass


# class RiskAssessment(BaseModel):
#     risk_level:Optional[RiskLevel] = None
#     risk_score:Optional[float] = None
#     fraud_indicators:Optional[List[str]] = []
#     compliance_issues:Optional[List[str]] = []
#     recommendation:Optional[str] = None
#     reason:Optional[str] = None
#     requires_human_review:Optional[bool] = False
#     # pass


# class PaymentDecision(BaseModel):
#     pass


# class AuditTrail(BaseModel):
#     pass


# class AgentMetrics(BaseModel):
#     pass


# class InvoiceProcessingState(BaseModel):
#     pass


# class WorkflowConfig(BaseModel):
#     pass


# WORKFLOW_CONFIGS = {}


"""State models and enumerations"""
 
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import uuid4
 
 
# ============================================================
# ENUMERATIONS
# ============================================================
 
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "PAUSED"
 
 
class ValidationStatus(str, Enum):
    VALID = "valid"
    PARTIAL_MATCH = "partial_match"
    INVALID = "invalid"
    MISSING_PO = "missing_po"
    REQUIRES_APPROVAL = "requires_approval"
 
 
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
 
 
class PaymentStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PENDING_APPROVAL = "pending_approval"
 
 
# ============================================================
# CORE DATA MODELS
# ============================================================
 
class ItemDetail(BaseModel):
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    rate: Optional[float] = None
    amount: Optional[float] = None
    category: Optional[str] = None
 
 
class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    due_date: Optional[str] = None
    ship_to: Optional[str] = None
    ship_mode: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    shipping_cost: Optional[float] = None
    total: Optional[float] = None
    item_details: Optional[List[ItemDetail]] = []
    extraction_confidence: Optional[float] = None
    raw_text: Optional[str] = None
    decision_record: Optional[dict] = None
    file_name:Optional[str] = None
    payment_decision: Optional[dict] = None
 
 
class ValidationResult(BaseModel):
    po_found: Optional[bool] = False
    quantity_match: Optional[bool] = None
    rate_match: Optional[bool] = None
    amount_match: Optional[bool] = None
    validation_status: Optional[ValidationStatus] = None
    validation_result: Optional[str] = None
    discrepancies: Optional[List[str]] = []
    confidence_score: Optional[float] = None
    expected_amount: Optional[float] = None
    po_data: Optional[Dict[str, Any]] = None
 
 
class RiskAssessment(BaseModel):
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[float] = None
    fraud_indicators: Optional[List[str]] = []
    compliance_issues: Optional[List[str]] = []
    recommendation: Optional[str] = None
    reason: Optional[str] = None
    requires_human_review: Optional[bool] = False
 
 
class PaymentDecision(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    approved_amount: Optional[float] = None
    transaction_id: Optional[str] = None
    payment_method: Optional[str] = None
    approval_chain: Optional[List[str]] = []
    rejection_reason: Optional[str] = None
    scheduled_date: Optional[str] = None
 
 
class AuditTrail(BaseModel):
    process_id: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_name: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
 



class AgentMetrics(BaseModel):
    executions: int = 0          # total number of times the agent ran
    successes: int = 0           # how many times it succeeded
    failures: int = 0            # how many times it failed
    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0

# class AgentMetrics(BaseModel):
#     success_rate: Optional[float] = None
#     average_duration_ms: Optional[int] = None
#     total_executions: Optional[int] = None
#     failed_executions: Optional[int] = None
 
 
# ============================================================
# STATE MODEL — CENTRAL WORKFLOW STATE
# ============================================================ from uuid import uuid4
class InvoiceProcessingState(BaseModel):
    """Central shared state for LangGraph workflow"""
    # Core identifiers
    # process_id: str
 

    # file_name: str
    process_id: Optional[str] = Field(default_factory=lambda: f"proc_{uuid4().hex[:8]}")
    file_name: str
 
    # Processing status
    overall_status: Optional[ProcessingStatus] = ProcessingStatus.PENDING
    current_agent: Optional[str] = None
    workflow_type: Optional[str] = "standard"
 
    # Agent outputs
    invoice_data: Optional[InvoiceData] = None
    validation_result: Optional[ValidationResult] = None
    risk_assessment: Optional[RiskAssessment] = None
    payment_decision: Optional[PaymentDecision] = None
 
    # Audit and metrics
    audit_trail: List[AuditTrail] = []
    agent_metrics: Dict[str, AgentMetrics] = {}
 
    # Escalation control
    escalation_required: bool = False
    human_review_required: bool = False
    escalation_record: Optional[Dict[str, Any]] = None
    notification_info: Optional[Dict[str, Any]] = None

 
    # Workflow control
    retry_count: int = 0
    completed_agents: List[str] = []
    audit_report: Optional[Dict[str, Any]] = None

 
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
 
    def log_action(self, agent_name: str, action: str, status: str, details: Dict[str, Any] = None, duration_ms: int = 0, error_message: str = None):
        """Add a log entry to the audit trail"""
        self.audit_trail.append(
            AuditTrail(
                process_id=self.process_id,
                agent_name=agent_name,
                action=action,
                status=status,
                details=details,
                duration_ms=duration_ms,
                error_message=error_message
            )
        )
        self.updated_at = datetime.utcnow()
 
    # def update_metrics(self, agent_name: str, success: bool, duration_ms: int):
    #     """Update performance metrics for an agent"""
    #     metrics = self.agent_metrics.get(agent_name, AgentMetrics(total_executions=0, failed_executions=0))
    #     metrics.total_executions = (metrics.total_executions or 0) + 1
    #     if not success:
    #         metrics.failed_executions = (metrics.failed_executions or 0) + 1
    #     if metrics.total_executions:
    #         metrics.success_rate = 1 - (metrics.failed_executions / metrics.total_executions)
    #     metrics.average_duration_ms = duration_ms
    #     self.agent_metrics[agent_name] = metrics

    def update_metrics(self, agent_name: str, success: bool, duration_ms: int):
        """Update performance metrics for an agent (used internally)."""
        metrics = self.agent_metrics.get(agent_name)
        if not metrics:
            metrics = AgentMetrics()
            self.agent_metrics[agent_name] = metrics

        # Increment total runs
        metrics.executions += 1

        # Track successes/failures
        if success:
            metrics.successes += 1
        else:
            metrics.failures += 1

        # Calculate average duration
        total_runs = metrics.executions
        metrics.average_duration_ms = (
            (metrics.average_duration_ms * (total_runs - 1)) + duration_ms
        ) / total_runs


    def add_audit_entry(self, agent_name: str, action: str, status: str, details: Dict[str, Any] = None):
        """Alias for log_action used by tests."""
        self.log_action(agent_name=agent_name, action=action, status=status, details=details)

    def update_agent_metrics(self, agent_name: str, success: bool, duration_ms: int):
        """Alias for update_metrics used by tests."""
        self.update_metrics(agent_name=agent_name, success=success, duration_ms=duration_ms)

 
 
# ============================================================
# WORKFLOW CONFIGURATIONS
# ============================================================
 
class WorkflowConfig(BaseModel):
    workflow_type: str
    description: str
    sequence: List[str]
 
 
WORKFLOW_CONFIGS = {
    "standard": WorkflowConfig(
        workflow_type="standard",
        description="Default workflow for standard invoices",
        sequence=[
            "document_agent",
            "validation_agent",
            "risk_agent",
            "payment_agent",
            "audit_agent",
        ],
    ),
    "high_value": WorkflowConfig(
        workflow_type="high_value",
        description="Enhanced workflow for high-value invoices",
        sequence=[
            "document_agent",
            "validation_agent",
            "risk_agent",
            "audit_agent",
            "escalation_agent",
        ],
    ),
    "expedited": WorkflowConfig(
        workflow_type="expedited",
        description="Fast-track workflow for urgent invoices",
        sequence=[
            "document_agent",
            "validation_agent",
            "payment_agent",
            "audit_agent",
        ],
    ),
}
