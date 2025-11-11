# """Base Agent Class for Invoice Processing System"""

# # TODO: Implement agent

# import time
# import logging
# from abc import ABC, abstractmethod
# from typing import Dict, Any, Optional, List
# from datetime import datetime

# from state import InvoiceProcessingState, ProcessingStatus, AuditTrail
# from utils.logger import get_logger


# class BaseAgent(ABC):
#     """Abstract base class for all invoice processing agents"""

#     def __init__(self, agent_name: str, config: Dict[str, Any] = None):
#         pass

#     @abstractmethod
#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     async def run(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def get_metrics(self) -> Dict[str, Any]:
#         pass

#     def reset_metrics(self):
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass

#     def _extract_business_context(self, state: InvoiceProcessingState) -> Dict[str, Any]:
#         pass

#     def _should_escalate(self, state: InvoiceProcessingState, reason: str = None) -> bool:
#         pass

#     def _log_decision(self, state: InvoiceProcessingState, decision: str,
#                      reasoning: str, confidence: float = None):
#         pass


# class AgentRegistry:
#     """Registry for managing agent instances"""

#     def __init__(self):
#         pass

#     def register(self, agent: BaseAgent):
#         pass

#     def get(self, agent_name: str) -> Optional[BaseAgent]:
#         pass

#     def list_agents(self) -> List[str]:
#         pass

#     def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
#         pass

#     async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
#         pass


# # Global agent registry instance
# agent_registry = AgentRegistry()

"""Base Agent Class for Invoice Processing System"""
 
# Implemented agent
 
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
 
