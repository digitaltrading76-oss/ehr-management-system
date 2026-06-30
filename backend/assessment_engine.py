def assess_documents(submitted_by, area, worker_name, worker_type, incident_category, incident_summary, files):
    text = (incident_category + " " + incident_summary).lower()
    findings = []

    rules = [
        (["salary","wage","pay","underpaid","deduction"], "Salary / Wage Concern", "Check payroll records, attendance logs, deductions, and proof of payment.", "Request payroll computation, attendance record, payout proof, and explanation of deductions."),
        (["accident","injury","hospital","crash","medical"], "Accident / Safety Incident", "Check accident report, photos, medical record, and police/barangay report if applicable.", "Prioritize documentation and welfare assistance verification."),
        (["theft","fraud","steal","missing parcel","cash","remittance"], "Possible Theft / Fraud", "Possible serious misconduct, dishonesty, breach of trust, or company property issue.", "Require evidence chain, inventory logs, witness statements, and worker explanation before issuing recommendation."),
        (["awol","absent","attendance","late"], "Attendance / Timekeeping Concern", "Check attendance policy, schedule, leave records, and prior offense history.", "Require attendance logs, duty schedule, leave records, and coordinator statement."),
        (["parcel","on hold","gps","timestamp","delivery","damage"], "Parcel / Delivery Operations Issue", "Possible performance of duties or negligence depending on proof.", "Require delivery app logs, GPS/timestamp records, parcel status history, and client complaint if any.")
    ]

    for keys, cls, basis, action in rules:
        if any(k in text for k in keys):
            findings.append({"classification": cls, "review_basis": basis, "recommended_action": action})

    if not findings:
        findings.append({
            "classification":"Unclassified Incident",
            "review_basis":"No direct policy match from submitted summary.",
            "recommended_action":"Request more complete facts before forwarding as a formal case."
        })

    uploaded_names=[x["filename"] for x in files if x.get("filename")]
    readiness=min(35 + len(uploaded_names)*10 + (15 if len(incident_summary)>120 else 0), 95)

    if readiness >= 75:
        status="Ready for Central Command review"
    elif readiness >= 50:
        status="Can be submitted, but follow-up evidence is likely required"
    else:
        status="Incomplete. Coordinator should add more details before submission"

    if readiness < 60:
        next_move = "Return to coordinator for additional documents before formal HR review."
    elif any("Possible Theft / Fraud" == f["classification"] for f in findings):
        next_move = "Escalate as high-risk case. Require evidence chain and worker explanation before NTE."
    elif any("Salary / Wage Concern" == f["classification"] for f in findings):
        next_move = "Request payroll and attendance validation before recommendation."
    elif any("Accident / Safety Incident" == f["classification"] for f in findings):
        next_move = "Prioritize welfare/safety verification and collect accident documentation."
    else:
        next_move = "Proceed to Central Command review. Prepare follow-up checklist and determine if NTE is required."

    return {
        "submission_status": status,
        "submitted_by": submitted_by,
        "area": area,
        "worker": {"name": worker_name, "type": worker_type},
        "incident_category": incident_category,
        "uploaded_files_count": len(uploaded_names),
        "uploaded_files": uploaded_names,
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
        "recommended_next_move": next_move,
        "central_command_note": "This is a preliminary system assessment. Final action must be reviewed by Central Command."
    }
