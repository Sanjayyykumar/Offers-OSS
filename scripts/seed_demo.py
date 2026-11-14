#!/usr/bin/env python3
"""Fill the tracker with realistic demo data so you can try Offers OSS in 10 seconds.

    python scripts/seed_demo.py            # adds ~24 fictional jobs across all stages
    python offeros.py export               # then open dashboard/index.html

Companies are fictional. Delete tracker/OffersOSS_Tracker.xlsx and re-run `init` to start clean.
"""
import datetime as dt
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import offeros as o  # noqa: E402

random.seed(7)
JDS = {
    "java": "3-5 years Java, Spring Boot, Microservices, Kafka, REST API, SQL. Docker and AWS nice to have. You will own services end to end.",
    "ai": "Build AI agents with LLM, RAG, prompt engineering, Python or Java. 2+ years. Experience with Claude or OpenAI APIs required.",
    "plm": "3+ years ENOVIA 3DEXPERIENCE customisation, Java, TCL, MQL, PLM data model. Must have JPA knowledge.",
    "support": "L2 application support and integration, Oracle Fusion, SQL, incident management, Java basics, Jenkins, Splunk.",
    "stretch": "6-9 years Go, Kubernetes, Terraform, system design, gRPC, Rust. Must lead a team of 8.",
}
JOBS = [
    ("Zentrix Payments", "Senior Java Developer", "java", "Naukri", "Interview"),
    ("Corvo Health", "Backend Engineer - Spring Boot", "java", "LinkedIn", "Screening"),
    ("Lumen Retail", "Java Microservices Engineer", "java", "Company site", "Applied"),
    ("Quasar Labs", "Founding Engineer - AI Agents", "ai", "Wellfound", "Interview"),
    ("Northwind Cloud", "GenAI Application Engineer", "ai", "Instahyre", "Viewed"),
    ("Helix PLM Services", "ENOVIA 3DX Developer", "plm", "Company site", "Offer"),
    ("Arcadia Motors", "PLM Integration Engineer", "plm", "Referral", "Screening"),
    ("Brightpath Logistics", "Application Support Engineer L2", "support", "Naukri", "Rejected"),
    ("Kestrel Fintech", "Java Full Stack Developer", "java", "Cutshort", "Applied"),
    ("Orbit Commerce", "Software Engineer - Kafka", "java", "LinkedIn", "Ghosted"),
    ("Pinecrest AI", "LLM Engineer", "ai", "Recruiter", "Applied"),
    ("Vela Systems", "Integration Engineer - Oracle Fusion", "support", "Foundit", "Viewed"),
    ("Granite Bank", "Java Developer (Payments)", "java", "Naukri", "Applied"),
    ("Sora Robotics", "Platform Engineer", "stretch", "LinkedIn", "Rejected"),
    ("Monsoon Media", "AI Workflow Engineer", "ai", "Company site", "Applied"),
    ("Tessera Networks", "Java Developer - Networking", "java", "Referral", "Interview"),
    ("Juniper Grove", "Spring Boot Engineer", "java", "Instahyre", "Shortlisted"),
    ("Atlas Aero", "3DEXPERIENCE Consultant", "plm", "Naukri", "Shortlisted"),
    ("Fable Learning", "Agentic AI Developer", "ai", "Wellfound", "Shortlisted"),
    ("Cobalt Insurance", "Backend Java Engineer", "java", "Company site", "Shortlisted"),
    ("Rivet Infra", "Staff SRE", "stretch", "LinkedIn", "Shortlisted"),
    ("Delta Grid", "Application Integration Engineer", "support", "Cutshort", "Withdrawn"),
    ("Saffron Foods Tech", "Java Developer", "java", "Naukri", "Applied"),
    ("Ember Analytics", "AI Engineer - RAG", "ai", "Referral", "Screening"),
]


def main(name: str = "Your Name") -> None:
    if not o.TRACKER.exists():
        o.build_workbook(o.TRACKER)
    profile = o.load_profile()
    wb, ws = o.open_tracker()
    existing = o.rows(ws)
    t = o.today()
    col = {c: i for i, c in enumerate(o.COLUMNS, 1)}
    for i, (co, role, kind, src, status) in enumerate(JOBS):
        d = o.add_job(ws, existing, profile, company=co, role=role, jd=JDS[kind], source=src,
                      url=f"https://example.com/jobs/{i + 1}", location=random.choice(["Bengaluru", "Remote", "Pune", "Hyderabad"]))
        if not d:
            continue
        r = ws.max_row
        added = t - dt.timedelta(days=random.randint(2, 28))
        ws.cell(row=r, column=col["Added"], value=added).number_format = "yyyy-mm-dd"
        ws.cell(row=r, column=col["Status"], value=status)
        if status != "Shortlisted":
            ap = added + dt.timedelta(days=random.randint(0, 2))
            ws.cell(row=r, column=col["Applied On"], value=ap).number_format = "yyyy-mm-dd"
            days = o.FOLLOW_UP_DAYS.get(status)
            if days:
                fu = min(t + dt.timedelta(days=3), ap + dt.timedelta(days=days + random.randint(0, 6)))
                ws.cell(row=r, column=col["Follow-up"], value=fu).number_format = "yyyy-mm-dd"
    wb.save(o.TRACKER)
    print(f"Seeded {len(JOBS)} demo jobs into {o.TRACKER.relative_to(o.ROOT)}")


if __name__ == "__main__":
    main()
