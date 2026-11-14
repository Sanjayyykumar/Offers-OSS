---
name: offeros-tailor
description: Tailor a resume top-third, cover note or recruiter message for one job from an Offers OSS packet. Use when the user asks to tailor, customise or write a cover letter for a job already in the tracker.
---
# Tailor
1. Run `python offeros.py packet <ID> --task <tailor|cover-note|recruiter-message>` and use ONLY its content.
2. Facts come from the packet's Candidate block. Anything else -> `[ASK: ...]`.
3. Keep the human's voice: short sentences, numbers over adjectives.
4. After the human approves, note what was sent: `python offeros.py status <ID> Applied --note "tailored: java variant + cover note"`.
