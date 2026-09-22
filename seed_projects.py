"""Seed / reconcile the known Adani projects into data.json.

data.json is intentionally gitignored (see .gitignore) — it's live runtime
state and can hold secrets (SMTP password, AI API key) plus growing check
history, so it must never be committed. That means a fresh `git clone` on
a new machine or VM starts with an *empty* project list.

This script is the fix: it's plain code (safe to commit), and running it
populates data.json with the current known project/URL/developer roster.
It's idempotent — safe to run once after cloning, or again any time later:

  - Missing projects are created.
  - Existing projects are left alone (name/description/project_url are
    only filled in if currently blank — never overwritten).
  - Developers are matched by name; a blank email is filled in, a
    developer not yet on the project is added, nothing is ever removed.
  - URLs are matched by exact URL string; a missing one is added (and
    checked immediately), an existing one is left untouched (so its check
    history/last_result/last_analysis survive re-runs).

Usage (after `git pull` / `git clone`, from the project root):

    .venv\\Scripts\\python.exe seed_projects.py       (Windows)
    .venv/bin/python seed_projects.py                 (Linux/macOS)

To add or update projects going forward: edit SEED_PROJECTS below, commit
the change, and have everyone re-run this script — it will only apply
what's new/missing.
"""

from __future__ import annotations

import checker
import storage

