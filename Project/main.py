# """Main Streamlit UI for invoice processing"""
# # TODO: Build Streamlit dashboard

# import os
# import asyncio
# import pandas as pd
# import streamlit as st
# from datetime import datetime
# import plotly.express as px
# import plotly.graph_objects as go
# from typing import Dict, Any, List

# from graph import get_workflow
# from state import ProcessingStatus, ValidationStatus, RiskLevel, PaymentStatus
# from utils.logger import setup_logging, get_logger


# class InvoiceProcessingApp:
#     """Main application class"""

#     def __init__(self):
#         pass

#     def initialize_session_state(self):
#         pass

#     def initialize_workflow(self):
#         pass

#     def render_header(self):
#         pass

#     def render_sidebar(self):
#         pass

#     def get_available_files(self) -> List[str]:
#         pass

#     async def process_invoices_async(self, selected_files: List[str],
#                                    workflow_type: str, priority_level: int,
#                                    max_concurrent: int):
#         pass

#     def show_processing_summary(self, results: List):
#         pass

#     def render_main_dashboard(self):
#         pass

#     def render_overview_tab(self):
#         pass

#     def render_invoice_details_tab(self):
#         pass

#     def show_detailed_invoice_view(self, result):
#         pass

#     def render_agent_performance_tab(self):
#         pass

#     def render_escalations_tab(self):
#         pass

#     def render_analytics_tab(self):
#         pass

#     def show_workflow_diagram(self):
#         pass

#     def show_health_check(self):
#         pass

#     def run(self):
#         pass


# if __name__ == "__main__":
#     pass






"""Main Streamlit UI for Invoice AgenticAI — LangGraph Version (Final UI Corrected)"""

import os
import asyncio
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
from typing import List
import threading
import uvicorn

from graph import get_workflow
from state import ProcessingStatus, PaymentStatus
from utils.logger import setup_logging, get_logger
from datetime import datetime, timezone
UTC = timezone.utc
from google.cloud import firestore
from fastapi import FastAPI



# --- FastAPI + Firestore setup ---
# db = firestore.Client()
# workflow = get_workflow({})
# api = FastAPI()

# Create ONE workflow instance
shared_workflow = get_workflow({})
db = firestore.Client()

from api_review import create_fastapi_app
api = create_fastapi_app(shared_workflow, db)



class InvoiceProcessingApp:
    """Main application class"""

    def __init__(self):
        setup_logging()
        self.logger = get_logger("StreamlitApp")
        self.initialize_session_state()
        self.initialize_workflow()

    # ---------------------------------------------------------------------- #
    # Initialization
    # ---------------------------------------------------------------------- #
    def initialize_session_state(self):
        if "results" not in st.session_state:
            st.session_state.results = []
        if "last_run" not in st.session_state:
            st.session_state.last_run = None
        if "workflow" not in st.session_state:
            st.session_state.workflow = None
        if "running" not in st.session_state:
            st.session_state.running = False
        if "workflow_initialized" not in st.session_state:
            st.session_state.workflow_initialized = False

    def initialize_workflow(self):
        if st.session_state.workflow is None:
            st.session_state.workflow = shared_workflow
            st.session_state.workflow_initialized = True
            self.logger.info("Workflow initialized successfully.")

    # ---------------------------------------------------------------------- #
    # Header
    # ---------------------------------------------------------------------- #
    def render_header(self):
        st.set_page_config(page_title="Invoice AgenticAI", page_icon="🧾", layout="wide")

        st.markdown(
            """
            <style>
            .main-title {
                background: linear-gradient(90deg, #004aad, #007bff);
                color: white;
                padding: 18px;
                border-radius: 8px;
                font-size: 26px;
                font-weight: 600;
                text-align: center;
            }
            .sub-caption {
                text-align: center;
                color: #f0f0f0;
                font-size: 15px;
                margin-top: -8px;
                margin-bottom: 20px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="main-title">🧾 Invoice AgenticAI — LangGraph
             <div class="sub-caption">AI-Powered Invoice Processing with Intelligent Agent Workflows</div>
            </div>
           
            """,
            unsafe_allow_html=True
        )

        if st.session_state.workflow_initialized:
            st.success("✅ AI agents and workflow initialized successfully!")

    # ---------------------------------------------------------------------- #
    # Sidebar
    # ---------------------------------------------------------------------- #
    def render_sidebar(self):
        with st.sidebar:
            st.markdown("### ⚙️ Control Panel")

            workflow_type = st.selectbox(
                "Workflow Type", ["standard", "high-value", "expedited"], index=0
            )
            # priority_level = st.slider("Priority Level", 1, 5, 3)
            max_concurrent = st.slider("Max Concurrent Processing", 1, 10, 3)

            st.markdown("### 📂 Invoice Files")
            files = self.get_available_files()
            selected_files = st.multiselect(
                "Select Invoices to Process", options=files, default=[]
            )

            st.markdown("### 🧭 Processing Controls")
            run_btn = st.button("🚀 Process Invoices", type="primary", use_container_width=True)
            clear_btn = st.button("🧹 Clear Results", use_container_width=True)

            if clear_btn:
                st.session_state.results = []
                st.toast("Results cleared.", icon="🧹")

            st.markdown("### 🩺 System Status")
            st.button("Health Check", use_container_width=True)

        return selected_files, workflow_type, max_concurrent, run_btn

    def get_available_files(self) -> List[str]:
            # ✅ Use absolute path (works on local and Cloud Run)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data", "invoices")

            # Ensure folder exists
            os.makedirs(data_dir, exist_ok=True)

            # ✅ Handle missing or empty directory gracefully
            if not os.path.exists(data_dir):
                st.warning("⚠️ No 'data/invoices' folder found inside the app.")
                return []

            pdf_files = [
                os.path.join("data/invoices", f)
                for f in os.listdir(data_dir)
                if f.lower().endswith(".pdf")
            ]

            if not pdf_files:
                st.info("📂 No invoice files found in the 'data/invoices' folder.")
            return sorted(pdf_files)
