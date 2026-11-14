# Recommended AI (Offers OSS works with all of them)

Offers OSS does the bookkeeping locally, so the AI only writes. Any capable model works; pick by the job.

| Task | Best fit | Why | Free / low-cost option |
|---|---|---|---|
| Tailoring, cover notes, recruiter messages | **Claude** (Sonnet/Opus) | Follows "facts only" rules closely; natural, non-salesy tone | Claude free tier |
| Agentic daily run in the repo | **Claude Code** - reads `CLAUDE.md` + `skills/` | Runs the CLI, follows skills, asks before acting | Gemini CLI (reads `GEMINI.md`) |
| Filling forms on a page you opened | **Claude in Chrome**, Gemini in Chrome, ChatGPT agent | Sees the page; `offeros-browser-assist` keeps you on Submit | - |
| Long JDs, many at once, research on a company | **Gemini** (long context) | Cheap bulk reading | Gemini free tier |
| Interview mock (voice) | **ChatGPT** voice / Gemini Live / Claude voice | Real-time spoken practice | Free tiers |
| Maximum privacy / offline | **Ollama** + Llama / Qwen / Mistral | Nothing leaves your machine | Free |
| Inside an IDE | GitHub Copilot, Cursor (read `AGENTS.md`) | Same rules, in your editor | Copilot free tier |

## Token budget (typical day, 10 applications)

| Step | Naive approach | Offers OSS |
|---|---|---|
| Score 30 JDs | ~30 x 2.5k = 75k tokens | **0** (local) |
| Tailor 10 jobs | 10 x (resume 2k + JD 1.5k + chat) ≈ 40k | 10 x ~450 ≈ **4.5k** |
| Answer 20 screening questions | ~6k | **0** for saved answers |
| Follow-ups, stats, dashboard | ~5k | **0** |
| **Total** | **~125k** | **~5-8k** |

Numbers are estimates (≈ 4 characters per token); `offeros packet` prints the estimate for each packet.

*Plans and prices change; check each provider's current offer.*
