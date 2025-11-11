# """Validation Agent for Invoice Processing"""

# # TODO: Implement agent

# import pandas as pd
# from typing import Dict, Any, List, Tuple
# from fuzzywuzzy import fuzz
# import numpy as np

# from agents.base_agent import BaseAgent
# from state import (
#     InvoiceProcessingState, ValidationResult, ValidationStatus,
#     ProcessingStatus
# )
# from utils.logger import StructuredLogger


# class ValidationAgent(BaseAgent):
#     """Agent responsible for validating invoice data against purchase orders"""

#     def __init__(self, config: Dict[str, Any] = None):
#         pass

#     def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
#         pass

#     async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
#         pass

#     def _load_purchase_orders(self) -> pd.DataFrame:
#         pass

#     async def _find_matching_pos(self, invoice_data) -> List[Dict[str, Any]]:
#         pass

#     async def _validate_against_pos(self, invoice_data, matching_pos: List[Dict[str, Any]]) -> ValidationResult:
#         pass

#     def _validate_item_against_po(self, item, po_data: Dict[str, Any]) -> List[str]:
#         pass

#     def _validate_totals(self, invoice_data, po_data: Dict[str, Any]) -> List[str]:
#         pass

#     def _calculate_validation_confidence(self, validation_result: ValidationResult,
#                                        matching_pos: List[Dict[str, Any]]) -> float:
#         pass

#     def _determine_validation_status(self, validation_result: ValidationResult) -> ValidationStatus:
#         pass

#     def _should_escalate_validation(self, validation_result: ValidationResult, invoice_data) -> bool:
#         pass

#     async def health_check(self) -> Dict[str, Any]:
#         pass


"""Validation Agent for Invoice Processing"""
 
import os
import pandas as pd
from typing import Dict, Any, List
from fuzzywuzzy import fuzz
import numpy as np
 
