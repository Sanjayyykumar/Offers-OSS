---
name: offeros-daily-run
description: Run the daily Offers OSS job-hunt loop - import new jobs, triage by fit, prepare the top applications, update the tracker and dashboard. Use when the user says "start my job hunt", "daily run", "apply today" or "what should I apply to".
---
# Daily run (30-45 min for the human, ~3-6k tokens for the AI)

1. `python offeros.py due` - handle follow-ups first (they convert better than new applications).
2. Ask the human for today's new job links/JDs, or read `jobs/inbox.csv`. Run `python offeros.py import jobs/inbox.csv`.
3. `python offeros.py triage` - work top-down. Respect `brain/instincts.yaml` (min_fit, daily cap).
4. For each chosen job: `python offeros.py packet <ID> --task tailor` and answer the packet. Do not read the full resume or JD again - the packet already has what is needed.
5. Use the `offeros-browser-assist` skill to fill the form. The human clicks Submit.
6. `python offeros.py status <ID> Applied --note "<what was sent>"`.
7. End: `python offeros.py export` and show `python offeros.py stats`.
