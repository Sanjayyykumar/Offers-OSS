---
name: offeros-interview-prep
description: Build an interview prep pack for a job in the tracker, grounded in the user's facts and past interview learnings. Use when status moves to Screening or Interview, or the user says "prep me for <company>".
---
# Interview prep
1. `python offeros.py packet <ID> --task interview-prep`.
2. Add any matching lines from `brain/learnings.md` and `brain/companies/<company>.md`.
3. Run a 10-minute mock: ask one question at a time, score answers 1-5, give one fix each.
4. After the real interview, log it with the second-brain skill.