from agents.base_agent import BaseAgent
from state import (
    InvoiceProcessingState, ValidationResult, ValidationStatus,
    ProcessingStatus
)
from utils.logger import StructuredLogger
 
 
class ValidationAgent(BaseAgent):
    """Agent responsible for validating invoice data against purchase orders"""
 
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_name="validation_agent")
        self.config = config or {}
        self.logger = StructuredLogger("ValidationAgent")
 
        self.po_file_path = self.config.get("po_file_path", "data/purchase_orders.csv")
        self.fuzzy_threshold = int(self.config.get("fuzzy_threshold", 80))
        self.amount_tolerance = float(self.config.get("amount_tolerance", 0.05))
        self.enable_three_way_match = bool(self.config.get("enable_three_way_match", True))
 
    # ------------------------------------------------------------------
    # Preconditions & Postconditions
    # ------------------------------------------------------------------
    def _validate_preconditions(self, state: InvoiceProcessingState) -> bool:
        if not state.invoice_data:
            self.logger.error("No invoice data found for validation.")
            return False
        if not os.path.exists(self.po_file_path):
            self.logger.error(f"PO file not found: {self.po_file_path}")
            return False
        return True
 
    def _validate_postconditions(self, state: InvoiceProcessingState) -> bool:
        return bool(state.validation_result and state.validation_result.po_found)
 
    # ------------------------------------------------------------------
    # Main Execution
    # ------------------------------------------------------------------
    async def execute(self, state: InvoiceProcessingState) -> InvoiceProcessingState:
        # print("Document_Agent:Invoice data",state)
        start = self._start_timer()
        state.current_agent = self.agent_name
        state.overall_status = ProcessingStatus.IN_PROGRESS
        invoice_data = state.invoice_data
 
        try:
            # 1. Load PO data
            po_df = self._load_purchase_orders()
 
            # 2. Find candidate POs using fuzzy matching
            matching_pos = await self._find_matching_pos(invoice_data)
 
            # 3. Validate invoice against PO(s)
            validation_result = await self._validate_against_pos(invoice_data, matching_pos)
 
            # 4. Assign results to state
            state.validation_result = validation_result
 
            # 5. Confidence & status
            validation_result.confidence_score = self._calculate_validation_confidence(validation_result, matching_pos)
            validation_result.validation_status = self._determine_validation_status(validation_result)
 
            # 6. Escalation check
            if self._should_escalate_validation(validation_result, invoice_data):
                state.escalation_required = True
                state.human_review_required = True
 
            # 7. Log audit
            state.log_action(
                agent_name=self.agent_name,
                action="validate_against_po",
                status="completed",
                details={
                    "po_found": validation_result.po_found,
                    "validation_status": validation_result.validation_status,
                    "confidence_score": validation_result.confidence_score,
                    "discrepancies": len(validation_result.discrepancies or [])
                },
                duration_ms=self._stop_timer(start)
            )
 
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            state.log_action(
                agent_name=self.agent_name,
                action="validate_against_po",
                status="failed",
                details={"error": str(e)},
                duration_ms=self._stop_timer(start),
                error_message=str(e)
            )
            state.overall_status = ProcessingStatus.FAILED
 
        print("validation agent o/p",state)
        return state
 
    # ------------------------------------------------------------------
    # PO Handling
    # ------------------------------------------------------------------
    def _load_purchase_orders(self) -> pd.DataFrame:
        try:
            po_df = pd.read_csv(self.po_file_path)
            po_df.columns = [col.strip().lower() for col in po_df.columns]
            return po_df
        except Exception as e:
            self.logger.error(f"Error loading PO file: {e}")
            raise
 
    async def _find_matching_pos(self, invoice_data) -> List[Dict[str, Any]]:
        """Use fuzzy string matching to find similar POs."""
        po_df = self._load_purchase_orders()
        candidates = []
        for _, row in po_df.iterrows():
            customer_score = fuzz.token_set_ratio(
                str(invoice_data.customer_name or ""), str(row.get("customer_name", ""))
            )
            if customer_score >= self.fuzzy_threshold:
                candidates.append(row.to_dict())
        self.logger.info(f"Found {len(candidates)} potential PO matches")
        return candidates
 
    # ------------------------------------------------------------------
    # Validation Logic
    # ------------------------------------------------------------------
    async def _validate_against_pos(self, invoice_data, matching_pos: List[Dict[str, Any]]) -> ValidationResult:
        if not matching_pos:
            return ValidationResult(
                po_found=False,
                validation_status=ValidationStatus.MISSING_PO,
                validation_result="No matching PO found",
                discrepancies=["No matching PO found"],
                confidence_score=0.0
            )
 
        best_match = max(
            matching_pos,
            key=lambda po: fuzz.token_set_ratio(str(invoice_data.order_id or ""), str(po.get("order_id", ""))),
        )
 
        discrepancies: List[str] = []
        quantity_match = rate_match = amount_match = True
 
        # Validate each item in the invoice
        for item in invoice_data.item_details or []:
            item_discrepancies = self._validate_item_against_po(item, best_match)
            if item_discrepancies:
                discrepancies.extend(item_discrepancies)
                quantity_match = False
 
        # Validate total amounts
        total_discrepancies = self._validate_totals(invoice_data, best_match)
        if total_discrepancies:
            discrepancies.extend(total_discrepancies)
            amount_match = False
 
        status = ValidationStatus.VALID if not discrepancies else ValidationStatus.PARTIAL_MATCH
 
        return ValidationResult(
            po_found=True,
            quantity_match=quantity_match,
            rate_match=rate_match,
            amount_match=amount_match,
            validation_status=status,
            validation_result="; ".join(discrepancies) if discrepancies else "All fields match",
            discrepancies=discrepancies,
            confidence_score=0.0,
            expected_amount=float(best_match.get("expected_amount", 0.0)),
            po_data=best_match
        )
 
    # def _validate_item_against_po(self, item, po_data: Dict[str, Any]) -> List[str]:
    #     issues = []
    #     item_name_score = fuzz.token_set_ratio(
    #         str(item.get("item_name", "")), str(po_data.get("item_name", ""))
    #     )
    #     if item_name_score < self.fuzzy_threshold:
    #         issues.append(f"Item name mismatch (similarity {item_name_score}%)")
 
    #     invoice_qty = float(item.get("quantity", 0))
    #     po_qty = float(po_data.get("quantity", 0))
    #     if invoice_qty != po_qty:
    #         issues.append(f"Quantity mismatch: Expected {po_qty}, Found {invoice_qty}")
 
    #     invoice_rate = float(item.get("rate", 0))
    #     po_rate = float(po_data.get("rate", 0))
    #     if abs(invoice_rate - po_rate) / (po_rate + 1e-6) > self.amount_tolerance:
    #         issues.append(f"Rate mismatch: Expected {po_rate}, Found {invoice_rate}")
 
    #     return issues
 
    def _validate_item_against_po(self, item, po_data: Dict[str, Any]) -> List[str]:
        """Compare a single invoice item with PO entry, supporting both dict and ItemDetail."""
        issues = []
 
        # ✅ Normalize invoice item data
        if isinstance(item, dict):
            item_name = str(item.get("item_name", "")).strip()
            invoice_qty = float(item.get("quantity", 0))
            invoice_rate = float(item.get("rate", 0))
        else:  # ItemDetail object
            item_name = str(getattr(item, "item_name", "")).strip()
            invoice_qty = float(getattr(item, "quantity", 0))
            invoice_rate = float(getattr(item, "rate", 0))
 
        # ✅ Normalize PO fields
        po_item_name = str(po_data.get("item_name", "")).strip()
        po_qty = float(po_data.get("quantity", 0))
        po_rate = float(po_data.get("rate", 0))
 
        # 🧩 Fuzzy compare item names
        item_name_score = fuzz.token_set_ratio(item_name, po_item_name)
        if item_name_score < self.fuzzy_threshold:
            issues.append(f"Item name mismatch (similarity {item_name_score}%)")
 
        # 🧩 Compare quantity
        if invoice_qty != po_qty:
            issues.append(f"Quantity mismatch: Expected {po_qty}, Found {invoice_qty}")
 
        # 🧩 Compare rate (within tolerance)
        if abs(invoice_rate - po_rate) / (po_rate + 1e-6) > self.amount_tolerance:
            issues.append(f"Rate mismatch: Expected {po_rate}, Found {invoice_rate}")
 
        return issues
 
 
    # def _validate_totals(self, invoice_data, po_data: Dict[str, Any]) -> List[str]:
    #     issues = []
    #     expected_amount = float(po_data.get("amount", 0))
    #     actual_total = float(invoice_data.total or 0)
    #     diff = abs(expected_amount - actual_total) / (expected_amount + 1e-6)
    #     if diff > self.amount_tolerance:
    #         issues.append(
    #             f"Total amount mismatch: Expected {expected_amount}, Actual {actual_total} (Diff {diff * 100:.2f}%)"
    #         )
 
    #     discount = getattr(invoice_data, "discount", 0) or 0
    #     if discount > 0:
    #         issues.append(f"Discount applied: {discount} not in PO")
 
    #     return issues
 
    def _validate_totals(self, invoice_data, po_data: Dict[str, Any]) -> List[str]:
        issues = []
        try:
            expected_amount = float(po_data.get("expected_amount", 0))
        except Exception:
            expected_amount = 0.0
        actual_total = float(getattr(invoice_data, "total", 0) or 0)
        diff = abs(expected_amount - actual_total) / (expected_amount + 1e-6)
        if diff > self.amount_tolerance:
            issues.append(
                f"Total amount mismatch: Expected {expected_amount}, Actual {actual_total} (Diff {diff * 100:.2f}%)"
            )
 
        discount = float(getattr(invoice_data, "discount", 0) or 0)
        if discount > 0:
            issues.append(f"Discount applied: {discount} not in PO")
 
        return issues
 
    # ------------------------------------------------------------------
    # Confidence, Status, Escalation
    # ------------------------------------------------------------------
    def _calculate_validation_confidence(
        self, validation_result: ValidationResult, matching_pos: List[Dict[str, Any]]
    ) -> float:
        score = 0.2 if validation_result.po_found else 0
        if validation_result.validation_status == ValidationStatus.VALID:
            score += 0.3
        elif validation_result.validation_status == ValidationStatus.PARTIAL_MATCH:
            score += 0.15
 
        if len(validation_result.discrepancies or []) <= 2:
            score += 0.2
        if len(matching_pos) > 0:
            score += 0.1
 
        return min(1.0, score)
 
    def _determine_validation_status(self, validation_result: ValidationResult) -> ValidationStatus:
        if not validation_result.po_found:
            return ValidationStatus.MISSING_PO
        if not validation_result.discrepancies:
            return ValidationStatus.VALID
        if len(validation_result.discrepancies) <= 2:
            return ValidationStatus.PARTIAL_MATCH
        if len(validation_result.discrepancies) > 3:
            return ValidationStatus.REQUIRES_APPROVAL
        return ValidationStatus.INVALID
 
    def _should_escalate_validation(self, validation_result: ValidationResult, invoice_data) -> bool:
        return (
            validation_result.validation_status in
            [ValidationStatus.REQUIRES_APPROVAL, ValidationStatus.INVALID, ValidationStatus.MISSING_PO]
            or invoice_data.total >= 25000
        )
 
    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "po_file_exists": os.path.exists(self.po_file_path),
            "fuzzy_threshold": self.fuzzy_threshold,
            "amount_tolerance": self.amount_tolerance,
        }