#     def get_available_files(self) -> List[str]:
#         data_dir = os.path.join("data", "invoices")
#         os.makedirs(data_dir, exist_ok=True)
#         return sorted([
#     os.path.join(data_dir, f)
#     for f in os.listdir(data_dir)
#     if f.lower().endswith(".pdf")
# ])

    

    async def process_invoices_async(self, selected_files, workflow_type, max_concurrent):
        workflow = st.session_state.workflow
        sem = asyncio.Semaphore(max_concurrent)
        results, progress = [], st.progress(0.0)

        async def _run_one(f):
            async with sem:
                state = await workflow.process_invoice(f, workflow_type=workflow_type)
                import copy
                return copy.deepcopy(state)  # ← ensure unique isolated object per invoice

        # tasks = [_run_one(f) for f in selected_files]
        # for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        #     results.append(await coro)
        #     progress.progress(i / len(selected_files))

        tasks = [_run_one(f) for f in selected_files]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            state = await coro
            results.append(state)
            st.session_state.current_process_id = state.process_id
            progress.progress(i / len(selected_files))

            # 🧩 Toast if escalation email was sent
            notify = getattr(state, "notification_info", None)
            if notify and notify.get("status") in ("sent", "simulated"):
                st.toast(
                    f"📧 Escalation email sent to {notify.get('recipient')} "
                    f"for invoice {notify.get('invoice')} ({notify.get('escalation_type')})",
                    icon="✉️"
                )
        progress.empty()
        return results


    # ---------------------------------------------------------------------- #
    # Main Dashboard Tabs
    # ---------------------------------------------------------------------- #
    def render_main_dashboard(self):
        tabs = st.tabs(["🏠 Overview", "🧾 Invoice Details", "🤖 Agent Performance", "🚨 Escalations", "📈 Analytics"])
        with tabs[0]:
            self.render_overview_tab()
        with tabs[1]:
            self.render_invoice_details_tab()
        with tabs[2]:
            self.render_agent_performance_tab()
        with tabs[3]:
            self.render_escalations_tab()
        with tabs[4]:
            self.render_analytics_tab()

    # ---------------------------------------------------------------------- #
    # Overview Tab
    # ---------------------------------------------------------------------- #
    def render_overview_tab(self):
        results = st.session_state.results
        st.markdown("#### 📊 Processing Overview")

        if not results:
            st.info("Please select and process invoices to view results.")
            return

        df = pd.DataFrame([{
            "File": os.path.basename(r.file_name),
            "Status": str(r.overall_status.value if isinstance(r.overall_status, ProcessingStatus) else r.overall_status),
            "Amount": getattr(r.invoice_data, "total", 0.0) if r.invoice_data else 0.0,
            "Processing Time (min)": round(
                (datetime.utcnow() - getattr(r, "created_at", datetime.utcnow())).total_seconds() / 60, 2
            )
        } for r in results])

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df, names="Status", title="Processing Status Distribution (Invoices)")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(df, x="File", y="Processing Time (min)", color="Status",
                          title="Processing Duration by Invoice (Minutes)")
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------------------- #
    # Invoice Details Tab
    # ---------------------------------------------------------------------- #
   
    def render_escalations_tab(self):
        import os
        import streamlit as st
        from google.cloud import firestore
        import requests

        st.markdown("#### 🚨 Escalation Summary")

        results = st.session_state.get("results", [])
        db = firestore.Client()

        # =====================================================================
        # 🔥 LOOK FOR PENDING REVIEW ONLY FOR THIS USER'S PROCESS ID
        # =====================================================================
        current_pid = st.session_state.get("current_process_id")
        if current_pid:
            query = db.collection("pending_reviews").where("process_id", "==", current_pid)
            pending_docs = list(query.stream())
        else:
            pending_docs = []

        # =====================================================================
        # CASE 1 — PENDING CLOUD REVIEW (SHOW APPROVE/REJECT BUTTONS)
        # =====================================================================
        if pending_docs:
            st.markdown("### 🕒 Pending Approval for Your Uploaded Invoice")

            api_url = os.getenv(
                "API_REVIEW_URL",
                "http://127.0.0.1:8081/api/review/submit"
            )

            for doc in pending_docs:
                data = doc.to_dict()

                process_id = data.get("process_id")
                invoice_number = data.get("invoice_number", "N/A")
                priority = data.get("priority", "medium")
                approver = data.get("approver", "Finance Manager")
                created_at = data.get("created_at", "N/A")
                status = data.get("status", "PENDING_REVIEW")

                with st.expander(f"🧾 Invoice {invoice_number} — Priority: {priority}", expanded=False):
                    st.write(f"**Process ID:** {process_id}")
                    st.write(f"**Approver:** {approver}")
                    st.write(f"**Created At:** {created_at}")
                    st.write(f"**Status:** {status}")

                    col1, col2 = st.columns(2)

                    # -------------------------------------------------------------
                    # APPROVE BUTTON
                    # -------------------------------------------------------------
                    with col1:
                        if st.button(f"✅ Approve {invoice_number}", key=f"approve_{process_id}"):

                            payload = {
                                "process_id": process_id,
                                "decision": "approved",
                                "reviewer": approver,
                                "comments": "Approved via Streamlit dashboard",
                            }

                            res = requests.post(api_url, json=payload)

                            if res.status_code == 200:
                                st.success(f"Approved {invoice_number}")

                                updated = res.json()

                                # ⭐ Update session state invoice
                                for idx, r in enumerate(st.session_state.results):
                                    if getattr(r, "process_id", None) == process_id:
                                        # r.payment_decision.get("payment_status") = PaymentStatus[updated["payment_status"]]
                                        r.payment_decision["payment_status"] = updated["payment_status"]
                                        r.overall_status = ProcessingStatus[updated["overall_status"]]
                                        r.human_review_required = False
                                        st.session_state.results[idx] = r
                                        break

                                # ⭐ Remove from Firestore
                                db.collection("pending_reviews").document(process_id).delete()

                                st.rerun()
                            else:
                                st.error(f"⚠️ API Error: {res.text}")

                    # -------------------------------------------------------------
                    # REJECT BUTTON
                    # -------------------------------------------------------------
                    with col2:
                        if st.button(f"❌ Reject {invoice_number}", key=f"reject_{process_id}"):

                            payload = {
                                "process_id": process_id,
                                "decision": "rejected",
                                "reviewer": approver,
                                "comments": "Rejected via Streamlit dashboard",
                            }

                            res = requests.post(api_url, json=payload)

                            if res.status_code == 200:
                                st.error(f"Rejected {invoice_number}")

                                updated = res.json()

                                for idx, r in enumerate(st.session_state.results):
                                    if getattr(r, "process_id", None) == process_id:
                                        # r.payment_decision.get("payment_status") = PaymentStatus[updated["payment_status"]] 
                                        r.payment_decision["payment_status"] = updated["payment_status"]
                                        r.overall_status = ProcessingStatus[updated["overall_status"]]
                                        r.human_review_required = False
                                        st.session_state.results[idx] = r
                                        break

                                db.collection("pending_reviews").document(process_id).delete()

                                st.rerun()
                            else:
                                st.error(f"⚠️ API Error: {res.text}")

            return  # 🔥 Do NOT show local escalations if cloud review exists

        # =====================================================================
        # CASE 2 — LOCAL MODE (NO CLOUD REVIEW FOUND)
        # =====================================================================
        if results:
            st.markdown("### 🧾 Local Workflow Escalations (This Session)")

            escalations = {}

            for idx, r in enumerate(results):
                inv = getattr(r, "invoice_data", None)
                val = getattr(r, "validation_result", None)
                esc = getattr(r, "escalation_record", None)
                risk = getattr(r, "risk_assessment", None)

                invoice_no = getattr(inv, "invoice_number", f"Unknown-{idx}")
                process_id = getattr(r, "process_id", f"proc_{idx}")
                file_name = os.path.basename(r.file_name)

                risk_level_attr = getattr(risk, "risk_level", "low")
                risk_level = (
                    risk_level_attr.name.lower()
                    if hasattr(risk_level_attr, "name")
                    else str(risk_level_attr).split(".")[-1].lower()
                )

                if (
                    risk_level in ("low", "none")
                    and (not esc or not esc.get("reason"))
                ):
                    continue

                if process_id not in escalations:
                    escalations[process_id] = {
                        "File": file_name,
                        "Invoice #": invoice_no,
                        "Issues": [],
                        "Details": [],
                        "Priority": "Medium",
                        "Process ID": process_id,
                    }

                if val and (
                    getattr(val, "validation_status", None) not in ("valid", "VALID")
                    or (val.discrepancies and len(val.discrepancies) > 0)
                ):
                    discrepancy_text = ", ".join(val.discrepancies or [])
                    escalations[process_id]["Issues"].append(
                        f"Validation issues: {discrepancy_text}"
                    )

                if esc:
                    escalations[process_id]["Issues"].append(esc.get("reason", "Escalation triggered"))
                    escalations[process_id]["Details"].append(esc.get("summary", "N/A"))
                    escalations[process_id]["Priority"] = esc.get("priority", "High")

            if not escalations:
                st.success("No escalations in this session.")
                return

            st.warning(f"{len(escalations)} invoice(s) require attention")

            for e in escalations.values():
                with st.expander(f"⚠️ {e['File']} — {', '.join(e['Issues'])}", expanded=False):
                    st.write(f"**Invoice #:** {e['Invoice #']}")
                    st.write(f"**Priority:** {e['Priority']}")
                    st.write(f"**Process ID:** {e['Process ID']}")
                    st.write("**Issues:**")
                    for issue in e["Issues"]:
                        st.markdown(f"- {issue}")

                    if e["Details"]:
                        st.write("**Details:**")
                        for d in e["Details"]:
                            st.markdown(f"- {d}")

            st.info("These escalations are from your current session.")
            return

        # =====================================================================
        # CASE 3 — NO ESCALATIONS ANYWHERE
        # =====================================================================
        st.info("📄 No escalations found in this session or Firestore.")


    

   


    # def render_escalations_tab(self):
    #     import os
    #     import streamlit as st
    #     from google.cloud import firestore
    #     import requests

    #     st.markdown("#### 🚨 Escalation Summary")

    #     # Load local results if any
    #     results = st.session_state.get("results", [])

    #     # Always check Firestore first
    #     db = firestore.Client()

    #     # ==========================================================
    #     # 🔥 SHOW ONLY MY UPLOADED INVOICE (FILTERED BY process_id)
    #     # ==========================================================
    #     current_pid = st.session_state.get("current_process_id")

    #     if current_pid:
    #         query = db.collection("pending_reviews").where("process_id", "==", current_pid)
    #         pending_docs = list(query.stream())
    #     else:
    #         pending_docs = []

    #     # ==========================================================
    #     # CASE 1 — ONLY MY PENDING CLOUD REVIEW (Approve/Reject)
    #     # ==========================================================
    #     if pending_docs:
    #         st.markdown("### 🕒 Pending Approval for Your Uploaded Invoice")

    #         api_url = os.getenv(
    #             "API_REVIEW_URL",
    #             "http://127.0.0.1:8081/api/review/submit"
    #         )

    #         for doc in pending_docs:
    #             data = doc.to_dict()

    #             process_id = data.get("process_id")
    #             invoice_number = data.get("invoice_number", "N/A")
    #             priority = data.get("priority", "medium")
    #             approver = data.get("approver", "Finance Manager")
    #             created_at = data.get("created_at", "N/A")
    #             status = data.get("status", "PENDING_REVIEW")

    #             with st.expander(f"🧾 Invoice {invoice_number} — Priority: {priority}", expanded=False):
    #                 st.write(f"**Process ID:** {process_id}")
    #                 st.write(f"**Approver:** {approver}")
    #                 st.write(f"**Created At:** {created_at}")
    #                 st.write(f"**Status:** {status}")

    #                 col1, col2 = st.columns(2)

    #                 # APPROVE
    #                 with col1:
    #                     # if st.button(f"✅ Approve {invoice_number}", key=f"approve_{process_id}"):
    #                     #     payload = {
    #                     #         "process_id": process_id,
    #                     #         "decision": "approved",
    #                     #         "reviewer": approver,
    #                     #         "comments": "Approved via Streamlit dashboard",
    #                     #     }
    #                     #     res = requests.post(api_url, json=payload)
    #                     #     if res.status_code == 200:
    #                     #         st.success(f"✅ Approved {invoice_number}. Workflow resumed.")
    #                     #     else:
    #                     #         st.error(f"⚠️ API Error: {res.text}")
    #                     if st.button(f"✅ Approve {invoice_number}", key=f"approve_{process_id}"):

    #                         payload = {
    #                             "process_id": process_id,
    #                             "decision": "approved",
    #                             "reviewer": approver,
    #                             "comments": "Approved via Streamlit dashboard",
    #                         }

    #                         res = requests.post(api_url, json=payload)

    #                         if res.status_code == 200:
    #                             st.success(f"✅ Approved {invoice_number}")

    #                             updated = res.json()

    #                             # ⭐ Update this invoice's state inside session_state
    #                             for idx, r in enumerate(st.session_state.results):
    #                                 if getattr(r, "process_id", None) == process_id:
    #                                     r.payment_decision.get("payment_status") = updated["payment_status"]
    #                                     r.overall_status = updated["overall_status"]
    #                                     r.human_review_required = False
    #                                     st.session_state.results[idx] = r
    #                                     break

    #                             # ⭐ Remove Firestore pending review
    #                             db.collection("pending_reviews").document(process_id).delete()

    #                             st.rerun()

    #                         else:
    #                             st.error(f"⚠️ API Error: {res.text}")
    #                 # REJECT
    #                 with col2:
    #                     if st.button(f"❌ Reject {invoice_number}", key=f"reject_{process_id}"):

    #                         payload = {
    #                             "process_id": process_id,
    #                             "decision": "rejected",
    #                             "reviewer": approver,
    #                             "comments": "Rejected via Streamlit dashboard",
    #                         }

    #                         res = requests.post(api_url, json=payload)

    #                         if res.status_code == 200:
    #                             st.error(f"🚫 Rejected {invoice_number}")

    #                             updated = res.json()

    #                             for idx, r in enumerate(st.session_state.results):
    #                                 if getattr(r, "process_id", None) == process_id:
    #                                     r.payment_decision.get("payment_status") = updated["payment_status"]
    #                                     r.overall_status = updated["overall_status"]
    #                                     r.human_review_required = False
    #                                     st.session_state.results[idx] = r
    #                                     break

    #                             db.collection("pending_reviews").document(process_id).delete()
    #                             st.rerun()

    #                         else:
    #                             st.error(f"⚠️ API Error: {res.text}")
    #                     if st.button(f"❌ Reject {invoice_number}", key=f"reject_{process_id}"):

    #                         payload = {
    #                             "process_id": process_id,
    #                             "decision": "rejected",
    #                             "reviewer": approver,
    #                             "comments": "Rejected via Streamlit dashboard",
    #                         }

    #                         res = requests.post(api_url, json=payload)

    #                         if res.status_code == 200:
    #                             st.error(f"🚫 Rejected {invoice_number}")

    #                             updated = res.json()

    #                             for idx, r in enumerate(st.session_state.results):
    #                                 if getattr(r, "process_id", None) == process_id:
    #                                     r.payment_decision.get("payment_status") = updated["payment_status"]
    #                                     r.overall_status = updated["overall_status"]
    #                                     r.human_review_required = False
    #                                     st.session_state.results[idx] = r
    #                                     break

    #                             db.collection("pending_reviews").document(process_id).delete()
    #                             st.rerun()

    #                         else:
    #                             st.error(f"⚠️ API Error: {res.text}")

    #                     # if st.button(f"❌ Reject {invoice_number}", key=f"reject_{process_id}"):
    #                     #     payload = {
    #                     #         "process_id": process_id,
    #                     #         "decision": "rejected",
    #                     #         "reviewer": approver,
    #                     #         "comments": "Rejected via Streamlit dashboard",
    #                     #     }
    #                     #     res = requests.post(api_url, json=payload)
    #                     #     if res.status_code == 200:
    #                     #         st.error(f"🚫 Rejected {invoice_number}. Workflow updated.")
    #                     #     else:
    #                     #         st.error(f"⚠️ API Error: {res.text}")

    #         return  # IMPORTANT → Stop here, avoid showing local data

    #     # ==========================================================
    #     # CASE 2 — LOCAL MODE (NO FIRESTORE PENDING REVIEW)
    #     # ==========================================================
    #     if results:
    #         st.markdown("### 🧾 Local Workflow Escalations (This Session)")

    #         escalations = {}

    #         for idx, r in enumerate(results):
    #             inv = getattr(r, "invoice_data", None)
    #             val = getattr(r, "validation_result", None)
    #             esc = getattr(r, "escalation_record", None)
    #             risk = getattr(r, "risk_assessment", None)

    #             invoice_no = getattr(inv, "invoice_number", f"Unknown-{idx}")
    #             process_id = getattr(r, "process_id", f"proc_{idx}")
    #             file_name = os.path.basename(r.file_name)

    #             risk_level_attr = getattr(risk, "risk_level", "low")
    #             risk_level = (
    #                 risk_level_attr.name.lower()
    #                 if hasattr(risk_level_attr, "name")
    #                 else str(risk_level_attr).split(".")[-1].lower()
    #             )

    #             # Skip low-risk/no escalation
    #             if (
    #                 risk_level in ("low", "none")
    #                 and (not esc or (isinstance(esc, dict) and not esc.get("reason")))
    #                 and not (hasattr(risk, "requires_human_review") and getattr(risk, "requires_human_review"))
    #             ):
    #                 continue

    #             if process_id not in escalations:
    #                 escalations[process_id] = {
    #                     "File": file_name,
    #                     "Invoice #": invoice_no,
    #                     "Issues": [],
    #                     "Details": [],
    #                     "Priority": "Medium",
    #                     "Process ID": process_id,
    #                 }

    #             if val and (
    #                 getattr(val, "validation_status", None) not in ("valid", "VALID")
    #                 or (val.discrepancies and len(val.discrepancies) > 0)
    #             ):
    #                 discrepancy_text = ", ".join(val.discrepancies or [])
    #                 escalations[process_id]["Issues"].append(
    #                     f"Validation issues: {discrepancy_text or 'Unknown validation issue'}"
    #                 )

    #             if esc:
    #                 escalations[process_id]["Issues"].append(esc.get("reason", "Escalation triggered"))
    #                 escalations[process_id]["Details"].append(esc.get("summary", "N/A"))
    #                 escalations[process_id]["Priority"] = esc.get("priority", "High")

    #         if not escalations:
    #             st.success("✅ All invoices passed validation and no escalations detected.")
    #             return

    #         st.warning(f"{len(escalations)} invoice(s) require manual attention")

    #         for e in escalations.values():
    #             with st.expander(f"⚠️ {e['File']} — {', '.join(e['Issues'])}", expanded=False):
    #                 st.write(f"**Invoice #:** {e['Invoice #']}")
    #                 st.write(f"**Priority:** {e['Priority']}")
    #                 st.write(f"**Process ID:** {e['Process ID']}")
    #                 st.write("**Issues:**")
    #                 for issue in e["Issues"]:
    #                     st.markdown(f"- {issue}")

    #                 if e["Details"]:
    #                     st.write("**Details:**")
    #                     for d in e["Details"]:
    #                         st.markdown(f"- {d}")

    #         st.info("ℹ️ These escalations are ONLY from this session.")
    #         return

    #     # ==========================================================
    #     # CASE 3 — NOTHING TO SHOW
    #     # ==========================================================
    #     st.info("📄 No escalations found in this session or Firestore.")

    def render_invoice_details_tab(self):
        import pandas as pd
        from datetime import datetime

        st.markdown("#### 🧾 Invoice Details Table")
        results = st.session_state.results
        if not results:
            st.info("No processed invoices yet. Run processing first.")
            return

        table_data = []
        for r in results:
            inv = r.invoice_data
            risk = r.risk_assessment
            pay = r.payment_decision
            duration = round(
                (datetime.utcnow() - getattr(r, "created_at", datetime.utcnow())).total_seconds() / 60, 2
            )

            payment_status = getattr(pay, "payment_status", "N/A")
            if hasattr(payment_status, "name"):
                payment_status = payment_status.name

            table_data.append({
                "File": os.path.basename(r.file_name),
                "Invoice #": getattr(inv, "invoice_number", "N/A"),
                "Customer": getattr(inv, "customer_name", "N/A"),
                "Amount": getattr(inv, "total", 0.0),
                "Risk Level": str(getattr(risk, "risk_level", "N/A")),
                "Payment Status": payment_status,
                "Status": str(getattr(r.overall_status, "value", r.overall_status)),
                "Processing Time (min)": duration,
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, width="stretch")

    # --- 📊 Summary metrics section ---
        # total_escalated = sum(1 for r in results if str(r.overall_status).lower() == "escalated")
        # total_completed = sum(1 for r in results if str(r.overall_status).lower() == "completed")

        # col1, col2 = st.columns(2)
        # with col1:
        #     st.metric("🚨 Total Escalated Invoices", total_escalated)
        # with col2:
        #     st.metric("✅ Total Completed Invoices", total_completed)

        # st.markdown("---")

# --- 📊 Metrics based on actual workflow state ---

        # Count invoices that have escalation records
        total_escalated = sum(1 for r in results if getattr(r, "escalation_record", None))

        # Count invoices that are marked as completed
        def is_completed(r):
            status = getattr(r, "overall_status", None)
            if hasattr(status, "value"):
                return str(status.value).lower() == "completed"
            return str(status).lower().endswith("completed")

        total_completed = sum(1 for r in results if is_completed(r))

        # --- Display summary metrics ---
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🚨 Total Escalated Invoices", total_escalated)
        with col2:
            st.metric("✅ Total Completed Invoices", total_completed)

        st.markdown("---")


        # --- 🔍 Detailed Invoice View ---
        st.subheader("🔍 Detailed Invoice View")

        invoice_options = [
            f"{os.path.basename(r.file_name)} - {getattr(r.invoice_data, 'customer_name', 'Unknown')}"
            for r in results
        ]

        selected_invoice = st.selectbox("Select invoice for detailed view:", invoice_options)

        selected_result = None
        for r in results:
            if selected_invoice.startswith(os.path.basename(r.file_name)):
                selected_result = r
                break

        if not selected_result:
            st.info("Select an invoice to see its details.")
            return

        inv = selected_result.invoice_data
        risk = selected_result.risk_assessment
        pay = selected_result.payment_decision

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🧾 Invoice Information")
            st.write(f"**Invoice Number:** {getattr(inv, 'invoice_number', 'N/A')}")
            st.write(f"**Customer:** {getattr(inv, 'customer_name', 'N/A')}")
            st.write(f"**Amount:** ${getattr(inv, 'total', 0.0):,.2f}")

        with col2:
            st.markdown("### 🎯 Processing Results")
            st.write(f"**Overall Status:** {getattr(selected_result.overall_status, 'value', selected_result.overall_status)}")
            st.write(f"**Risk Level:** {getattr(risk, 'risk_level', 'N/A')}")
            st.write(f"**Payment Status:** {getattr(pay, 'payment_status', 'N/A')}")

        st.markdown("---")

   
    def render_agent_performance_tab(self):
        st.markdown("#### 🤖 Agent Performance Summary")

        results = st.session_state.results
        # st.info(results)
        if not results:
            st.info("No agent performance data available yet. Run some invoices first.")
            return

        # Collect aggregated metrics from all results
        aggregated = {}
        for r in results:
            for agent_name, metrics in getattr(r, "agent_metrics", {}).items():
                if agent_name not in aggregated:
                    aggregated[agent_name] = {
                        "executions": 0,
                        "successes": 0,
                        "failures": 0,
                        "total_duration": 0,
                    }
                aggregated[agent_name]["executions"] += metrics.executions
                aggregated[agent_name]["successes"] += metrics.successes
                aggregated[agent_name]["failures"] += metrics.failures
                aggregated[agent_name]["total_duration"] += (
                    metrics.average_duration_ms * metrics.executions
                )

        # Build table data
        data = []
        for agent_name, m in aggregated.items():
            total_runs = m["executions"] or 1
            success_rate = (m["successes"] / total_runs) * 100
            avg_duration = m["total_duration"] / total_runs if total_runs else 0
            data.append({
                "Agent": agent_name.replace("_", " ").title(),
                "Executions": total_runs,
                "Success Rate (%)": round(success_rate, 1),
                "Avg Duration (ms)": round(avg_duration, 2),
                "Failures": m["failures"],
            })

        if not data:
            st.warning("No runtime metrics recorded yet.")
            return

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                px.bar(df, x="Agent", y="Success Rate (%)", title="Agent Success Rates (%)"),
                use_container_width=True,
            )
        with c2:
            st.plotly_chart(
                px.bar(df, x="Agent", y="Avg Duration (ms)", title="Average Agent Processing Time (ms)"),
                use_container_width=True,
            )

    



    # def handle_human_decision(self, escalation, decision: str):
    #     """Handle manual approval/rejection of a single invoice without affecting others."""
    #     import asyncio
    #     import streamlit as st
    #     from datetime import datetime, UTC
    #     from graph import get_workflow
    #     from state import ProcessingStatus, PaymentStatus

    #     invoice_no = escalation.get("Invoice #")
    #     process_id = escalation.get("Process ID")

    #     st.toast(
    #         f"🧠 Reviewer marked Invoice {invoice_no} as {decision.upper()}",
    #         icon="✅" if decision == "approved" else "❌",
    #     )

    #     decision_data = {
    #         "decision": decision,
    #         "reviewer": "Risk Manager",
    #         "comments": f"Manually {decision} by Risk Manager.",
    #         "timestamp": datetime.now(UTC).isoformat(),
    #     }

    #     try:
    #         workflow = get_workflow({})

    #         # ✅ Resume only the correct workflow instance
    #         updated_state = asyncio.run(
    #             workflow.resume(
    #                 process_id=process_id,
    #                 node="human_review_node",  # make sure node name matches
    #                 value=decision_data,
    #             )
    #         )

    #         # ✅ Update only this invoice in session_state
    #         for idx, r in enumerate(st.session_state.results):
    #             if getattr(r, "process_id", None) == process_id:
    #                 # Update key fields only, not replace the whole object
    #                 r.overall_status = ProcessingStatus.COMPLETED
    #                 r.human_review_required = False
    #                 r.escalation_record = getattr(r, "escalation_record", None)

    #                 r.payment_decision = type("PaymentDecision", (), {
    #                     "payment_status": PaymentStatus.APPROVED if decision == "approved" else PaymentStatus.REJECTED,
    #                     "approved_amount": getattr(r.invoice_data, "total", 0.0),
    #                     "method": "MANUAL_REVIEW",
    #                     "reviewed_by": "Risk Manager",
    #                     "review_comments": f"Manually {decision} by Risk Manager.",
    #                 })()

    #                 # ✅ Keep other attributes intact (invoice_data, validation_result, etc.)
    #                 st.session_state.results[idx] = r
    #                 break  # stop loop once found
    #         st.session_state[f"review_status_{process_id}"] = decision
                   

    #         st.rerun()

    #     except Exception as err:
    #         import traceback
    #         st.error(f"⚠️ Failed to resume workflow for {invoice_no}: {err}")
    #         st.text(traceback.format_exc())



    


    
    # ---------------------------------------------------------------------- #
    # Analytics Tab
    # ---------------------------------------------------------------------- #
    def render_analytics_tab(self):
        st.markdown("#### 📈 Analytics Dashboard")
        results = st.session_state.results
        if not results:
            st.info("No analytics available yet.")
            return

        df = pd.DataFrame([{
            "File": os.path.basename(r.file_name),
            "Amount": getattr(r.invoice_data, "total", 0.0) if r.invoice_data else 0.0,
            "Risk": str(getattr(r.risk_assessment, "risk_level", "N/A")),
            "Status": str(r.overall_status.value if isinstance(r.overall_status, ProcessingStatus) else r.overall_status)
        } for r in results])

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.histogram(df, x="Amount", nbins=10, title="Amount Distribution"), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(df, names="Risk", title="Risk Level Breakdown"), use_container_width=True)

        st.markdown("##### Processing Time Distribution")
        df["Processing Time (min)"] = [round(
            (datetime.utcnow() - getattr(r, "created_at", datetime.utcnow())).total_seconds() / 60, 2
        ) for r in results]
        st.plotly_chart(px.bar(df, x="File", y="Processing Time (min)", color="Status"), use_container_width=True)

    # ---------------------------------------------------------------------- #
    # Run
    # ---------------------------------------------------------------------- #
    def run(self):
        self.render_header()
        selected_files, workflow_type,  max_concurrent, run_btn = self.render_sidebar()

        if run_btn:
            if not selected_files:
                st.warning("Please select at least one invoice file to process.")
            else:
                st.session_state.running = True
                with st.spinner("Processing invoices..."):
                    results = asyncio.run(
                        self.process_invoices_async(selected_files, workflow_type,  max_concurrent)
                    )
                    st.session_state.results = results
                    st.session_state.last_run = datetime.utcnow().isoformat()
                st.session_state.running = False
                st.success(f"✅ Completed processing {len(selected_files)} invoice(s).")

        self.render_main_dashboard()

if __name__ == "__main__":
    # --- Start FastAPI in background ---
    def start_fastapi():
        uvicorn.run(api, host="0.0.0.0", port=8081, log_level="info")

    threading.Thread(target=start_fastapi, daemon=True).start()
    app = InvoiceProcessingApp()
    app.run()

