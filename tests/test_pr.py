"""Reviews authorize a specific revision and respect later review decisions."""

import json
import sqlite3
import subprocess

import pytest
from conftest import load_workbench


@pytest.fixture
def pull_request(tmp_path, monkeypatch):
    wb = load_workbench()
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Engineer")
    git("config", "user.email", "engineer@example.com")
    git("commit", "-q", "--allow-empty", "-m", "Initial")
    git("checkout", "-q", "-b", "feature")
    git("commit", "-q", "--allow-empty", "-m", "Feature")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"repos": {"service": str(repo)}}))
    monkeypatch.setattr(wb, "DB_PATH", tmp_path / "workbench.db")
    monkeypatch.setattr(wb, "CONFIG_PATH", config)
    monkeypatch.setenv("SUDO_USER", "priya")
    assert wb.main(["pr", "open", "--branch", "feature", "--title", "Feature"]) == 0
    merged = []
    monkeypatch.setattr(wb, "merge_branch", lambda *args: merged.append(args))
    return wb, git, merged


def test_new_commit_needs_new_approval(pull_request, monkeypatch, capsys):
    wb, git, merged = pull_request
    monkeypatch.setenv("SUDO_USER", "sam")
    assert wb.main(["pr", "review", "1", "--verdict", "approve"]) == 0
    old = git("rev-parse", "HEAD")
    git("commit", "-q", "--allow-empty", "-m", "Extra change")
    assert wb.main(["pr", "merge", "1"]) == 1
    assert "current commit" in capsys.readouterr().err
    assert merged == []
    assert wb.main(["pr", "review", "1", "--verdict", "approve"]) == 0
    assert wb.main(["pr", "merge", "1"]) == 0
    assert merged[0][-1] == git("rev-parse", "HEAD") != old
    assert wb.main(["pr", "review", "1", "--verdict", "approve"]) == 1
    assert "is merged" in capsys.readouterr().err


def test_latest_decisive_review_wins(pull_request, monkeypatch, capsys):
    wb, _, merged = pull_request
    monkeypatch.setenv("SUDO_USER", "sam")
    for verdict in ("approve", "request-changes", "comment"):
        assert wb.main(["pr", "review", "1", "--verdict", verdict]) == 0
    monkeypatch.setenv("SUDO_USER", "lena")
    assert wb.main(["pr", "review", "1", "--verdict", "approve"]) == 0
    assert wb.main(["pr", "merge", "1"]) == 1
    assert "outstanding requests" in capsys.readouterr().err
    assert merged == []
    monkeypatch.setenv("SUDO_USER", "sam")
    assert wb.main(["pr", "review", "1", "--verdict", "approve"]) == 0
    assert wb.main(["pr", "review", "1", "--verdict", "comment"]) == 0
    assert wb.main(["pr", "merge", "1"]) == 0


def test_legacy_reviews_migrate_without_authorizing_unknown_commits(tmp_path, monkeypatch):
    wb = load_workbench()
    path = tmp_path / "workbench.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE pr_reviews (id INTEGER PRIMARY KEY, number INTEGER, "
                     "reviewer TEXT, verdict TEXT, body TEXT, created TEXT)")
        conn.execute("INSERT INTO pr_reviews VALUES (1, 1, 'sam', 'approve', '', '')")
    monkeypatch.setattr(wb, "DB_PATH", path)
    for _ in range(2):
        with wb.db() as conn:
            row = conn.execute("SELECT verdict, head FROM pr_reviews").fetchone()
            assert tuple(row) == ("approve", None)


def test_merge_uses_reviewed_commit_when_branch_has_moved(pull_request, tmp_path):
    _, git, _ = pull_request
    approved = git("rev-parse", "HEAD")
    git("commit", "-q", "--allow-empty", "-m", "Unreviewed change")
    unreviewed = git("rev-parse", "HEAD")
    git("checkout", "-q", "main")
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(tmp_path / "repo"), str(origin)], check=True)
    wb = load_workbench()
    wb.merge_branch(str(origin), "feature", "priya", "Merge reviewed change", approved)
    result = subprocess.run(["git", "-C", str(origin), "rev-list", "main"],
                            check=True, capture_output=True, text=True).stdout.splitlines()
    assert approved in result and unreviewed not in result


def test_same_branch_name_can_have_a_pr_in_each_repository(pull_request, tmp_path, capsys):
    wb, _, _ = pull_request
    other = tmp_path / "other.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(tmp_path / "repo"), str(other)], check=True)
    config = json.loads(wb.CONFIG_PATH.read_text())
    config["repos"]["other"] = str(other)
    wb.CONFIG_PATH.write_text(json.dumps(config))
    command = ["pr", "open", "--repo", "other", "--branch", "feature", "--title", "Other feature"]
    assert wb.main(command) == 0
    assert "#2" in capsys.readouterr().out
    assert wb.main(command) == 1
    assert "already exists" in capsys.readouterr().err
    with wb.db() as conn:
        rows = conn.execute("SELECT repo, branch FROM prs ORDER BY number").fetchall()
        assert [tuple(r) for r in rows] == [("service", "feature"), ("other", "feature")]
