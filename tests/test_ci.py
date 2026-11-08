"""Database compatibility for the CI requester/executor split."""

import sqlite3

from conftest import load_workbench


def test_legacy_ci_records_keep_historical_executor(tmp_path, monkeypatch):
    wb = load_workbench()
    path = tmp_path / "workbench.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE ci_runs (id INTEGER PRIMARY KEY, repo TEXT, ref TEXT, "
                     "actor TEXT, status TEXT, output TEXT, created TEXT)")
        conn.execute("INSERT INTO ci_runs VALUES (1, 'billing-api', 'main', 'maya', 'passed', '', '')")
    monkeypatch.setattr(wb, "DB_PATH", path)
    for _ in range(2):
        conn = wb.db()
        assert dict(conn.execute("SELECT actor,ran_as FROM ci_runs").fetchone()) == {
            "actor": "maya", "ran_as": "workbench",
        }
        conn.close()
    args = wb.parser().parse_args(["ci", "view", "CI-1"])
    assert "by maya, ran as workbench" in wb.ci(args)
