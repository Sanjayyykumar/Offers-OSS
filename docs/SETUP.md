# Setup - pick your path

| Path | For | Time | Needs |
|---|---|---|---|
| **A. CLI + any AI** (recommended) | Anyone comfortable with a terminal | 5 min | Python 3.10+ |
| **B. No-code** | Non-developers, any field | 3 min | Excel / Google Sheets + any AI chat |
| **C. Agentic** | Power users | 10 min | Claude Code, Gemini CLI, Codex CLI, Cursor or Copilot |

---

## A. CLI + any AI

```bash
git clone https://github.com/Sanjayyykumar/Offers-OSS && cd Offers-OSS
pip install -r requirements.txt
python offers.py init          # creates tracker, profile, second brain
```

1. **Fill `profile/profile.yaml`** - skills you can defend, 4-6 one-line facts with numbers, and your resume variants. Put the resume PDFs in `profile/resumes/` (git-ignored).
2. **Fill `brain/answers.yaml`** - replace every `<...>` with your truth (notice period, CTC stance, gap, relocation). This one-time step saves the most tokens later.
3. **Collect jobs** - paste links + the JD text into `jobs/inbox.csv` (copy `jobs/inbox.example.csv`). You open and read the job pages yourself; Offers OSS never scrapes.
4. **Daily loop**

```bash
python offers.py import jobs/inbox.csv   # score + dedupe, 0 tokens
python offers.py triage                  # best fit first
python offers.py packet OF-0007          # paste into Claude / ChatGPT / Gemini
#   ...apply on the site yourself (or with a browser assistant that stops before Submit)...
python offers.py status OF-0007 Applied --note "java resume + cover note"
python offers.py due                     # follow-ups
python offers.py export                  # open dashboard/index.html
```

Try it first with demo data: `python scripts/seed_demo.py && python offers.py export`.

## B. No-code (Excel + any AI chat)

1. Download `tracker/OffersOSS_Tracker.template.xlsx`. Open it in Excel or upload to Google Sheets. Status/Source drop-downs, colours and the Dashboard sheet work without any code.
2. In your AI (ChatGPT Project, Claude Project, Gemini Gem, Copilot notebook), create a project and paste **`AGENTS.md`** as its instructions. Upload `profile.example.yaml` (filled in), `brain/answers.example.yaml` (filled in) and `brain/instincts.yaml` as files.
3. For each job, paste the JD and ask for the task you need, e.g. "tailor (prompts/tailor.md)". The AI follows the same rules as the CLI.
4. Update the Status column yourself. For the visual dashboard, open `dashboard/index.html` and drag your `.xlsx` onto it.

## C. Agentic (Claude Code, Gemini CLI, Codex, Cursor, Copilot)

Open the repo in your agent. It auto-reads `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` / `.github/copilot-instructions.md`, which all point to the same rules. `CLAUDE.md` points Claude Code at the playbooks in `skills/`.

Say: **"start my daily run"** - the `offers-daily-run` skill does the rest and stops for your approval before anything is sent.

### Browser assistants (Claude in Chrome, Gemini in Chrome, ChatGPT agent)
Use the `offers-browser-assist` skill. The assistant may read the page you opened and fill fields from your profile and saved answers. **You click Submit.** Prefer company career pages; on LinkedIn/Indeed, draft text only (see [COMPLIANCE.md](COMPLIANCE.md)).

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Missing dependencies` | `pip install -r requirements.txt` |
| Dashboard empty | Run `python offers.py export`, or drag the `.xlsx` onto the page |
| Fit % looks wrong | Add aliases to skills in `profile.yaml`, e.g. `spring boot\|springboot` |
| Dashboard sheet shows 0s in a previewer | Open in Excel/Sheets - formulas compute on open |
| `answer` says "not in brain" | Save it once: `python offers.py learn --q "..." --a "..."` |
