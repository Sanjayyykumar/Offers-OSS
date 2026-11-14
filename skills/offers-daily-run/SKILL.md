---
name: offers-daily-run
description: Run the daily Offers OSS job-hunt loop - import new jobs, triage by fit, prepare the top applications, update the tracker and dashboard. Use when the user says "start my job hunt", "daily run", "apply today" or "what should I apply to".
---
# Daily run (30-45 min for the human, ~3-6k tokens for the AI)

1. `python offers.py due` - handle follow-ups first (they convert better than new applications).
2. Ask the human for today's new job links/JDs, or read `jobs/inbox.csv`. Run `python offers.py import jobs/inbox.csv`.
3. `python offers.py triage` - work top-down. Respect `brain/instincts.yaml` (min_fit, daily cap).
4. For each chosen job: `python offers.py packet <ID> --task tailor` and answer the packet. Do not read the full resume or JD again - the packet already has what is needed.
5. Use the `offers-browser-assist` skill to fill the form. The human clicks Submit.
6. `python offers.py status <ID> Applied --note "<what was sent>"`.
7. End: `python offers.py export` and show `python offers.py stats`.
