from typing import Dict

COMPANY_RULES = [
    {
        "category": "Timekeeping and Attendance",
        "violation": "AWOL",
        "keywords": ["awol", "absent without leave", "absence without official leave", "unauthorized absence"],
        "condition": "Absence without official leave or absence not informed to supervisor, co-worker, or HRD.",
        "penalties": {
            "1": "Written Warning",
            "2": "3 days suspension",
            "3": "5 days suspension",
            "4": "7 days suspension",
            "5": "Dismissal"
        },
        "required_facts": [
            "number of days absent",
            "whether employee informed supervisor/HR",
            "prior AWOL count within one calendar year",
            "approved leave form or absence of approval"
        ]
    },
    {
        "category": "Performance of Duties",
        "violation": "Simple Negligence",
        "keywords": ["negligence", "mistake", "failed to observe", "careless", "delay", "on hold", "wrong tagging", "gps", "timestamp", "signal", "parcel"],
        "condition": "Failure to observe the degree of diligence demanded by the situation, exposing the company to unnecessary risk.",
        "penalties": {
            "1": "Written Reprimand",
            "2": "5 days suspension",
            "3": "15 days suspension",
            "4": "Dismissal"
        },
        "required_facts": [
            "exact act or omission",
            "business impact",
            "whether mistake was intentional or technical",
            "supporting logs or evidence",
            "prior similar incidents"
        ]
    },
    {
        "category": "Performance of Duties",
        "violation": "Gross Negligence",
        "keywords": ["gross negligence", "reckless", "blatant disregard", "serious damage", "repeated serious failure"],
        "condition": "Blatant disregard to perform required care or diligence amounting to reckless disregard of established rules.",
        "penalties": {
            "1": "30 days suspension to dismissal depending on circumstances"
        },
        "required_facts": [
            "seriousness of damage",
            "clear rule disregarded",
            "whether disregard was reckless",
            "prior warnings",
            "proof of company loss or serious risk"
        ]
    },
    {
        "category": "Performance of Duties",
        "violation": "Insubordination",
        "keywords": ["refused", "refusal", "failed to follow order", "disobeyed", "insubordination"],
        "condition": "Refusal or failure to follow reasonable work-related orders or instructions of superiors.",
        "penalties": {
            "1": "15 days suspension",
            "2": "Dismissal"
        },
        "required_facts": [
            "specific order given",
            "whether order was lawful and work-related",
            "who gave the order",
            "employee response",
            "witnesses or proof"
        ]
    },
    {
        "category": "Behavior",
        "violation": "Grave Disrespect / Rudeness",
        "keywords": ["shouted", "insulted", "disrespect", "rude", "profane", "threatened", "intimidated"],
        "condition": "Acts of grave disrespect, rudeness or discourtesy toward colleagues, superiors, customers, suppliers, applicants or clients.",
        "penalties": {
            "1": "15 days suspension",
            "2": "Dismissal"
        },
        "required_facts": [
            "exact words/actions",
            "recipient of conduct",
            "witnesses",
            "whether work was disrupted",
            "provocation or mitigating facts"
        ]
    },
    {
        "category": "Behavior",
        "violation": "Dishonesty / Falsification",
        "keywords": ["false", "falsified", "tampered", "forged", "misleading", "fake", "altered document"],
        "condition": "Knowingly giving false or misleading information or tampering, forging, falsifying, or altering documents.",
        "penalties": {
            "1": "Dismissal"
        },
        "required_facts": [
            "document or record involved",
            "proof of falsification",
            "intent to deceive",
            "benefit gained",
            "person who discovered the issue"
        ]
    }
]

LABOR_STANDARDS_FALLBACK = [
    {
        "classification": "Serious Misconduct",
        "when_to_consider": "Intentional wrongful conduct connected to work, serious in nature, and not merely a minor error.",
        "questions": [
            "Was the act intentional?",
            "Was it serious and work-related?",
            "Did it violate a known rule or standard?"
        ]
    },
    {
        "classification": "Willful Disobedience / Insubordination",
        "when_to_consider": "Employee knowingly refused a lawful and reasonable work-related order.",
        "questions": [
            "Was there a clear order?",
            "Was the order lawful and reasonable?",
            "Did the employee knowingly refuse?"
        ]
    },
    {
        "classification": "Gross and Habitual Neglect of Duties",
        "when_to_consider": "There is serious or repeated failure to perform duties, not just one minor mistake.",
        "questions": [
            "Was the neglect gross or habitual?",
            "Was there serious damage or risk?",
            "Were there previous warnings?"
        ]
    },
    {
        "classification": "Fraud or Willful Breach of Trust",
        "when_to_consider": "There is deception, dishonesty, or breach of confidence by an employee occupying a position of trust.",
        "questions": [
            "Was there intentional deception?",
            "Did the employee hold a position of trust?",
            "Was trust clearly breached?"
        ]
    }
]