from state import InvoiceProcessingState, ProcessingStatus
from utils.logger import get_logger
 
 
class BaseAgent(ABC):
    """Abstract base class for all invoice processing agents"""
 
    def __init__(self, agent_name: str, config: Dict[str, Any] = None):
        self.agent_name = agent_name
        self.config = (config or {}).copy()
        self.logger: logging.Logger = get_logger(agent_name)
 
        # simple in-memory metrics
        self._metrics: Dict[str, Any] = {
            "total_runs": 0,
            "successes": 0,
            "failures": 0,
            "last_duration_ms": 0,
            "avg_duration_ms": 0.0,
            "last_error": None,
            "last_run_at": None,
        }
 
    # ------------------------------------------------------------------
    # Abstract: concrete agents must implement their logic here
    # ------------------------------------------------------------------
    @abstractmethod
    async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        """Perform the agent's core function and return the updated state."""
        raise NotImplementedError
 
    # ------------------------------------------------------------------
    # Orchestrated wrapper: handles timing, logging, errors, metrics
    # ------------------------------------------------------------------
    async def run(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        """Safe wrapper around execute() with metrics, logging and audit updates."""
        start = self._start_timer()
        self._metrics["total_runs"] += 1
        self._metrics["last_run_at"] = datetime.utcnow().isoformat()
 
        # mark the pipeline context
        state.current_agent = self.agent_name
        if state.overall_status == ProcessingStatus.PENDING:
            state.overall_status = ProcessingStatus.IN_PROGRESS
 
        # preconditions
        if not self._validate_preconditions(state):
            msg = f"Preconditions failed for {self.agent_name}"
            self.logger.error(msg)
            self._metrics["failures"] += 1
            self._metrics["last_error"] = msg
            state.overall_status = ProcessingStatus.FAILED
            # also log to audit
            state.log_action(
                agent_name=self.agent_name,
                action="precondition_check",
                status="failed",
                details={"reason": msg},
                duration_ms=self._stop_timer(start),
                error_message=msg,
            )
            return state
 
        try:
            updated = await self.execute(state)
 
            # postconditions
            post_ok = self._validate_postconditions(updated)
            duration = self._stop_timer(start)
            self._metrics["last_duration_ms"] = duration
            self._recompute_avg(duration)
 
            if post_ok:
                self._metrics["successes"] += 1
                self._metrics["last_error"] = None
            else:
                self._metrics["failures"] += 1
                self._metrics["last_error"] = "Postconditions failed"
                self.logger.warning(f"Postconditions failed for {self.agent_name}")
                updated.log_action(
                    agent_name=self.agent_name,
                    action="postcondition_check",
                    status="failed",
                    details={"reason": "Postconditions failed"},
                    duration_ms=0,
                    error_message="Postconditions failed",
                )
            # ✅ Push runtime metrics to the global invoice state for dashboard tracking
            if hasattr(updated, "update_metrics"):
                updated.update_metrics(
                    self.agent_name,
                    success=post_ok,
                    duration_ms=self._metrics["last_duration_ms"]
                )
 
            return updated
 
        except Exception as e:
            duration = self._stop_timer(start)
            self._metrics["last_duration_ms"] = duration
            self._recompute_avg(duration)
            self._metrics["failures"] += 1
            self._metrics["last_error"] = str(e)
 
            self.logger.exception(f"{self.agent_name} execution failed: {e}")
            state.log_action(
                agent_name=self.agent_name,
                action="execute",
                status="failed",
                details={"error": str(e)},
                duration_ms=duration,
                error_message=str(e),
            )
            state.overall_status = ProcessingStatus.FAILED
 
            if hasattr(state, "update_metrics"):
                state.update_metrics(
                    self.agent_name,
                    success=False,
                    duration_ms=self._metrics["last_duration_ms"]
                )
 
           
           
            return state
 
    # ------------------------------------------------------------------
    # Hooks (default permissive)
    # ------------------------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        """Override in subclasses to guard inputs; default = True."""
        return True
 
    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        """Override in subclasses to verify outputs; default = True."""
        return True
 
    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)
 
    def reset_metrics(self):
        self._metrics.update(
            {
                "total_runs": 0,
                "successes": 0,
                "failures": 0,
                "last_duration_ms": 0,
                "avg_duration_ms": 0.0,
                "last_error": None,
                "last_run_at": None,
            }
        )
 
    # ------------------------------------------------------------------
    # Health check (subclasses may extend)
    # ------------------------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "config": self.config,
        }
 
    # ------------------------------------------------------------------
    # Helpers available to all agents
    # ------------------------------------------------------------------
    def _extract_business_context(self, state: InvoiceProcessingState) -> Dict[str, Any]:
        """Lightweight summary useful for logs and AI prompts."""
        inv = state.invoice_data
        val = state.validation_result
        return {
            "process_id": state.process_id,
            "file_name": state.file_name,
            "workflow_type": state.workflow_type,
            "invoice_summary": {
                "invoice_number": getattr(inv, "invoice_number", None) if inv else None,
                "order_id": getattr(inv, "order_id", None) if inv else None,
                "customer_name": getattr(inv, "customer_name", None) if inv else None,
                "total": getattr(inv, "total", None) if inv else None,
                "due_date": getattr(inv, "due_date", None) if inv else None,
            },
            "validation_status": str(getattr(val, "validation_status", None)) if val else None,
        }
 
    def _should_escalate(self, state: InvoiceProcessingState, reason: str = None) -> bool:
        """Mark state for escalation; returns True to simplify calling code."""
        state.escalation_required = True
        state.human_review_required = True
        if reason:
            self.logger.info(f"Escalation requested by {self.agent_name}: {reason}")
            state.log_action(
                agent_name=self.agent_name,
                action="escalation_flag",
                status="pending",
                details={"reason": reason},
                duration_ms=0,
            )
        return True
 
    def _log_decision(
        self,
        state: InvoiceProcessingState,
        decision: str,
        reasoning: str,
        confidence: float = None,
    ):
        """Uniform audit log for decisions made by agents."""
        details = {"decision": decision, "reasoning": reasoning}
        if confidence is not None:
            details["confidence"] = round(float(confidence), 3)
        state.log_action(
            agent_name=self.agent_name,
            action="decision",
            status="completed",
            details=details,
            duration_ms=0,
        )
 
    # ------------------------------------------------------------------
    # Timing helpers
    # ------------------------------------------------------------------
    def _start_timer(self) -> float:
        return time.perf_counter()
 
    def _stop_timer(self, start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
 
    def _recompute_avg(self, last_ms: int):
        # incremental average
        n = max(1, int(self._metrics["total_runs"]))
        prev_avg = float(self._metrics["avg_duration_ms"])
        new_avg = prev_avg + (last_ms - prev_avg) / n
        self._metrics["avg_duration_ms"] = new_avg
 
 
class AgentRegistry:
    """Registry for managing agent instances"""
 
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
 
    def register(self, agent: BaseAgent):
        if not isinstance(agent, BaseAgent):
            raise TypeError("Only BaseAgent instances can be registered.")
        name = getattr(agent, "agent_name", None)
        if not name:
            raise ValueError("Agent must have a valid agent_name.")
        self._agents[name] = agent
 
    def get(self, agent_name: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_name)
 
    def list_agents(self) -> List[str]:
        return sorted(self._agents.keys())
 
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        return {name: agent.get_metrics() for name, agent in self._agents.items()}
 
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for name, agent in self._agents.items():
            try:
                results[name] = await agent.health_check()
            except Exception as e:
                results[name] = {"agent": name, "status": "error", "error": str(e)}
        return results
 
 
# Global agent registry instance
agent_registry = AgentRegistry()
