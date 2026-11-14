---
name: offeros-triage
description: Decide which jobs are worth applying to, using Offers OSS's local fit score and the user's instincts. Use when the user pastes several job links or asks "which of these should I apply to".
---
# Triage
- Scores come from `offeros.py` (local keyword match, zero tokens). Never re-score by reading every JD yourself.
- Apply in this order: referral/recruiter > fit >= 75 > fit 55-74 with a clear reason > skip.
- For each skip, say why in <= 8 words (e.g. "asks 8 yrs, has 3"; "no Java").
- Flag duplicates (same company, similar role) and recommend at most 2 per company.
