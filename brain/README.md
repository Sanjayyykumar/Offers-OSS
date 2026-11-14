# 🧠 Second Brain

Everything you learn during a job hunt is written down **once** and reused **forever** - by you, by the CLI, and by any AI.
That is the single biggest token saver in Offers OSS: the AI never re-derives your notice period, salary stance or "why are you leaving" answer.

| File | What it holds | Who writes it |
|---|---|---|
| `answers.yaml` | Your approved answers to the questions recruiters and forms ask again and again | You (via `offers learn --q --a`) |
| `instincts.yaml` | Decision rules the agent must follow (min fit, daily cap, when to follow up, when to walk away) | You, tuned over time |
| `learnings.md` | Dated feedback: interview questions you got, rejection reasons, what worked | `offers learn --feedback` |
| `companies/*.md` | One note per company: people, process, salary band heard, red flags | You or the AI (with your OK) |

**Rules**
1. Answers are *yours*. The AI may shorten or adapt tone, never change facts.
2. When the AI meets a new question, it asks you once, then saves your answer here.
3. Review `learnings.md` every Sunday; promote repeated lessons into `instincts.yaml`.
