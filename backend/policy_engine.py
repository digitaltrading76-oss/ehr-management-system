COMPANY_POLICY_RULES = [
    {
        "keywords": ["late", "tardy", "tardiness"],
        "policy_category": "Timekeeping and Attendance",
        "possible_violation": "Tardiness",
        "policy_basis": "Company Code of Conduct - Matrix of Violations: Tardiness within one calendar year.",
        "usual_next_step": "Verify attendance logs and prior offense count."
    },
    {
        "keywords": ["awol", "absent without leave", "unauthorized absence", "absence"],
        "policy_category": "Timekeeping and Attendance",
        "possible_violation": "AWOL / Unauthorized Absence",
        "policy_basis": "Company Code of Conduct - AWOL and unauthorized absences.",
        "usual_next_step": "Verify schedule, attendance, leave filing, and whether employee informed supervisor/HR."
    },
    {
        "keywords": ["on hold", "parcel", "gps", "timestamp", "delivery", "damage", "wrong tagging"],
        "policy_category": "Performance of Duties",
        "possible_violation": "Possible Simple Negligence / Performance Issue",
        "policy_basis": "Company Code of Conduct - Negligence in the Performance of Duties.",
        "usual_next_step": "Verify delivery app logs, GPS/timestamp records, route history, and worker explanation."
    },
    {
        "keywords": ["refuse", "refused", "disobey", "insubordination", "failed to follow order"],
        "policy_category": "Performance of Duties",
        "possible_violation": "Insubordination",
        "policy_basis": "Company Code of Conduct - Refusal or failure to follow reasonable work-related orders.",
        "usual_next_step": "Confirm the lawful work-related order, who gave it, proof of refusal, and employee explanation."
    },
    {
        "keywords": ["theft", "steal", "stolen", "fraud", "falsified", "cash", "remittance", "missing parcel"],
        "policy_category": "Behavior / Company Property",
        "possible_violation": "Possible Theft, Fraud, Dishonesty, or Breach of Trust",
        "policy_basis": "Company Code of Conduct - stealing, falsification, breach of trust and confidence, or company property violations.",
        "usual_next_step": "Secure evidence chain, inventory/cash logs, witness statements, and employee explanation."
    },
    {
        "keywords": ["shouted", "insulted", "threatened", "rude", "disrespect", "fight", "harass"],
        "policy_category": "Behavior",
        "possible_violation": "Possible Grave Disrespect / Disorderly Conduct",
        "policy_basis": "Company Code of Conduct - disrespectful, insulting, indecent, threatening, or disorderly conduct.",
        "usual_next_step": "Collect exact words/actions, witness statements, and employee explanation."
    },
    {
        "keywords": ["accident", "injury", "hospital", "medical", "crash"],
        "policy_category": "Health, Safety and Security",
        "possible_violation": "Safety / Accident Incident",
        "policy_basis": "Company Code of Conduct - Health, Safety and Security obligations.",
        "usual_next_step": "Prioritize safety documentation, medical report, accident report, and welfare verification."
    },
    {
        "keywords": ["salary", "wage", "deduction", "underpaid", "payroll", "unpaid"],
        "policy_category": "Labor Standards / Payroll Concern",
        "possible_violation": "Salary or Wage Complaint",
        "policy_basis": "Requires payroll, attendance, and labor standards verification.",
        "usual_next_step": "Validate payroll computation, attendance, deductions, and payout proof."
    }
]

LABOR_STANDARDS = [
    {
        "keywords": ["theft", "fraud", "falsified", "dishonesty", "cash", "remittance"],
        "labor_category": "Possible serious misconduct / fraud / breach of trust",
        "legal_note": "May fall under just cause principles only if supported by substantial evidence and due process."
    },
    {
        "keywords": ["refuse", "disobey", "insubordination"],
        "labor_category": "Possible willful disobedience",
        "legal_note": "Requires proof that the order was lawful, reasonable, work-related, known to the employee, and willfully refused."
    },
    {
        "keywords": ["negligence", "on hold", "parcel", "gps", "timestamp", "damage"],
        "labor_category": "Possible neglect of duties",
        "legal_note": "For serious discipline, neglect must be proven by facts and must be gross, habitual, or sufficiently serious depending on the proposed penalty."
    },
    {
        "keywords": ["salary", "wage", "deduction", "underpaid", "payroll", "unpaid"],
        "labor_category": "Labor standards/payroll compliance concern",
        "legal_note": "Requires payroll verification and may not be a worker violation. Treat first as compliance review."
    },
    {
        "keywords": ["accident", "injury", "hospital", "medical", "crash"],
        "labor_category": "Workplace safety / welfare concern",
        "legal_note": "Focus first on documentation, assistance, and safety compliance before disciplinary assessment."
    }
]

DUE_PROCESS_REQUIREMENTS = [
    "Incident report",
    "Employee written explanation or opportunity to explain",
    "Evidence documents or logs",
    "Witness statement if applicable",
    "Prior offense record if penalty depends on offense count",
    "Central Command review",
    "Notice to Explain before formal disciplinary decision",
    "Final decision only after employee side is considered"
]