def score_rule(text: str, rule: Dict) -> int:
    text_l = text.lower()
    score = 0
    for kw in rule["keywords"]:
        if kw in text_l:
            score += 18
    return min(score, 100)

def get_penalty(rule: Dict, prior_offense_count: int):
    offense_no = str(prior_offense_count + 1)
    if offense_no in rule["penalties"]:
        return rule["penalties"][offense_no]
    keys = list(rule["penalties"].keys())
    return rule["penalties"][keys[-1]]

def analyze_case(employee_name: str, position: str, incident_date: str, incident_text: str, prior_offense_count: int = 0) -> Dict:
    text = incident_text or ""
    ranked = []
    for rule in COMPANY_RULES:
        s = score_rule(text, rule)
        if s > 0:
            ranked.append((s, rule))
    ranked.sort(reverse=True, key=lambda x: x[0])

    if ranked:
        best_score, best_rule = ranked[0]
        policy_match = {
            "found": True,
            "confidence": best_score,
            "category": best_rule["category"],
            "possible_violation": best_rule["violation"],
            "condition": best_rule["condition"],
            "possible_penalty_based_on_matrix": get_penalty(best_rule, prior_offense_count),
            "required_facts": best_rule["required_facts"],
        }
    else:
        policy_match = {
            "found": False,
            "confidence": 0,
            "message": "No exact company policy match found. Refer to labor standards as additional confirmation and flag for authorized review."
        }

    missing_evidence = [
        "Supervisor incident report",
        "Employee written explanation",
        "Witness statement",
        "System or application logs",
        "GPS or timestamp logs",
        "Prior disciplinary record",
        "Proof of business impact or damage"
    ]

    lower = text.lower()
    if "signal" in lower or "gps" in lower or "timestamp" in lower:
        missing_evidence.extend([
            "Network or signal issue verification",
            "Delivery route history",
            "Other riders' reports for same date/location"
        ])

    follow_up_questions = [
        "What exact act or omission is being complained of?",
        "When and where did the incident happen?",
        "Who witnessed the incident?",
        "What evidence supports the allegation?",
        "Is this the employee's first offense?",
        "Was the employee given a chance to explain?"
    ]

    if "on hold" in lower or "parcel" in lower:
        follow_up_questions.extend([
            "Were all On Hold parcels recorded on the same date?",
            "Were the parcels later delivered or returned?",
            "Did other riders experience similar GPS or signal issues?",
            "Can system logs confirm the timestamp and location?"
        ])

    labor_fallback = []
    if not policy_match["found"] or policy_match.get("confidence", 0) < 50:
        labor_fallback = LABOR_STANDARDS_FALLBACK

    evidence_strength = 30
    if len(text) > 300:
        evidence_strength += 10
    if any(word in lower for word in ["witness", "cctv", "gps log", "screenshot", "proof"]):
        evidence_strength += 20
    evidence_strength = min(evidence_strength, 100)

    if policy_match.get("confidence", 0) >= 70 and evidence_strength >= 60:
        recommendation = "Proceed with Notice to Explain and formal investigation. Do not impose final penalty until due process is completed."
    elif policy_match.get("confidence", 0) >= 30:
        recommendation = "Continue investigation. Ask follow-up questions and require supporting evidence before recommending discipline."
    else:
        recommendation = "Insufficient information. No disciplinary recommendation yet. Refer to authorized review and gather more facts."

    return {
        "case_status": "For Investigation",
        "employee": {
            "name": employee_name,
            "position": position,
            "incident_date": incident_date
        },
        "incident_summary": text[:1200],
        "policy_assessment": policy_match,
        "labor_standards_review": labor_fallback,
        "missing_evidence": list(dict.fromkeys(missing_evidence)),
        "follow_up_questions": list(dict.fromkeys(follow_up_questions)),
        "scores": {
            "policy_match": policy_match.get("confidence", 0),
            "evidence_strength": evidence_strength,
            "due_process_completion": 10,
            "overall_confidence": int((policy_match.get("confidence", 0) + evidence_strength) / 2)
        },
        "recommendation": recommendation,
        "safeguard": "System output is preliminary only. Final action must be reviewed by authorized personnel after due process."
    }
