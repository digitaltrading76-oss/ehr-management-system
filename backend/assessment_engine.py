def assess_documents(submitted_by, area, worker_name, worker_type, incident_category, incident_summary, files):
    text = (incident_category + " " + incident_summary).lower()
    findings = []

    rules = [
        (["salary","wage","pay","underpaid","deduction"], "Salary / Wage Concern", "Check payroll records, attendance logs, deductions, and proof of payment.", "Request payroll computation, attendance record, payout proof, and explanation of deductions."),
        (["accident","injury","hospital","crash","medical"], "Accident / Safety Incident", "Check accident report, photos, medical record, and police/barangay report if applicable.", "Prioritize documentation and welfare assistance verification."),
        (["theft","fraud","steal","missing parcel","cash","remittance"], "Possible Theft / Fraud", "Possible serious misconduct, dishonesty, breach of trust, or company property issue.", "Require evidence chain, inventory logs, witness statements, and worker explanation."),
        (["awol","absent","attendance","late"], "Attendance / Timekeeping Concern", "Check attendance policy, schedule, leave records, and prior offense history.", "Require attendance logs, duty schedule, leave records, and coordinator statement."),
        (["parcel","on hold","gps","timestamp","delivery","damage"], "Parcel / Delivery Operations Issue", "Possible performance of duties or negligence depending on proof.", "Require delivery app logs, GPS/timestamp records, parcel status history, and client complaint if any.")
    ]

    for keys, cls, basis, action in rules:
        if any(k in text for k in keys):
            findings.append({"classification": cls, "review_basis": basis, "recommended_action": action})

    if not findings:
        findings.append({"classification":"Unclassified Incident","review_basis":"No direct policy match from submitted summary.","recommended_action":"Request more complete facts before forwarding as a formal case."})

    names=[x["filename"] for x in files if x.get("filename")]
    readiness=min(35 + len(names)*10 + (15 if len(incident_summary)>120 else 0), 95)

    if readiness >= 75:
        status="Ready for Central Command review"
    elif readiness >= 50:
        status="Can be submitted, but follow-up evidence is likely required"
    else:
        status="Incomplete. Coordinator should add more details before submission"

    return {
        "submission_status": status,
        "submitted_by": submitted_by,
        "area": area,
        "worker": {"name": worker_name, "type": worker_type},
        "incident_category": incident_category,
        "uploaded_files_count": len(names),
        "uploaded_files": names,
        "preliminary_assessment": findings,
        "missing_or_recommended_documents": [
            "Coordinator incident report",
            "Worker written explanation received by coordinator",
            "Supporting photos or screenshots",
            "Witness statement, if any",
            "System logs or records",
            "Prior offense record, if any"
        ],
        "readiness_score": readiness,
        "recommended_next_step": "Complete missing facts/documents, then submit to Central Command for formal review."
    }
