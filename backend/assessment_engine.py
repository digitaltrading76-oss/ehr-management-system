def assess_documents(submitted_by, area, worker_name, worker_type, incident_category, incident_summary, files):
    text = (incident_category + " " + incident_summary).lower()

    possible = []
    if any(k in text for k in ["salary", "wage", "pay", "underpaid", "deduction"]):
        possible.append({
            "classification": "Salary / Wage Concern",
            "review_basis": "Labor standards review required. Check payroll records, attendance, deductions, and proof of payment.",
            "recommended_action": "Request payroll computation, attendance logs, proof of payout, and explanation of deductions."
        })
    if any(k in text for k in ["accident", "injury", "hospital", "crash", "medical"]):
        possible.append({
            "classification": "Accident / Safety Incident",
            "review_basis": "Safety and welfare concern. Check accident report, photos, medical records, police/barangay report if applicable.",
            "recommended_action": "Prioritize incident documentation and immediate welfare assistance verification."
        })
    if any(k in text for k in ["theft", "fraud", "steal", "missing parcel", "cash", "remittance"]):
        possible.append({
            "classification": "Possible Theft / Fraud",
            "review_basis": "Possible serious misconduct, dishonesty, breach of trust, or company property issue.",
            "recommended_action": "Do not conclude yet. Require evidence chain, inventory logs, witness statements, and worker explanation."
        })
    if any(k in text for k in ["awol", "absent", "attendance", "late"]):
        possible.append({
            "classification": "Attendance / Timekeeping Concern",
            "review_basis": "Check company attendance policy and prior offense record.",
            "recommended_action": "Require attendance logs, schedule, leave records, and coordinator statement."
        })
    if any(k in text for k in ["parcel", "on hold", "gps", "timestamp", "delivery", "damage"]):
        possible.append({
            "classification": "Parcel / Delivery Operations Issue",
            "review_basis": "Possible performance of duties or negligence depending on proof.",
            "recommended_action": "Require delivery app logs, GPS/timestamp records, parcel status history, and client complaint if any."
        })

    if not possible:
        possible.append({
            "classification": "Unclassified Incident",
            "review_basis": "No direct policy match from submitted summary. Labor standards and company policy review required.",
            "recommended_action": "Request more complete facts before forwarding as formal case."
        })

    missing = [
        "Coordinator incident report",
        "Worker written explanation received by coordinator",
        "Supporting photos or screenshots",
        "Witness statement, if any",
        "System logs or records",
        "Prior offense record, if any"
    ]

    uploaded_names = [x["filename"] for x in files if x.get("filename")]
    readiness = 35 + min(len(uploaded_names) * 10, 40)
    if len(incident_summary) > 120:
        readiness += 15
    readiness = min(readiness, 95)

    if readiness >= 75:
        central_status = "Ready for Central Command review"
    elif readiness >= 50:
        central_status = "Can be submitted, but follow-up evidence is likely required"
    else:
        central_status = "Incomplete. Coordinator should add more details before submission"

    return {
        "submission_status": central_status,
        "submitted_by": submitted_by,
        "area": area,
        "worker": {
            "name": worker_name,
            "type": worker_type
        },
        "incident_category": incident_category,
        "uploaded_files_count": len(uploaded_names),
        "uploaded_files": uploaded_names,
        "preliminary_assessment": possible,
        "missing_or_recommended_documents": missing,
        "readiness_score": readiness,
        "recommended_next_step": "Submit to Central Command after completing missing documents and confirming facts. Assessment is preliminary and not a final disciplinary decision.",
        "central_command_note": "This pre-review is designed to organize the coordinator submission before the HR Grievance Department receives the case."
    }
