---
name: offeros-browser-assist
description: Help the user fill a job application form in their own browser session (Claude in Chrome, Gemini in Chrome, ChatGPT agent, Copilot) without breaking site rules. Use when the user says "fill this application", "help me apply on this page".
---
# Browser assist - human in the loop, always

**Allowed:** reading the page the human opened, filling fields with the human's saved facts and answers, uploading the resume variant the tracker picked, pausing for review.
**Never:** clicking Submit/Apply/Send, solving CAPTCHAs, logging in with stored passwords, bulk-navigating search results, scraping lists of jobs or people, messaging people automatically.

Steps
1. Confirm the job ID in the tracker (add it if missing).
2. Fill fields from `profile/profile.yaml` and `brain/answers.yaml` (`python offeros.py answer "<field label>"`).
3. Unknown question -> stop and ask the human; then save with `offeros learn --q --a`.
4. Hand over: "Everything is filled. Please review and click Submit yourself."
5. After the human confirms, run `python offeros.py status <ID> Applied`.

On LinkedIn, Indeed and similar sites, third-party automation of activity is prohibited by their terms. Prefer the company career page; on those sites, limit yourself to drafting text the human pastes.
