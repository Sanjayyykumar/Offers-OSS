# Compliance by design

> Offers OSS is built so that using it does **not** break job-site rules or privacy law. This page explains how. It is not legal advice; check the current terms of every site you use.

## The one rule that matters: the human submits
Most job platforms forbid bots acting on their sites. LinkedIn's help centre says it does not permit third-party software, including crawlers, bots, browser plug-ins or extensions, that scrape, modify the appearance of, or automate activity on its website ([LinkedIn - Prohibited software and extensions](https://www.linkedin.com/help/linkedin/answer/a1341387)), and members using such tools risk account restriction. Indeed's terms (updated 29 Sep 2026) prohibit automation, scripting or bots for the Indeed Apply process outside its official vendors ([quoted here](https://blog.fastapply.co/can-you-get-banned-for-auto-applying-on-linkedin-2026)). Naukri's terms also restrict automated access.

So Offers OSS **has no auto-apply, no scraper, no login automation and no auto-messaging** - by design, not by omission.

| Offers OSS does | Offers OSS never does |
|---|---|
| Scores JDs **you** paste, locally | Crawl or scrape job boards or profiles |
| Drafts text you review and paste | Click Submit / Apply / Send |
| Lets a browser assistant fill fields on a page **you** opened, then stop | Log in for you, store passwords, solve CAPTCHAs |
| Tracks, reminds, visualises | Bulk-apply or mass-message |
| Keeps facts you wrote | Invent experience, titles, numbers, degrees |

## Honesty
Every prompt carries the rule "use only the candidate's facts; otherwise write `[ASK: ...]`". Fabricated claims fail background checks and can lead to offer withdrawal. The `brain/answers.yaml` tips repeat this for salary and notice period.

## Privacy (India DPDP Act 2023, GDPR and similar)
- **Local-first.** Your tracker, profile, answers and learnings stay on your machine. The dashboard runs from a file; the only network call is optional - loading the open-source Excel reader when you drag in an `.xlsx`.
- **Git-ignored by default:** `profile/profile.yaml`, resumes, `tracker/*.xlsx`, `brain/answers.yaml`, `brain/learnings.md`, packets, JDs.
- **Data minimisation for AI.** Packets send a short fact list and a JD excerpt - not your full resume, phone number or address.
- **Other people's data.** Store only what a recruiter gave you for the hiring process (name, role, work email). Delete it when the process ends.
- **Screenshots.** Use the dashboard's **Privacy blur** button (or `?blur=1`) before sharing.

## AI provider terms
Use each AI under its own terms. If your employer bans personal use of AI tools on work devices, run Offers OSS on a personal device. To avoid any provider, use a local model (Ollama) - see [RECOMMENDED_AI.md](RECOMMENDED_AI.md).
