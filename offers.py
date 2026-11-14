#!/usr/bin/env python3
"""
Offers OSS by Idharyn Labs - the compliant, AI-agnostic job-hunt operating system.

One file. Local-first. Your Excel tracker is the source of truth,
the dashboard is a view, and any AI (Claude, ChatGPT, Gemini, Copilot,
a local model) does only the writing - on a token-lean "packet".

    python offers.py setup                # 6 questions -> ready (runs init)
    python offers.py go                   # daily cockpit: numbered choices, counters
    python offers.py brain                # fill common job-site questions once
    python offers.py add --company Acme --role "Java Dev" --jd jd.txt --url https://...
    python offers.py import jobs/inbox.csv
    python offers.py triage               # best-fit jobs first (zero AI tokens)
    python offers.py packet OF-0003       # token-lean prompt for any AI
    python offers.py status OF-0003 Applied --note "Referral via Priya"
    python offers.py due                  # follow-ups due today
    python offers.py stats                # pipeline in the terminal
    python offers.py export               # refresh dashboard/data.js
    python offers.py answer "notice period?"   # second brain, 0 tokens
    python offers.py learn --feedback "Recruiter wanted Kafka depth" --kind interview

License: MIT
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    import openpyxl
    from openpyxl.formatting.rule import CellIsRule, FormulaRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing dependencies. Run:  pip install -r requirements.txt")

__version__ = "1.0.0"
import os
ROOT = Path(os.environ.get("OFFERS_HOME") or Path(__file__).resolve().parent)  # your workspace folder
TRACKER = ROOT / "tracker" / "OffersOSS_Tracker.xlsx"
PROFILE = ROOT / "profile" / "profile.yaml"
PROFILE_EXAMPLE = ROOT / "profile" / "profile.example.yaml"
PACKETS = ROOT / "packets"
BRAIN = ROOT / "brain"
ANSWERS = BRAIN / "answers.yaml"
INSTINCTS = BRAIN / "instincts.yaml"
LEARNINGS = BRAIN / "learnings.md"
METER = BRAIN / "meter.json"
DATA_JS = ROOT / "dashboard" / "data.js"

COLUMNS = ["ID", "Added", "Company", "Role", "Location", "Source", "URL",
           "Resume", "Fit %", "Matched Skills", "Missing Skills", "Status",
           "Applied On", "Follow-up", "Contact", "Notes"]
WIDTHS = [10, 12, 22, 30, 16, 13, 30, 16, 8, 34, 26, 13, 12, 12, 20, 40]
STATUSES = ["Shortlisted", "Applied", "Viewed", "Screening", "Interview",
            "Offer", "Accepted", "Rejected", "Withdrawn", "Ghosted"]
ACTIVE = {"Shortlisted", "Applied", "Viewed", "Screening", "Interview", "Offer"}
SOURCES = ["LinkedIn", "Naukri", "Instahyre", "Cutshort", "Wellfound", "Indeed",
           "Foundit", "Company site", "Referral", "Recruiter", "Other"]
FOLLOW_UP_DAYS = {"Applied": 7, "Viewed": 4, "Screening": 3, "Interview": 2, "Offer": 2}
GHOST_AFTER_DAYS = 21

# Common tech skills detected in job descriptions ("a|b" = aliases). Profile skills are added on top.
SKILL_BANK = [x.strip() for x in """
java, spring boot|springboot, microservices, hibernate, jpa, rest api|rest apis|restful, graphql, grpc, kafka, rabbitmq,
sql, oracle, mysql, postgresql|postgres, mongodb, redis, elasticsearch, docker, kubernetes|k8s, jenkins, ci/cd,
aws, azure, gcp, terraform, linux, git, maven, gradle, junit, mockito, python, django, flask, fastapi, node.js|nodejs,
typescript, javascript, react, angular, vue, next.js|nextjs, html, css, tailwind, golang|go lang, rust, c++, c#, .net,
llm|llms, genai|generative ai, rag, langchain, openai, claude, ai agents|agentic, prompt engineering, vector database,
pandas, pytorch, tensorflow, machine learning, data structures, system design, oauth, jwt,
enovia, 3dexperience|3dx, plm, tcl, mql, oracle fusion, nokia nsp, sdn, netconf, yang,
agile, scrum, jira, splunk, grafana, prometheus, observability, trigger.dev
""".replace("\n", " ").split(",") if x.strip()]


# ----------------------------------------------------------------- helpers
def today() -> dt.date:
    return dt.date.today()


def die(msg: str) -> None:
    sys.exit(f"offers: {msg}")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def skill_variants(entry: str) -> list[str]:
    return [v.strip().lower() for v in entry.split("|") if v.strip()]


def contains(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def load_profile() -> dict:
    path = PROFILE if PROFILE.exists() else PROFILE_EXAMPLE
    if not path.exists():
        die("no profile found. Run: python offers.py init")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def profile_skills(profile: dict) -> list[str]:
    return [s for s in profile.get("skills", []) if isinstance(s, str)]


def bank(profile: dict) -> list[str]:
    seen, out = set(), []
    for raw in SKILL_BANK + profile_skills(profile):
        key = skill_variants(raw)[0]
        if key not in seen:
            seen.add(key)
            out.append(raw)
    return out


# ----------------------------------------------------------------- scoring
def analyse(jd: str, profile: dict) -> dict:
    """Score a JD against the profile locally. Costs zero AI tokens."""
    text = norm(jd)
    mine = {skill_variants(s)[0]: skill_variants(s) for s in profile_skills(profile)}
    detected, matched, missing = [], [], []
    for raw in bank(profile):
        names = skill_variants(raw)
        if any(contains(text, n) for n in names):
            key = names[0]
            if key in detected:
                continue
            detected.append(key)
            have = key in mine or any(n in v for v in mine.values() for n in names)
            (matched if have else missing).append(key)
    must = [m.lower() for m in profile.get("must_have_any", [])]
    must_ok = not must or any(contains(text, m) for m in must)
    deal = [d for d in profile.get("deal_breakers", []) if contains(text, d.lower())]
    fit = round(100 * len(matched) / len(detected)) if detected else 0
    if not must_ok:
        fit = min(fit, 40)
    if deal:
        fit = min(fit, 20)

    exp = None
    m = re.search(r"(\d{1,2})\s*(?:\+|-|–|to)?\s*(\d{1,2})?\s*\+?\s*(?:years|yrs)", text)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo + 3
        exp = (lo, hi)
    years = float(profile.get("years_experience", 0))
    exp_flag = ""
    if exp and years and years + 1 < exp[0]:
        exp_flag = f"asks {exp[0]}-{exp[1]} yrs, you have {years:g}"

    variant, best = "", -1
    for v in profile.get("resume_variants", []):
        score = sum(1 for k in v.get("keywords", []) if contains(text, k.lower()))
        if score > best:
            variant, best = v.get("name", ""), score
    return {"fit": fit, "detected": detected, "matched": matched, "missing": missing,
            "experience": exp, "experience_flag": exp_flag, "deal_breakers": deal,
            "must_ok": must_ok, "variant": variant}


def jd_excerpt(jd: str, limit: int = 1200) -> str:
    """Keep only requirement-bearing lines: the cheapest useful JD for an AI."""
    keys = re.compile(r"(require|must|experience|skill|responsib|you will|you'll|qualif|"
                      r"nice to have|bonus|stack|years|degree|own|build|design)", re.I)
    lines = [l.strip(" -•*\t") for l in jd.splitlines() if l.strip()]
    keep = [l for l in lines if keys.search(l)] or lines
    out, size = [], 0
    for l in keep:
        if size + len(l) > limit:
            break
        out.append("- " + l)
        size += len(l)
    return "\n".join(out)


def tokens(s: str) -> int:
    return max(1, len(s) // 4)  # good-enough estimate for English across models


# ----------------------------------------------------------------- meter (everything counted)
def meter() -> dict:
    base = {"tokens_saved": 0, "jds_scored": 0, "packets": 0, "answers_reused": 0, "minutes_saved": 0}
    try:
        base.update(json.loads(METER.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return base


def bump(**inc) -> dict:
    m = meter()
    for k, v in inc.items():
        m[k] = m.get(k, 0) + v
    try:
        METER.parent.mkdir(parents=True, exist_ok=True)
        METER.write_text(json.dumps(m, indent=1), encoding="utf-8")
    except OSError:
        pass
    return m


def is_template(answer: str) -> bool:
    return "<" in answer and ">" in answer


def streak(items: list[dict]) -> int:
    days = {r["Applied On"] for r in items if isinstance(r.get("Applied On"), dt.date)}
    n, d = 0, today()
    if d not in days:
        d -= dt.timedelta(days=1)  # today not done yet: streak still alive
    while d in days:
        n, d = n + 1, d - dt.timedelta(days=1)
    return n


# ----------------------------------------------------------------- workbook
THIN = Side(style="thin", color="D9DEE7")
HEAD_FILL = PatternFill("solid", fgColor="111827")
HEAD_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=10)
BODY_FONT = Font(name="Arial", size=10)
STATUS_COLORS = {"Shortlisted": "E0E7FF", "Applied": "DBEAFE", "Viewed": "CFFAFE",
                 "Screening": "FEF3C7", "Interview": "FDE68A", "Offer": "BBF7D0",
                 "Accepted": "86EFAC", "Rejected": "FECACA", "Withdrawn": "E5E7EB",
                 "Ghosted": "F3F4F6"}


def build_workbook(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Applications"
    ws.append(COLUMNS)
    for i, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
        c = ws.cell(row=1, column=i)
        c.font, c.fill = HEAD_FONT, HEAD_FILL
        c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}1"

    lists = wb.create_sheet("Lists")
    lists["A1"], lists["B1"] = "Status", "Source"
    for i, s in enumerate(STATUSES, 2):
        lists.cell(row=i, column=1, value=s)
    for i, s in enumerate(SOURCES, 2):
        lists.cell(row=i, column=2, value=s)
    for c in ("A1", "B1"):
        lists[c].font = HEAD_FONT
        lists[c].fill = HEAD_FILL
    lists.column_dimensions["A"].width = lists.column_dimensions["B"].width = 16

    dv_s = DataValidation(type="list", formula1=f"=Lists!$A$2:$A${len(STATUSES)+1}", allow_blank=True)
    dv_src = DataValidation(type="list", formula1=f"=Lists!$B$2:$B${len(SOURCES)+1}", allow_blank=True)
    ws.add_data_validation(dv_s)
    ws.add_data_validation(dv_src)
    dv_s.add("L2:L2000")
    dv_src.add("F2:F2000")

    for status, color in STATUS_COLORS.items():
        ws.conditional_formatting.add(
            "L2:L2000", CellIsRule(operator="equal", formula=[f'"{status}"'],
                                   fill=PatternFill("solid", fgColor=color)))
    ws.conditional_formatting.add(  # overdue follow-up
        "N2:N2000", FormulaRule(formula=['AND(N2<>"",N2<=TODAY())'],
                                font=Font(name="Arial", bold=True, color="B91C1C")))
    ws.conditional_formatting.add(
        "I2:I2000", FormulaRule(formula=['AND(I2<>"",I2>=70)'],
                                font=Font(name="Arial", bold=True, color="047857")))

    dash = wb.create_sheet("Dashboard", 0)
    dash.column_dimensions["A"].width = 26
    dash.column_dimensions["B"].width = 12
    dash.column_dimensions["C"].width = 12
    dash["A1"] = "Offers OSS - Pipeline"
    dash["A1"].font = Font(name="Arial", bold=True, size=16)
    dash["A2"] = "All numbers are live formulas over the Applications sheet."
    dash["A2"].font = Font(name="Arial", italic=True, color="6B7280", size=9)
    dash["A4"], dash["B4"], dash["C4"] = "Status", "Count", "Share"
    for c in ("A4", "B4", "C4"):
        dash[c].font, dash[c].fill = HEAD_FONT, HEAD_FILL
    r = 5
    for s in STATUSES:
        dash.cell(row=r, column=1, value=s).font = BODY_FONT
        dash.cell(row=r, column=2, value=f'=COUNTIF(Applications!$L:$L,A{r})').font = BODY_FONT
        dash.cell(row=r, column=1).fill = PatternFill("solid", fgColor=STATUS_COLORS[s])
        r += 1
    total_row = r
    dash.cell(row=r, column=1, value="Total").font = Font(name="Arial", bold=True)
    dash.cell(row=r, column=2, value=f"=SUM(B5:B{r-1})").font = Font(name="Arial", bold=True)
    for rr in range(5, total_row):  # fix share formulas to point at the total row
        dash.cell(row=rr, column=3, value=f"=IF($B${total_row}=0,0,B{rr}/$B${total_row})").number_format = "0%"

    k = total_row + 2
    kpis = [
        ("Applications sent", '=COUNTIF(Applications!$M:$M,">0")', "0"),
        ("Response rate", f'=IF(B{k}=0,0,(COUNTIF(Applications!$L:$L,"Viewed")+COUNTIF(Applications!$L:$L,"Screening")'
                          f'+COUNTIF(Applications!$L:$L,"Interview")+COUNTIF(Applications!$L:$L,"Offer")'
                          f'+COUNTIF(Applications!$L:$L,"Accepted"))/B{k})', "0%"),
        ("Interview rate", f'=IF(B{k}=0,0,(COUNTIF(Applications!$L:$L,"Interview")+COUNTIF(Applications!$L:$L,"Offer")'
                           f'+COUNTIF(Applications!$L:$L,"Accepted"))/B{k})', "0%"),
        ("Average fit %", '=IFERROR(AVERAGE(Applications!$I:$I)/100,0)', "0%"),
        ("Follow-ups due", '=COUNTIFS(Applications!$N:$N,"<="&TODAY(),Applications!$N:$N,">0")', "0"),
    ]
    dash.cell(row=k - 1, column=1, value="Key metrics").font = Font(name="Arial", bold=True, size=12)
    for i, (label, formula, fmt) in enumerate(kpis):
        dash.cell(row=k + i, column=1, value=label).font = BODY_FONT
        c = dash.cell(row=k + i, column=2, value=formula)
        c.number_format, c.font = fmt, Font(name="Arial", bold=True)

    guide = wb.create_sheet("Guide")
    guide.column_dimensions["A"].width = 110
    rows = [
        "HOW TO USE THIS TRACKER",
        "1. You can edit the Applications sheet by hand OR let `python offers.py` write to it. Both are fine.",
        "2. Editable columns: everything on Applications. Status and Source have drop-downs (from the Lists sheet).",
        "3. Do not edit the Dashboard sheet: every number there is a formula.",
        "4. Fit % is computed locally from your profile.yaml skills vs the job description (0 AI tokens).",
        "5. Follow-up is set automatically when you change Status with the CLI: Applied +7d, Viewed +4d, Screening +3d, Interview/Offer +2d.",
        "6. Red bold follow-up date = overdue. Green bold Fit % = 70 or higher.",
        "7. Run `python offers.py export` to refresh the HTML dashboard (dashboard/index.html).",
        "Example row format: OF-0001 | 2026-11-14 | Acme Corp | Java Developer | Bengaluru | Naukri | https://... | java | 82 | java, spring boot | kubernetes | Applied | 2026-11-14 | 2026-11-21 | Priya (HR) | Referral",
    ]
    for i, t in enumerate(rows, 1):
        guide.cell(row=i, column=1, value=t).font = Font(name="Arial", bold=(i == 1), size=12 if i == 1 else 10)

    for sheet in (ws, dash, guide):  # print-ready: landscape, one page wide
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth, sheet.page_setup.fitToHeight = 1, 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
    wb.calculation.fullCalcOnLoad = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def open_tracker():
    if not TRACKER.exists():
        die("tracker not found. Run: python offers.py init")
    wb = openpyxl.load_workbook(TRACKER)
    return wb, wb["Applications"]


def rows(ws) -> list[dict]:
    out = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r or not r[0]:
            continue
        d = dict(zip(COLUMNS, r))
        for k in ("Added", "Applied On", "Follow-up"):
            if isinstance(d.get(k), dt.datetime):
                d[k] = d[k].date()
        out.append(d)
    return out


def find_row(ws, job_id: str) -> int:
    for i, r in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=True), 2):
        if r[0] and str(r[0]).upper() == job_id.upper():
            return i
    die(f"no job with ID {job_id}")
    return -1


def next_id(ws) -> str:
    n = 0
    for r in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        if r[0] and str(r[0]).startswith("OF-"):
            n = max(n, int(str(r[0])[3:]))
    return f"OF-{n + 1:04d}"


def write_row(ws, idx: int, d: dict) -> None:
    for c, col in enumerate(COLUMNS, 1):
        cell = ws.cell(row=idx, column=c, value=d.get(col))
        cell.font = BODY_FONT
        cell.border = Border(bottom=THIN)
        if col in ("Added", "Applied On", "Follow-up") and d.get(col):
            cell.number_format = "yyyy-mm-dd"
        if col in ("Notes", "Matched Skills", "Missing Skills", "Role"):
            cell.alignment = Alignment(wrap_text=False)


# ----------------------------------------------------------------- commands
def cmd_init(a) -> None:
    if TRACKER.exists() and not a.force:
        print(f"Tracker already exists: {TRACKER.relative_to(ROOT)} (use --force to rebuild)")
    else:
        build_workbook(TRACKER)
        print(f"Created {TRACKER.relative_to(ROOT)}")
    if not PROFILE.exists():
        PROFILE.write_text(PROFILE_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Created {PROFILE.relative_to(ROOT)}  <- edit this with your real skills")
    for live, example in ((ANSWERS, BRAIN / "answers.example.yaml"), (LEARNINGS, BRAIN / "learnings.example.md")):
        if not live.exists() and example.exists():
            live.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Created {live.relative_to(ROOT)}")
    for d in ("packets", "jobs/jds"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    print("Next: edit profile/profile.yaml, then `python offers.py add ...` or `import jobs/inbox.csv`")


def add_job(ws, existing: list[dict], profile: dict, *, company: str, role: str, jd: str,
            url: str = "", source: str = "Other", location: str = "", contact: str = "",
            notes: str = "", status: str = "Shortlisted") -> dict | None:
    for e in existing:
        if (url and e.get("URL") == url) or (norm(e.get("Company") or "") == norm(company)
                                              and norm(e.get("Role") or "") == norm(role)):
            print(f"  skip duplicate: {company} - {role} (already {e['ID']})")
            return None
    an = analyse(jd, profile)
    bump(jds_scored=1, tokens_saved=tokens(jd) + 300, minutes_saved=3)
    job_id = next_id(ws)
    flags = "; ".join(x for x in [an["experience_flag"],
                                  "deal-breaker: " + ", ".join(an["deal_breakers"]) if an["deal_breakers"] else "",
                                  "" if an["must_ok"] else "no must-have skill found"] if x)
    d = {"ID": job_id, "Added": today(), "Company": company, "Role": role, "Location": location,
         "Source": source, "URL": url, "Resume": an["variant"], "Fit %": an["fit"],
         "Matched Skills": ", ".join(an["matched"]), "Missing Skills": ", ".join(an["missing"]),
         "Status": status, "Applied On": None, "Follow-up": None, "Contact": contact,
         "Notes": " | ".join(x for x in [notes, flags] if x)}
    write_row(ws, ws.max_row + 1, d)
    existing.append(d)
    if jd:
        (ROOT / "jobs" / "jds").mkdir(parents=True, exist_ok=True)
        (ROOT / "jobs" / "jds" / f"{job_id}.txt").write_text(jd, encoding="utf-8")
    return d


def cmd_add(a) -> None:
    profile = load_profile()
    jd = Path(a.jd).read_text(encoding="utf-8") if a.jd and Path(a.jd).exists() else (a.jd or "")
    wb, ws = open_tracker()
    d = add_job(ws, rows(ws), profile, company=a.company, role=a.role, jd=jd, url=a.url or "",
                source=a.source, location=a.location or "", contact=a.contact or "", notes=a.note or "")
    wb.save(TRACKER)
    if d:
        print(f"Added {d['ID']}  {d['Company']} - {d['Role']}  fit {d['Fit %']}%  resume: {d['Resume'] or '-'}")
        if d["Notes"]:
            print(f"  note: {d['Notes']}")


def cmd_import(a) -> None:
    profile = load_profile()
    wb, ws = open_tracker()
    existing = rows(ws)
    added = 0
    with open(a.csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            jd = r.get("jd", "")
            if r.get("jd_file") and Path(r["jd_file"]).exists():
                jd = Path(r["jd_file"]).read_text(encoding="utf-8")
            if not r.get("company") or not r.get("role"):
                continue
            d = add_job(ws, existing, profile, company=r["company"], role=r["role"], jd=jd,
                        url=r.get("url", ""), source=r.get("source") or "Other",
                        location=r.get("location", ""), contact=r.get("contact", ""), notes=r.get("notes", ""))
            if d:
                added += 1
                print(f"  + {d['ID']}  {d['Fit %']:>3}%  {d['Company']} - {d['Role']}")
    wb.save(TRACKER)
    print(f"Imported {added} job(s).")


def table(items: list[dict], cols: list[str]) -> str:
    if not items:
        return "  (nothing here)"
    w = {c: max(len(c), *(len(str(i.get(c) or "")) for i in items)) for c in cols}
    w = {c: min(v, 34) for c, v in w.items()}
    line = "  " + "  ".join(c.ljust(w[c]) for c in cols)
    out = [line, "  " + "  ".join("-" * w[c] for c in cols)]
    for i in items:
        out.append("  " + "  ".join(str(i.get(c) or "")[: w[c]].ljust(w[c]) for c in cols))
    return "\n".join(out)


def load_instincts() -> dict:
    return (yaml.safe_load(INSTINCTS.read_text(encoding="utf-8")) or {}) if INSTINCTS.exists() else {}


def cmd_triage(a) -> None:
    _, ws = open_tracker()
    ins = load_instincts()
    a.min = a.min if a.min is not None else int(ins.get("min_fit", 50))
    a.top = a.top if a.top is not None else int(ins.get("daily_application_cap", 15))
    items = [r for r in rows(ws) if r["Status"] == "Shortlisted" and (r["Fit %"] or 0) >= a.min]
    items.sort(key=lambda r: -(r["Fit %"] or 0))
    print(f"Shortlisted jobs with fit >= {a.min}%  (apply top-down; scored locally, 0 tokens)\n")
    print(table(items[: a.top], ["ID", "Fit %", "Company", "Role", "Resume", "Missing Skills"]))


def cmd_list(a) -> None:
    _, ws = open_tracker()
    items = rows(ws)
    if a.status:
        items = [r for r in items if (r["Status"] or "").lower() == a.status.lower()]
    print(table(items, ["ID", "Status", "Fit %", "Company", "Role", "Source", "Follow-up"]))


def cmd_packet(a) -> None:
    profile = load_profile()
    _, ws = open_tracker()
    r = next((x for x in rows(ws) if str(x["ID"]).upper() == a.id.upper()), None)
    if not r:
        die(f"no job with ID {a.id}")
    jd_path = ROOT / "jobs" / "jds" / f"{r['ID']}.txt"
    jd = jd_path.read_text(encoding="utf-8") if jd_path.exists() else ""
    task = a.task
    tpl = (ROOT / "prompts" / f"{task}.md").read_text(encoding="utf-8")
    facts = "\n".join(f"- {x}" for x in profile.get("facts", []))
    variant = next((v for v in profile.get("resume_variants", []) if v.get("name") == r["Resume"]), {})
    card = (f"Company: {r['Company']} | Role: {r['Role']} | Location: {r['Location'] or '-'}\n"
            f"Fit: {r['Fit %']}% | Matched: {r['Matched Skills'] or '-'} | Gaps: {r['Missing Skills'] or '-'}\n"
            f"Resume variant: {r['Resume'] or '-'} ({variant.get('file', '')})")
    body = tpl.replace("{{CANDIDATE}}", f"{profile.get('headline', '')}\n{facts}") \
              .replace("{{JOB_CARD}}", card) \
              .replace("{{JD_EXCERPT}}", jd_excerpt(jd) or "(no JD saved - paste key requirements here)")
    PACKETS.mkdir(exist_ok=True)
    out = PACKETS / f"{r['ID']}-{task}.md"
    out.write_text(body, encoding="utf-8")
    raw = tokens(jd) + tokens(profile.get("resume_text", "") or "x" * 9000)
    bump(packets=1, tokens_saved=max(0, raw - tokens(body)), minutes_saved=12)
    print(body)
    print(f"\n--- saved {out.relative_to(ROOT)} | ~{tokens(body)} tokens "
          f"(vs ~{raw} pasting full resume + JD: {100 - round(100 * tokens(body) / raw)}% saved)")


def cmd_status(a) -> None:
    status = next((s for s in STATUSES if s.lower() == a.status.lower()), None)
    if not status:
        die(f"status must be one of: {', '.join(STATUSES)}")
    wb, ws = open_tracker()
    i = find_row(ws, a.id)
    col = {c: n for n, c in enumerate(COLUMNS, 1)}
    ws.cell(row=i, column=col["Status"], value=status)
    if status == "Applied" and not ws.cell(row=i, column=col["Applied On"]).value:
        c = ws.cell(row=i, column=col["Applied On"], value=today())
        c.number_format = "yyyy-mm-dd"
    days = FOLLOW_UP_DAYS.get(status)
    f = ws.cell(row=i, column=col["Follow-up"])
    f.value = (today() + dt.timedelta(days=days)) if days else None  # cell(value=None) would not clear it
    f.number_format = "yyyy-mm-dd"
    if a.note:
        old = ws.cell(row=i, column=col["Notes"]).value or ""
        ws.cell(row=i, column=col["Notes"], value=(old + " | " if old else "") + f"{today()}: {a.note}")
    if a.contact:
        ws.cell(row=i, column=col["Contact"], value=a.contact)
    wb.save(TRACKER)
    print(f"{a.id.upper()} -> {status}" + (f"  (follow up on {f.value})" if f.value else ""))


def cmd_due(a) -> None:
    _, ws = open_tracker()
    t = today()
    due = [r for r in rows(ws) if r["Follow-up"] and r["Follow-up"] <= t and r["Status"] in ACTIVE]
    ghost = [r for r in rows(ws) if r["Status"] == "Applied" and r["Applied On"]
             and (t - r["Applied On"]).days >= GHOST_AFTER_DAYS]
    print(f"Follow-ups due ({len(due)}):\n" + table(due, ["ID", "Status", "Company", "Role", "Follow-up", "Contact"]))
    if ghost:
        print(f"\nNo reply in {GHOST_AFTER_DAYS}+ days - consider `status <ID> Ghosted`:")
        print(table(ghost, ["ID", "Company", "Role", "Applied On"]))
    print("\nTip: `python offers.py packet <ID> --task follow-up` drafts the message.")


def summary(items: list[dict]) -> dict:
    counts = {s: sum(1 for r in items if r["Status"] == s) for s in STATUSES}
    sent = sum(1 for r in items if r["Applied On"])
    responded = sum(counts[s] for s in ("Viewed", "Screening", "Interview", "Offer", "Accepted"))
    interviews = sum(counts[s] for s in ("Interview", "Offer", "Accepted"))
    fits = [r["Fit %"] for r in items if isinstance(r["Fit %"], (int, float))]
    return {"total": len(items), "sent": sent, "counts": counts,
            "response_rate": round(100 * responded / sent) if sent else 0,
            "interview_rate": round(100 * interviews / sent) if sent else 0,
            "avg_fit": round(sum(fits) / len(fits)) if fits else 0}


def cmd_stats(a) -> None:
    _, ws = open_tracker()
    items = rows(ws)
    s = summary(items)
    print(banner(items) + "\n")
    print(f"Offers OSS pipeline  -  {s['total']} jobs tracked, {s['sent']} applications sent")
    print(f"Response rate {s['response_rate']}%  |  Interview rate {s['interview_rate']}%  |  Avg fit {s['avg_fit']}%\n")
    peak = max(s["counts"].values()) or 1
    for st, n in s["counts"].items():
        print(f"  {st:<12} {'#' * round(28 * n / peak):<28} {n}")


def cmd_export(a) -> None:
    _, ws = open_tracker()
    profile = load_profile()
    items = rows(ws)
    data = {"generated": dt.datetime.now().isoformat(timespec="minutes"),
            "owner": profile.get("display_name", "Candidate"),
            "brand": {"product": "Offers OSS", "by": "Idharyn Labs", "tagline": "Guarded by Frost. Driven by Heart."},
            "statuses": STATUSES, "active": sorted(ACTIVE, key=STATUSES.index),
            "replied": ["Viewed", "Screening", "Interview", "Offer", "Accepted"],
            "interviewing": ["Interview", "Offer", "Accepted"], "won": ["Offer", "Accepted"],
            "tracker": {"name": TRACKER.name, "path": str(TRACKER), "uri": TRACKER.resolve().as_uri(),
                        "sheet": "Applications",
                        "rows": {str(r[0]): i for i, r in enumerate(ws.iter_rows(min_row=2, max_col=1, values_only=True), 2) if r[0]}},
            "summary": summary(items),
            "meter": meter(),
            "streak": streak(items),
            "applied_today": sum(1 for r in items if r.get("Applied On") == today()),
            "daily_goal": int(load_instincts().get("daily_application_cap", 15)),
            "brain": brain_coverage(),
            "next": next_actions(items),
            "jobs": [{k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in r.items()} for r in items]}
    DATA_JS.parent.mkdir(exist_ok=True)
    DATA_JS.write_text("window.OFFEROS_DATA = " + json.dumps(data, indent=1, default=str) + ";\n", encoding="utf-8")
    print(f"Wrote {DATA_JS.relative_to(ROOT)} ({len(items)} jobs). Open dashboard/index.html in any browser.")


# ----------------------------------------------------------------- second brain
STOP = set("a an the is are do does did you your yours what why how when where which to of in on for and or with "
           "be can could would will please tell me about we our us it this that from".split())


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9+#.]+", s.lower()) if w not in STOP and len(w) > 1}


def load_answers() -> list[dict]:
    path = ANSWERS if ANSWERS.exists() else BRAIN / "answers.example.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or []) if path.exists() else []


def best_answer(question: str, bank_: list[dict]) -> tuple[dict | None, float]:
    q = words(question)
    best, score = None, 0.0
    for e in bank_:
        for pattern in [e.get("q", "")] + e.get("also", []):
            p = words(pattern)
            if not p or not q:
                continue
            sc = len(q & p) / len(q | p)
            if sc > score:
                best, score = e, sc
    return best, score


def cmd_answer(a) -> None:
    """Answer a screening/recruiter question from your saved answers. 0 tokens."""
    e, sc = best_answer(a.question, load_answers())
    if not e or sc < 0.2:
        print("Not in your second brain yet. Answer it once, then save it:\n"
              f'  python offers.py learn --q "{a.question}" --a "<your answer>"')
        return
    print(f"[{e.get('id', '?')}] match {round(sc * 100)}%  (updated {e.get('updated', '-')})\n")
    print(e["a"].strip())
    if is_template(e["a"]):
        print("\n(!) still a template - fill it once with `python offers.py brain`")
    else:
        bump(answers_reused=1, tokens_saved=150, minutes_saved=2)
    if e.get("tip"):
        print(f"\ntip: {e['tip']}")


def cmd_learn(a) -> None:
    """Grow the second brain: saved answers, feedback, interview learnings."""
    BRAIN.mkdir(exist_ok=True)
    if a.q and a.a:
        bank_ = load_answers()
        e, sc = best_answer(a.q, bank_)
        if e and sc >= 0.6:
            e["a"], e["updated"] = a.a, str(today())
            print(f"Updated answer [{e.get('id')}]")
        else:
            nums = [int(x["id"][1:]) for x in bank_ if str(x.get("id", "")).startswith("A") and str(x["id"])[1:].isdigit()]
            new_id = f"A{max(nums, default=0) + 1:02d}"
            bank_.append({"id": new_id, "q": a.q, "also": [], "a": a.a, "updated": str(today())})
            print(f"Saved new answer [{new_id}]")
        ANSWERS.write_text(yaml.safe_dump(bank_, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    if a.feedback:
        tag = f" [{a.job}]" if a.job else ""
        with LEARNINGS.open("a", encoding="utf-8") as f:
            f.write(f"- {today()}{tag} ({a.kind}): {a.feedback}\n")
        print(f"Logged {a.kind} to {LEARNINGS.relative_to(ROOT)}")
    if not ((a.q and a.a) or a.feedback):
        die('give --q and --a, or --feedback "..."')


def brain_coverage() -> dict:
    bank_ = load_answers()
    done = sum(1 for e in bank_ if not is_template(str(e.get("a", ""))))
    return {"answered": done, "total": len(bank_)}


def save_answers(bank_: list[dict]) -> None:
    BRAIN.mkdir(exist_ok=True)
    ANSWERS.write_text(yaml.safe_dump(bank_, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")


def ask(prompt: str, default: str = "") -> str:
    try:
        v = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    except EOFError:
        v = ""
    return v or default


def cmd_brain(a) -> None:
    """Fill unanswered common questions one at a time. Enter = skip, q = stop."""
    bank_ = load_answers()
    todo = [e for e in bank_ if is_template(str(e.get("a", "")))]
    cov = brain_coverage()
    print(f"Second brain: {cov['answered']}/{cov['total']} common questions answered.\n")
    if a.list or not todo:
        for e in bank_:
            mark = "  " if is_template(str(e["a"])) else "✓ "
            print(f"  {mark}[{e['id']}] {e['q']}")
        if not todo:
            print("\nAll answered. Forms will take seconds now.")
        return
    print("Answer in your own words. Enter = skip, q = save & stop.\n")
    n = 0
    for e in todo:
        print(f"[{e['id']}] {e['q']}\n   hint: {e['a']}" + (f"\n   tip:  {e['tip']}" if e.get("tip") else ""))
        v = ask("   you")
        if v.lower() == "q":
            break
        if v:
            e["a"], e["updated"] = v, str(today())
            n += 1
        print()
    save_answers(bank_)
    cov = brain_coverage()
    print(f"Saved {n}. Coverage now {cov['answered']}/{cov['total']}.")


def cmd_setup(a) -> None:
    """Six questions -> a working profile. Everything else is optional."""
    if not TRACKER.exists() or not PROFILE.exists():
        cmd_init(argparse.Namespace(force=False))
    p = load_profile()
    print("\nOffers OSS setup - 6 questions, about 2 minutes. Enter keeps the value in [brackets].\n")
    p["display_name"] = ask("1/6  Your name (shown only on your dashboard)", p.get("display_name", ""))
    p["headline"] = ask("2/6  Target headline (role | top skills | years)", p.get("headline", ""))
    p["years_experience"] = float(ask("3/6  Years of experience", str(p.get("years_experience", 0))) or 0)
    sk = ask("4/6  Skills you can defend, comma separated", ", ".join(s.split("|")[0] for s in profile_skills(p)))
    p["skills"] = [x.strip() for x in sk.split(",") if x.strip()]
    p["notice_period"] = ask("5/6  Notice period", p.get("notice_period", "Immediate"))
    p["location"] = ask("6/6  Current location", p.get("location", ""))
    PROFILE.write_text(yaml.safe_dump(p, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    bank_ = load_answers()
    for e in bank_:  # pre-fill the brain from setup answers
        if e["id"] == "A01" and is_template(e["a"]):
            e["a"] = f"My notice period is {p['notice_period']}." if p["notice_period"].lower() != "immediate" else "I can join immediately."
        if e["id"] == "A13" and is_template(e["a"]) and p["location"]:
            e["a"] = p["location"]
    save_answers(bank_)
    cov = brain_coverage()
    print(f"\nDone. Profile saved, {len(p['skills'])} skills, brain {cov['answered']}/{cov['total']}.")
    print("Next: `python offers.py brain` (fill common questions once)  then  `python offers.py go`.")


def next_actions(items: list[dict]) -> list[dict]:
    t = today()
    acts = []
    due = [r for r in items if r["Follow-up"] and r["Follow-up"] <= t and r["Status"] in ACTIVE]
    if due:
        acts.append({"label": f"Send {len(due)} follow-up(s)", "cmd": "python offers.py due"})
    top = sorted([r for r in items if r["Status"] == "Shortlisted"], key=lambda r: -(r["Fit %"] or 0))
    if top:
        r = top[0]
        acts.append({"label": f"Apply: {r['Company']} - {r['Role']} ({r['Fit %']}%)", "cmd": f"python offers.py packet {r['ID']}"})
    cov = brain_coverage()
    if cov["answered"] < cov["total"]:
        acts.append({"label": f"Fill {cov['total'] - cov['answered']} common answers once", "cmd": "python offers.py brain"})
    if (ROOT / "jobs" / "inbox.csv").exists():
        acts.append({"label": "Import new jobs from inbox", "cmd": "python offers.py import jobs/inbox.csv"})
    return acts[:4]


def banner(items: list[dict]) -> str:
    m, s, cov = meter(), summary(items), brain_coverage()
    goal = int(load_instincts().get("daily_application_cap", 15))
    done = sum(1 for r in items if r.get("Applied On") == today())
    bar = "█" * min(10, round(10 * done / goal)) + "░" * (10 - min(10, round(10 * done / goal)))
    return (f"  Today  {bar} {done}/{goal} applied   streak {streak(items)}d   follow-ups due "
            f"{sum(1 for r in items if r['Follow-up'] and r['Follow-up'] <= today() and r['Status'] in ACTIVE)}\n"
            f"  Total  {s['sent']} sent · {s['response_rate']}% replies · {s['interview_rate']}% interviews   "
            f"brain {cov['answered']}/{cov['total']}\n"
            f"  Saved  ~{m['tokens_saved']:,} tokens · ~{m['minutes_saved'] // 60}h {m['minutes_saved'] % 60}m · "
            f"{m['jds_scored']} JDs scored locally · {m['answers_reused']} answers reused")


def cmd_go(a) -> None:
    """The cockpit: one command, numbered choices, you stay in control."""
    while True:
        _, ws = open_tracker()
        items = rows(ws)
        print("\n◆ Offers OSS cockpit\n" + banner(items) + "\n")
        acts = next_actions(items)
        for i, x in enumerate(acts, 1):
            print(f"  [{i}] {x['label']}")
        print("  [a] mark a job Applied   [s] change a status   [d] dashboard   [q] quit")
        c = ask("\nchoose").lower()
        if c in ("q", ""):
            print("See you tomorrow. Consistency beats volume.")
            return
        if c.isdigit() and 1 <= int(c) <= len(acts):
            argv = acts[int(c) - 1]["cmd"].split()[2:]
            main(argv)
        elif c == "a":
            main(["status", ask("job ID (e.g. OF-0007)"), "Applied", "--note", ask("what you sent (optional)") or "applied"])
        elif c == "s":
            main(["status", ask("job ID"), ask("new status (" + "/".join(STATUSES) + ")")])
        elif c == "d":
            cmd_export(a)
            print(f"Open: {(ROOT / 'dashboard' / 'index.html').as_uri()}")
        if a.once:
            return


def cmd_open(a) -> None:
    """Open the Excel tracker in your spreadsheet app (Excel, Numbers, LibreOffice)."""
    import os
    import subprocess
    if not TRACKER.exists():
        die("tracker not found. Run: python offers.py init")
    print(f"Opening {TRACKER}" + (f"  -> look at row {find_row(open_tracker()[1], a.id)} for {a.id.upper()}" if a.id else ""))
    if sys.platform.startswith("win"):
        os.startfile(TRACKER)  # type: ignore[attr-defined]
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(TRACKER)], check=False)


def cmd_doctor(a) -> None:
    ok = True
    for label, p in [("tracker", TRACKER), ("profile", PROFILE), ("prompts", ROOT / "prompts"),
                     ("dashboard", ROOT / "dashboard" / "index.html"), ("brain", ANSWERS),
                     ("instincts", INSTINCTS), ("skills", ROOT / "skills")]:
        exists = p.exists()
        ok &= exists
        print(f"  [{'ok' if exists else '!!'}] {label:<10} {p.relative_to(ROOT)}")
    if PROFILE.exists():
        pr = load_profile()
        n = len(profile_skills(pr))
        print(f"  [{'ok' if n >= 5 else '!!'}] skills     {n} listed in profile.yaml")
        print(f"  [{'ok' if pr.get('resume_variants') else '!!'}] variants   {len(pr.get('resume_variants', []))} resume variant(s)")
    print("All good." if ok else "Run `python offers.py init` to fix missing items.")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="offers", description="Offers OSS - compliant, AI-agnostic job-hunt OS")
    p.add_argument("--version", action="version", version=f"Offers OSS {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create tracker + profile"); s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("add", help="add one job and score it")
    s.add_argument("--company", required=True); s.add_argument("--role", required=True)
    s.add_argument("--jd", help="path to JD text file, or the JD text itself")
    s.add_argument("--url"); s.add_argument("--source", default="Other", choices=SOURCES)
    s.add_argument("--location"); s.add_argument("--contact"); s.add_argument("--note")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("import", help="bulk add jobs from CSV"); s.add_argument("csv"); s.set_defaults(fn=cmd_import)
    s = sub.add_parser("triage", help="best-fit shortlisted jobs first")
    s.add_argument("--min", type=int); s.add_argument("--top", type=int)
    s.set_defaults(fn=cmd_triage)
    s = sub.add_parser("list", help="list jobs"); s.add_argument("--status"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("packet", help="token-lean prompt for any AI"); s.add_argument("id")
    s.add_argument("--task", default="tailor",
                   choices=["tailor", "cover-note", "recruiter-message", "screening-answers", "follow-up", "interview-prep"])
    s.set_defaults(fn=cmd_packet)
    s = sub.add_parser("status", help="update status (sets follow-up date)")
    s.add_argument("id"); s.add_argument("status"); s.add_argument("--note"); s.add_argument("--contact")
    s.set_defaults(fn=cmd_status)
    sub.add_parser("due", help="follow-ups due + ghosted").set_defaults(fn=cmd_due)
    sub.add_parser("stats", help="pipeline summary").set_defaults(fn=cmd_stats)
    sub.add_parser("export", help="refresh dashboard/data.js").set_defaults(fn=cmd_export)
    s = sub.add_parser("setup", help="6-question guided setup"); s.set_defaults(fn=cmd_setup)
    s = sub.add_parser("go", help="daily cockpit with numbered choices"); s.add_argument("--once", action="store_true")
    s.set_defaults(fn=cmd_go)
    s = sub.add_parser("brain", help="fill unanswered common questions once"); s.add_argument("--list", action="store_true")
    s.set_defaults(fn=cmd_brain)
    s = sub.add_parser("answer", help="answer a common question from your second brain")
    s.add_argument("question"); s.set_defaults(fn=cmd_answer)
    s = sub.add_parser("learn", help="save an answer or log feedback/learnings")
    s.add_argument("--q"); s.add_argument("--a"); s.add_argument("--feedback"); s.add_argument("--job")
    s.add_argument("--kind", default="feedback", choices=["feedback", "interview", "rejection", "instinct", "company"])
    s.set_defaults(fn=cmd_learn)
    s = sub.add_parser("open", help="open the Excel tracker"); s.add_argument("id", nargs="?"); s.set_defaults(fn=cmd_open)
    sub.add_parser("doctor", help="check your setup").set_defaults(fn=cmd_doctor)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