SEED_PROJECTS: list[dict] = [
    {
        "name": "F & A Report Optimization",
        "project_url": "https://agel-agents-uat.adani.com/fna/dashboard/financial-summary",
        "description": "Finance & Account Report Optimization",
        "developers": [
            {"name": "Vishal", "email": ""},
            {"name": "Nauman", "email": "naumanpathan@adani.com"},
            {"name": "Sahil", "email": "sahil.singh1@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com/fna/dashboard/financial-summary", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "Resource Assessment Console",
        "project_url": "",
        "description": "Resource Assessment Console",
        "developers": [
            {"name": "Imran", "email": ""},
            {"name": "Rahul", "email": ""},
            {"name": "Bhargav", "email": ""},
        ],
        "urls": [],
    },
    {
        "name": "Akasha Intelligence Cross Platform",
        "project_url": "https://digitalized-dpr-uat.adani.com/akasha",
        "description": "Akasha Intelligence Cross Platform portal",
        "developers": [
            {"name": "Praveen", "email": "praveen.gunja@adani.com"},
            {"name": "Nikitha", "email": ""},
        ],
        "urls": [
            {"name": "Portal", "url": "https://digitalized-dpr-uat.adani.com/akasha", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "PMAG Cost Process",
        "project_url": "https://agel-agents-uat.adani.com/pmag/details",
        "description": "PMAG Cost Process portal",
        "developers": [
            {"name": "Harshith", "email": ""},
            {"name": "Sahil", "email": ""},
            {"name": "Satwik", "email": "satwik.narwa@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com/pmag/details", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "NDC",
        "project_url": "https://agel-agents-uat.adani.com/ndc/ndc-reporting/overview",
        "description": "HR NDC Tracking Dashboard",
        "developers": [
            {"name": "Laxmi", "email": "laxminarayana@adani.com"},
            {"name": "Sahil", "email": ""},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com/ndc/ndc-reporting/overview", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "ENOC UI/UX",
        "project_url": "https://agel-agents-uat.adani.com/enoc",
        "description": "ENOC UI/UX portal",
        "developers": [
            {"name": "Satwik", "email": "satwik.narwa@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com/enoc", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "Landed Tariff",
        "project_url": "https://agel-agents-uat.adani.com/landed-tariff/dashboard",
        "description": "Landed Tariff portal",
        "developers": [
            {"name": "Sai Manohar", "email": "SaiManohar@cognitbotz.com"},
            {"name": "Bhargav", "email": ""},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com/landed-tariff/dashboard", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "Debt Pulse",
        "project_url": "https://aegis.adani.com/debt-markets/",
        "description": "Debt Markets - Adani Treasury",
        "developers": [
            {"name": "Abhishek", "email": "Abhishek.MahadevMane@adani.com"},
            {"name": "Guruprasad", "email": ""},
        ],
        "urls": [
            {"name": "Portal", "url": "https://aegis.adani.com/debt-markets/", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "DPR",
        "project_url": "https://digitalized-dpr.adani.com/",
        "description": "Digitalized DPR - Enterprise Project Management",
        "developers": [
            {"name": "Praveen", "email": "praveen.gunja@adani.com"},
            {"name": "Nikitha", "email": "nikitham@cognitbotz.com"},
        ],
        "urls": [
            {"name": "https://digitalized-dpr.adani.com/", "url": "https://digitalized-dpr.adani.com/", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "IR",
        "project_url": "https://aegis.adani.com/equity-dashboard/",
        "description": "Equity Pulse - IR Console",
        "developers": [
            {"name": "Abhishek", "email": "Abhishek.MahadevMane@adani.com"},
            {"name": "Pallavi", "email": "pallavi.namburi@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://aegis.adani.com/equity-dashboard/", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "AEGIS",
        "project_url": "https://aegis.adani.com/",
        "description": "Project AEGIS",
        "developers": [
            {"name": "Abhishek", "email": "Abhishek.MahadevMane@adani.com"},
            {"name": "Sreeja", "email": ""},
            {"name": "Sreecharan", "email": ""},
            {"name": "Satwik", "email": "satwik.narwa@adani.com"},
            {"name": "Sohel", "email": ""},
        ],
        "urls": [
            {"name": "Portal", "url": "https://aegis.adani.com/", "expected_status": 200, "timeout_seconds": 10},
        ],
    },
    {
        "name": "Carbon Credit",
        "project_url": "https://agel-agents.adani.com/carbon-credit-tracker/",
        "description": "Carbon Credit portal",
        "developers": [
            {"name": "Rahul", "email": "rahul.chenna@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents.adani.com/carbon-credit-tracker/", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "Plant Maintenance",
        "project_url": "https://agel-agents-uat.adani.com",
        "description": "Plant Maintenance portal",
        "developers": [
            {"name": "Farhan", "email": "farhan.vhora@adani.com"},
            {"name": "Nauman", "email": "naumanpathan@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "https://agel-agents-uat.adani.com", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "DSM NIS Booking - Phase 2",
        "project_url": "",
        "description": "SAP NIS 2.0 (internal SAP module - not HTTP-monitorable).",
        "developers": [
            {"name": "Rohit", "email": ""},
        ],
        "urls": [],
    },
    {
        "name": "Cobot Dashboard",
        "project_url": "http://aegis.adani.com/cobot/home",
        "description": "Cobot Dashboard portal",
        "developers": [
            {"name": "Praveen", "email": "praveen.gunja@adani.com"},
        ],
        "urls": [
            {"name": "Portal", "url": "http://aegis.adani.com/cobot/home", "expected_status": 200, "timeout_seconds": 15},
        ],
    },
    {
        "name": "Execution Tracker",
        "project_url": "",
        "description": "Execution Tracker",
        "developers": [
            {"name": "Praveen", "email": ""},
            {"name": "Satwik", "email": ""},
            {"name": "Sohel", "email": ""},
        ],
        "urls": [],
    },
]


def _merge_developers(existing: list[dict], seed: list[dict]) -> tuple[list[dict], bool]:
    changed = False
    by_name = {(d.get("name") or "").strip().lower(): d for d in existing}
    for sdev in seed:
        key = (sdev.get("name") or "").strip().lower()
        email = (sdev.get("email") or "").strip()
        existing_dev = by_name.get(key)
        if existing_dev is None:
            existing.append({"name": sdev.get("name") or "", "email": email})
            by_name[key] = existing[-1]
            changed = True
        elif email and not (existing_dev.get("email") or "").strip():
            existing_dev["email"] = email
            changed = True
    return existing, changed


def main() -> None:
    projects = storage.list_projects()
    by_name = {p["name"]: p for p in projects}

    created = 0
    updated_meta = 0
    devs_touched = 0
    urls_added = 0

    for seed in SEED_PROJECTS:
        name = seed["name"]
        project = by_name.get(name)

        if project is None:
            project = storage.create_project(
                name,
                description=seed.get("description", ""),
                project_url=seed.get("project_url", ""),
                developers=seed.get("developers", []),
            )
            created += 1
            print(f"[create] {name}")
            for u in seed.get("urls", []):
                entry = storage.add_url(
                    project["id"], u["name"], u["url"],
                    u.get("expected_status", 200), u.get("timeout_seconds", 10),
                )
                urls_added += 1
                if entry:
                    result = checker.run_single(project["id"], entry["id"])
                    print(f"  [check] {u['url']}: {result.get('label')}")
            continue

        # Existing project: fill gaps only, never clobber.
        meta_changed = False
        new_project_url = project.get("project_url") or ""
        new_description = project.get("description") or ""
        if not new_project_url.strip() and seed.get("project_url"):
            new_project_url = seed["project_url"]
            meta_changed = True
        if not new_description.strip() and seed.get("description"):
            new_description = seed["description"]
            meta_changed = True

        devs, devs_changed = _merge_developers(project.get("developers", []), seed.get("developers", []))
        if devs_changed:
            devs_touched += 1

        if meta_changed or devs_changed:
            storage.update_project(
                project["id"],
                description=new_description,
                project_url=new_project_url,
                developers=devs,
            )
            updated_meta += 1

        existing_urls = {u["url"] for u in project.get("urls", [])}
        for u in seed.get("urls", []):
            if u["url"] in existing_urls:
                continue
            entry = storage.add_url(
                project["id"], u["name"], u["url"],
                u.get("expected_status", 200), u.get("timeout_seconds", 10),
            )
            urls_added += 1
            print(f"[add-url] {name}: {u['url']}")
            if entry:
                result = checker.run_single(project["id"], entry["id"])
                print(f"  [check] {result.get('label')}")

    print()
    print(f"Projects created      : {created}")
    print(f"Projects updated      : {updated_meta}")
    print(f"Projects w/ dev merge : {devs_touched}")
    print(f"URLs added            : {urls_added}")


if __name__ == "__main__":
    main()
