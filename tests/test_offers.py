"""End-to-end tests: every CLI command runs against a throwaway copy of the repo layout."""
import datetime as dt
import shutil
from pathlib import Path

import openpyxl
import pytest

import offers as o

REPO = Path(o.__file__).resolve().parent


@pytest.fixture()
def home(tmp_path, monkeypatch):
    for d in ("profile", "prompts", "brain", "dashboard", "skills", "jobs"):
        shutil.copytree(REPO / d, tmp_path / d, ignore=shutil.ignore_patterns("profile.yaml", "answers.yaml", "learnings.md", "data.js", "jds"))
    paths = dict(ROOT=tmp_path, TRACKER=tmp_path / "tracker" / "OffersOSS_Tracker.xlsx", PROFILE=tmp_path / "profile" / "profile.yaml",
                 PROFILE_EXAMPLE=tmp_path / "profile" / "profile.example.yaml", PACKETS=tmp_path / "packets",
                 DATA_JS=tmp_path / "dashboard" / "data.js", BRAIN=tmp_path / "brain", ANSWERS=tmp_path / "brain" / "answers.yaml",
                 INSTINCTS=tmp_path / "brain" / "instincts.yaml", LEARNINGS=tmp_path / "brain" / "learnings.md",
                 METER=tmp_path / "brain" / "meter.json")
    for k, v in paths.items():
        monkeypatch.setattr(o, k, v)
    o.main(["init"])
    return tmp_path


def jobs(home):
    return o.rows(openpyxl.load_workbook(o.TRACKER)["Applications"])


def test_init_creates_everything(home):
    assert o.TRACKER.exists() and o.PROFILE.exists() and o.ANSWERS.exists()
    wb = openpyxl.load_workbook(o.TRACKER)
    assert wb.sheetnames == ["Dashboard", "Applications", "Lists", "Guide"]
    assert [c.value for c in wb["Applications"][1]] == o.COLUMNS


def test_import_scores_and_dedupes(home, capsys):
    o.main(["import", str(home / "jobs" / "inbox.example.csv")])
    o.main(["import", str(home / "jobs" / "inbox.example.csv")])
    j = jobs(home)
    assert len(j) == 3
    acme = next(x for x in j if x["Company"] == "Acme Fintech")
    assert acme["Fit %"] >= 80 and acme["Resume"] == "java"
    assert "skip duplicate" in capsys.readouterr().out


def test_fit_scoring_rules():
    p = {"skills": ["java", "spring boot"], "must_have_any": ["java"], "deal_breakers": ["night shift only"],
         "years_experience": 3, "resume_variants": [{"name": "x", "keywords": ["java"]}]}
    assert o.analyse("Java and Spring Boot, 2-4 years", p)["fit"] == 100
    assert o.analyse("Python and Django only", p)["fit"] <= 40           # must-have missing
    assert o.analyse("Java, night shift only", p)["fit"] <= 20           # deal breaker
    assert o.analyse("Java with 8-10 years", p)["experience_flag"]       # over-asks experience
    assert o.analyse("golang role", p)["matched"] == []                 # no false 'go' match on 'golang'


def test_status_sets_dates_and_followup(home):
    o.main(["add", "--company", "X", "--role", "Java Dev", "--jd", "Java Spring Boot Kafka", "--source", "Naukri"])
    o.main(["status", "OF-0001", "applied", "--note", "sent"])
    j = jobs(home)[0]
    assert j["Status"] == "Applied" and j["Applied On"] == dt.date.today()
    assert j["Follow-up"] == dt.date.today() + dt.timedelta(days=7)
    o.main(["status", "OF-0001", "Rejected"])
    assert jobs(home)[0]["Follow-up"] is None


def test_packet_is_token_lean(home, capsys):
    o.main(["import", str(home / "jobs" / "inbox.example.csv")])
    capsys.readouterr()
    o.main(["packet", "OF-0001", "--task", "tailor"])
    out = capsys.readouterr().out
    assert "Acme Fintech" in out and "{{" not in out and "saved" in out
    assert (home / "packets" / "OF-0001-tailor.md").exists()


def test_second_brain_answer_and_learn(home, capsys):
    o.main(["answer", "when can you join?"])
    assert "A01" in capsys.readouterr().out
    o.main(["learn", "--q", "Do you have a passport?", "--a", "Yes, valid till 2032."])
    o.main(["answer", "do you have a passport"])
    assert "2032" in capsys.readouterr().out
    o.main(["learn", "--feedback", "Asked about Kafka", "--kind", "interview"])
    assert "Asked about Kafka" in o.LEARNINGS.read_text()


def test_export_due_stats_doctor(home, capsys):
    o.main(["import", str(home / "jobs" / "inbox.example.csv")])
    o.main(["status", "OF-0002", "Interview"])
    for cmd in (["export"], ["due"], ["stats"], ["triage"], ["list"], ["doctor"]):
        o.main(cmd)
    assert "window.OFFEROS_DATA" in o.DATA_JS.read_text()
    assert "Offers OSS pipeline" in capsys.readouterr().out


def feed(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(it, ""))


def test_setup_wizard_prefills_brain(home, monkeypatch):
    feed(monkeypatch, "Test User", "Java Dev | Spring", "4", "java, kafka, sql", "30 days", "Pune")
    o.main(["setup"])
    p = o.load_profile()
    assert p["display_name"] == "Test User" and p["skills"] == ["java", "kafka", "sql"]
    bank = {e["id"]: e["a"] for e in o.load_answers()}
    assert "30 days" in bank["A01"] and bank["A13"] == "Pune"


def test_brain_fill_and_coverage(home, monkeypatch):
    before = o.brain_coverage()["answered"]
    feed(monkeypatch, "I can join on 1 Dec.", "", "q")
    o.main(["brain"])
    assert o.brain_coverage()["answered"] == before + 1


def test_go_cockpit_and_meter(home, monkeypatch, capsys):
    o.main(["import", str(home / "jobs" / "inbox.example.csv")])
    feed(monkeypatch, "a", "OF-0001", "java resume")
    o.main(["go", "--once"])
    out = capsys.readouterr().out
    assert "Offers OSS cockpit" in out and "OF-0001 -> Applied" in out
    m = o.meter()
    assert m["jds_scored"] == 3 and m["tokens_saved"] > 0
    o.main(["export"])
    assert '"applied_today": 1' in o.DATA_JS.read_text()
