import csv, io, datetime, uuid
from openpyxl import load_workbook

def parse_bulk_file(filename, content):
    name=(filename or "").lower()
    if name.endswith(".csv"):
        text=content.decode("utf-8",errors="ignore")
        return [{(k or "").strip():(v or "").strip() for k,v in r.items() if k} for r in csv.DictReader(io.StringIO(text))]
    if name.endswith(".xlsx"):
        wb=load_workbook(io.BytesIO(content),data_only=True)
        ws=wb.active
        rows=list(ws.values)
        if not rows: return []
        headers=[str(h).strip() if h else "" for h in rows[0]]
        out=[]
        for row in rows[1:]:
            item={}
            for i,h in enumerate(headers):
                if h: item[h]="" if i>=len(row) or row[i] is None else str(row[i]).strip()
            if any(item.values()): out.append(item)
        return out
    if name.endswith(".txt"):
        return [{"raw_text":line.strip()} for line in content.decode("utf-8",errors="ignore").splitlines() if line.strip()]
    return [{"raw_file":filename,"note":"File accepted. OCR/document extraction planned."}]

def first(row,*keys):
    d={str(k).lower().strip():v for k,v in row.items()}
    for k in keys:
        if d.get(k): return d[k]
    return ""

def action(issue, act):
    t=f"{issue} {act}".lower()
    if "nte" in t or "explain" in t: return "Prepare / send Notice to Explain instruction"
    if "ir" in t or "incident report" in t: return "Request Incident Report from coordinator"
    if "salary" in t or "payroll" in t or "wage" in t: return "Request payroll verification and worker statement"
    if "accident" in t or "injury" in t: return "Request accident report, medical proof, and safety documents"
    if "theft" in t or "fraud" in t or "cash" in t: return "Escalate high-risk case and secure evidence chain"
    return act or "Request supporting documents"

def build_bulk_assessment(rows):
    items=[]
    for i,r in enumerate(rows,1):
        issue=first(r,"issue","incident","violation","case_type","concern","reason") or first(r,"raw_text") or first(r,"raw_file") or "For review"
        act=first(r,"action","required_action","notice","next_action") or "Send IR notification / request explanation"
        items.append({
            "line_no":i,
            "worker_id":first(r,"worker_id","employee_id","id") or f"W-TEMP-{i:03d}",
            "worker_name":first(r,"worker_name","employee_name","name","worker","employee") or f"Unnamed Worker {i}",
            "worker_type":first(r,"worker_type","type","position","category") or "Worker",
            "coordinator":first(r,"coordinator","coor","coordinator_id","assigned_coordinator") or "coor001",
            "location":first(r,"location","area","hub","branch") or "Unassigned",
            "issue":issue,
            "recommended_action":action(issue,act)
        })
    return {"batch_id":"BATCH-"+datetime.datetime.now().strftime("%Y%m%d")+"-"+uuid.uuid4().hex[:5].upper(),"total_records":len(items),"summary":{"high_risk_cases":sum(1 for x in items if "high-risk" in x["recommended_action"].lower()),"payroll_verification":sum(1 for x in items if "payroll" in x["recommended_action"].lower()),"nte_instructions":sum(1 for x in items if "notice to explain" in x["recommended_action"].lower()),"ir_requests":sum(1 for x in items if "incident report" in x["recommended_action"].lower())},"items":items}

def make_csv_template(items):
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["worker_id","worker_name","worker_type","coordinator","location","issue","recommended_action","message_template"])
    for x in items:
        msg=f"Please coordinate with {x['worker_name']} regarding: {x['issue']}. Required action: {x['recommended_action']}. Submit supporting documents through EHR Central Command."
        w.writerow([x["worker_id"],x["worker_name"],x["worker_type"],x["coordinator"],x["location"],x["issue"],x["recommended_action"],msg])
    return out.getvalue()