def _contains(text, keywords):
    return any(k in text for k in keywords)

def assess_case(worker_name, worker_type, category, summary, uploaded_names, submitted_by, area):
    text = f"{category} {summary}".lower()

    policy_matches = [r for r in COMPANY_POLICY_RULES if _contains(text, r["keywords"])]
    labor_matches = [r for r in LABOR_STANDARDS if _contains(text, r["keywords"])]

    if not policy_matches:
        policy_matches = [{
            "policy_category": "No exact company policy match",
            "possible_violation": "Unclassified or policy-silent incident",
            "policy_basis": "No direct match found in the current coded policy rules. Central Command should review company policy manually and validate under labor standards.",
            "usual_next_step": "Request more facts and supporting documents before formal action."
        }]

    if not labor_matches:
        labor_matches = [{
            "labor_category": "General labor due process review",
            "legal_note": "No specific legal category identified from the summary. Apply due process and request facts before any disciplinary action."
        }]

    uploaded_lower = " ".join(uploaded_names).lower()
    has_ir = bool(summary.strip()) or any("incident" in x.lower() or "ir" in x.lower() for x in uploaded_names)
    has_explanation = any("explanation" in x.lower() or "salaysay" in x.lower() or "explain" in x.lower() for x in uploaded_names)
    has_evidence = len(uploaded_names) > 0
    has_witness = any("witness" in x.lower() or "testimony" in x.lower() for x in uploaded_names)
    has_logs = any(x in uploaded_lower for x in ["gps", "log", "attendance", "payroll", "timestamp", "cctv", "screenshot"])
    has_prior = any("prior" in x.lower() or "record" in x.lower() for x in uploaded_names)

    checklist = [
        {"item":"Incident report / coordinator summary", "status": has_ir},
        {"item":"Employee written explanation or opportunity to explain", "status": has_explanation},
        {"item":"Supporting evidence / uploaded documents", "status": has_evidence},
        {"item":"Witness statement if applicable", "status": has_witness},
        {"item":"System logs / GPS / payroll / CCTV if applicable", "status": has_logs},
        {"item":"Prior offense record if penalty depends on offense count", "status": has_prior},
        {"item":"Central Command review", "status": False},
        {"item":"Notice to Explain before disciplinary decision", "status": False},
        {"item":"Final decision only after employee side is considered", "status": False}
    ]

    completed = sum(1 for x in checklist if x["status"])
    due_process_score = int((completed / len(checklist)) * 100)

    evidence_score = min(25 + len(uploaded_names)*12 + (20 if has_logs else 0) + (15 if has_explanation else 0), 100)
    policy_score = 80 if policy_matches and policy_matches[0]["policy_category"] != "No exact company policy match" else 35
    labor_score = 75 if labor_matches and labor_matches[0]["labor_category"] != "General labor due process review" else 45
    overall_readiness = int((due_process_score + evidence_score + policy_score + labor_score) / 4)

    missing = [x["item"] for x in checklist if not x["status"]]

    high_risk = any(word in text for word in ["theft", "fraud", "cash", "remittance", "falsified", "stolen"])
    payroll_case = any(word in text for word in ["salary", "wage", "deduction", "payroll", "unpaid"])
    accident_case = any(word in text for word in ["accident", "injury", "hospital", "medical"])

    if due_process_score < 45:
        recommended = "Do not proceed to disciplinary recommendation yet. Return/request missing due-process documents from coordinator."
    elif payroll_case:
        recommended = "Treat first as payroll/labor standards verification. Request payroll, attendance, payout proof, and deduction basis before any worker-directed action."
    elif accident_case:
        recommended = "Prioritize safety/welfare verification and accident documentation. Do not treat as violation unless facts show misconduct or negligence."
    elif high_risk and has_explanation and evidence_score >= 60:
        recommended = "Central Command may consider issuing or finalizing NTE review, but no final decision until employee explanation and evidence are evaluated."
    elif high_risk:
        recommended = "High-risk allegation. Secure evidence chain and require employee explanation before NTE/decision stage."
    elif overall_readiness >= 70:
        recommended = "Ready for Central Command review. Prepare follow-up checklist and determine whether NTE is appropriate."
    else:
        recommended = "More information required. Request missing documents and allow employee to explain before any disciplinary step."

    return {
        "worker": {"name": worker_name, "type": worker_type},
        "submitted_by": submitted_by,
        "area": area,
        "incident_category": category,
        "policy_assessment": policy_matches,
        "labor_standards_review": labor_matches,
        "due_process_checklist": checklist,
        "scores": {
            "company_policy_match": policy_score,
            "labor_standards_relevance": labor_score,
            "evidence_sufficiency": evidence_score,
            "due_process_completion": due_process_score,
            "overall_readiness": overall_readiness
        },
        "missing_requirements": missing,
        "recommended_next_move": recommended,
        "safeguard": "No final disciplinary action should be recommended until the worker is given due process under Philippine labor standards."
    }
