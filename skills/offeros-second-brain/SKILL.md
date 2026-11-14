---
name: offeros-second-brain
description: Answer recruiter or form questions from the user's saved answers, and capture new answers, interview feedback and lessons. Use for "what's my notice period answer", "save this answer", "log this interview", "what have I learned".
---
# Second brain
- Lookup first: `python offeros.py answer "<question>"`. Reuse saved answers; only adapt tone/length.
- New question: ask the human once, then `python offeros.py learn --q "<question>" --a "<answer>"`.
- After any interview or rejection: `python offeros.py learn --kind interview --job <ID> --feedback "<questions asked / outcome>"`.
- Weekly: read `brain/learnings.md`, propose at most 3 new rules for `brain/instincts.yaml`, and let the human approve them.
