import csv, io, datetime, uuid
from openpyxl import load_workbook

def parse_bulk_file(filename, content):
    name=(filename or "").lower()
    rows=[]
    if name.endswith(".csv"):
        text=content.decode("utf-8",errors="ignore")
        return [{(k or "").strip():(v or "").strip() for k,v in r.items() if k} for r in csv.DictReader(io.StringIO(text))]
    if name.endswith(".xlsx"):
        wb=load_workbook(io.BytesIO(content),data_only=True)
        ws=wb.active
        values=list(ws.values)
        if not values: return []
        headers=[str(h).strip() if h is not None else "" for h in values[0]]
        for row in values[1:]:
            item={}
            for i,h in enumerate(headers):
                if h:
                    item[h]="" if i>=len(row) or row[i] is None else str(row[i]).strip()
            if any(item.values()): rows.append(item)
        return rows
    if name.endswith(".txt"):
        return [{"raw_text":line.strip()} for line in content.decode("utf-8",errors="ignore").splitlines() if line.strip()]
    return [{"raw_file":filename,"note":"File accepted. OCR/document extraction is planned for production."}]

def first_value(row,*keys):
    normalized={str(k).lower().strip():v for k,v in row.items()}
    for key in keys:
        val=normalized.get(key.lower().strip())
        if val: return val
    return ""

def classify_action(issue, action):
    text=f"{issue} {action}".lower()
    if any(x in text for x in ["nte","explain","notice to explain"]): return "Prepare / send Notice to Explain instruction"
    if any(x in text for x in ["ir","incident report","report"]): return "Request Incident Report from coordinator"
    if any(x in text for x in ["salary","payroll","deduction","wage"]): return "Request payroll verification and worker statement"
    if any(x in text for x in ["accident","injury","medical"]): return "Request accident report, medical proof, and safety documents"
    if any(x in text for x in ["theft","fraud","missing","cash"]): return "Escalate high-risk case and secure evidence chain"
    return action or "Request supporting documents"

def normalize_row(row,index):
    worker=first_value(row,"worker_name","employee_name","name","worker","employee")
    worker_id=first_value(row,"worker_id","employee_id","id")
    coordinator=first_value(row,"coordinator","coor","coordinator_id","assigned_coordinator") or "coor001"
    location=first_value(row,"location","area","hub","branch") or "Unassigned"
    worker_type=first_value(row,"worker_type","type","position","category") or "Worker"
    issue=first_value(row,"issue","incident","violation","case_type","concern","reason") or first_value(row,"raw_text") or first_value(row,"raw_file") or "For review"
    action=first_value(row,"action","required_action","notice","next_action") or "Send IR notification / request explanation"
    return {"line_no":index,"worker_id":worker_id or f"W-TEMP-{index:03d}","worker_name":worker or f"Unnamed Worker {index}","worker_type":worker_type,"coordinator":coordinator,"location":location,"issue":issue,"recommended_action":classify_action(issue,action),"status":"For Coordinator Action"}

def build_bulk_assessment(rows):
    items=[normalize_row(r,i+1) for i,r in enumerate(rows)]
    return {"batch_id":"BATCH-"+datetime.datetime.now().strftime("%Y%m%d")+"-"+uuid.uuid4().hex[:5].upper(),"total_records":len(items),"summary":{"high_risk_cases":sum(1 for x in items if "high-risk" in x["recommended_action"].lower()),"payroll_verification":sum(1 for x in items if "payroll" in x["recommended_action"].lower()),"nte_instructions":sum(1 for x in items if "notice to explain" in x["recommended_action"].lower()),"ir_requests":sum(1 for x in items if "incident report" in x["recommended_action"].lower())},"recommended_central_command_action":"Review bulk records, confirm coordinator assignment, then release action template to coordinators.","items":items}

def make_csv_template(items):
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["worker_id","worker_name","worker_type","coordinator","location","issue","recommended_action","message_template"])
    for x in items:
        msg=f"Please coordinate with {x['worker_name']} regarding: {x['issue']}. Required action: {x['recommended_action']}. Submit supporting documents through EHR Central Command."
        writer.writerow([x["worker_id"],x["worker_name"],x["worker_type"],x["coordinator"],x["location"],x["issue"],x["recommended_action"],msg])
    return output.getvalue()
