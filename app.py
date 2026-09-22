"""Ping Tester — Flask dashboard with background URL checks + NVIDIA agents."""

from __future__ import annotations

import atexit
from urllib.parse import urlparse

from apscheduler.schedulers.background import BackgroundScheduler
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import auth
import checker
import storage
from agents.helper import chat as helper_chat
from agents.helper import clear_chat_history, get_chat_history
from agents.llm import agents_configured

app = Flask(__name__, static_url_path="/dashboard/static")
app.secret_key = "ping-tester-change-me-in-production"
app.config["TEMPLATES_AUTO_RELOAD"] = True

DASHBOARD_PREFIX = "/dashboard"

scheduler = BackgroundScheduler(daemon=True)


def _valid_http_url(value: str) -> bool:
    if not value or not str(value).strip():
        return True  # optional project URL
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _valid_monitor_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _schedule_jobs() -> None:
    interval = int(storage.get_settings().get("check_interval_seconds") or 60)
    if scheduler.get_job("url_checks"):
        scheduler.reschedule_job("url_checks", trigger="interval", seconds=interval)
    else:
        scheduler.add_job(
            checker.run_all,
            "interval",
            seconds=interval,
            id="url_checks",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


@app.context_processor
def inject_globals():
    from agents.llm import get_model_name

    return {
        "app_name": "Ping Tester",
        "check_interval": storage.get_settings().get("check_interval_seconds", 60),
        "agents_ready": agents_configured(),
        "nvidia_model": get_model_name("chat") if agents_configured() else None,
        "analysis_model": get_model_name("analysis") if agents_configured() else None,
    }


@app.route("/dashboard/setup", methods=["GET", "POST"])
def setup():
    return redirect(url_for("login"))


@app.route("/dashboard/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if auth.verify_credentials(username, password):
            session["authenticated"] = True
            session["admin_user"] = auth.ADMIN_USERNAME
            nxt = request.args.get("next") or url_for("dashboard")
            return redirect(nxt)
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/dashboard/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@auth.login_required
def dashboard():
    projects = storage.list_projects()
    cards = []
    for project in projects:
        health = storage.project_health(project)
        cards.append({"project": project, "health": health})

    def _sort_key(card: dict) -> tuple:
        h = card["health"]
        name = (card["project"].get("name") or "").lower()
        if h.get("down", 0) > 0:
            return (0, name)  # problems first
        if h.get("total", 0) == 0:
            return (2, name)
        if h.get("unknown", 0) > 0:
            return (1, name)
        return (3, name)

    cards.sort(key=_sort_key)
    return render_template("dashboard.html", cards=cards)


def _add_services_to_project(project_id: str, services: list) -> tuple[int, list[str]]:
    """Add and immediately check services. Returns (added_count, errors)."""
    added = 0
    errors: list[str] = []
    for svc in services:
        url = (svc.get("url") or "").strip()
        name = (svc.get("name") or "").strip() or url
        if not url:
            errors.append(f"Missing URL for “{name or 'service'}”")
            continue
        if not _valid_monitor_url(url):
            errors.append(f"Invalid URL: {url}")
            continue
        entry = storage.add_url(
            project_id,
            name,
            url,
            int(svc.get("expected_status") or 200),
            int(svc.get("timeout_seconds") or 10),
        )
        if entry:
            checker.run_single(project_id, entry["id"])
            added += 1
    return added, errors


@app.route("/dashboard/projects", methods=["POST"])
@auth.login_required
def create_project():
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    project_url = (request.form.get("project_url") or "").strip()
    developers = storage.developers_from_form(request.form)
    services = storage.services_from_form(request.form)
    if not name:
        flash("Project name is required.", "error")
        return redirect(url_for("dashboard"))
    if project_url and not _valid_monitor_url(project_url):
        flash("Project URL must start with http:// or https://", "error")
        return redirect(url_for("dashboard"))
    project = storage.create_project(name, description, project_url, developers)
    added, errors = _add_services_to_project(project["id"], services)
    msg = f"Project “{project['name']}” created."
    if added:
        msg += f" {added} microservice(s) added and checked."
    flash(msg, "success")
    for err in errors:
        flash(err, "error")
    return redirect(url_for("project_detail", project_id=project["id"]))


@app.route("/dashboard/projects/<project_id>", methods=["GET"])
@auth.login_required
def project_detail(project_id: str):
    project = storage.get_project(project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("dashboard"))
    health = storage.project_health(project)
    return render_template("project.html", project=project, health=health)


@app.route("/dashboard/projects/<project_id>/edit", methods=["POST"])
@auth.login_required
def edit_project(project_id: str):
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    project_url = (request.form.get("project_url") or "").strip()
    developers = storage.developers_from_form(request.form)
    if not name:
        flash("Project name is required.", "error")
        return redirect(url_for("project_detail", project_id=project_id))
    if project_url and not _valid_monitor_url(project_url):
        flash("Project URL must start with http:// or https://", "error")
        return redirect(url_for("project_detail", project_id=project_id))
    updated = storage.update_project(
        project_id,
        name=name,
        description=description,
        project_url=project_url,
        developers=developers,
    )
    if not updated:
        flash("Project not found.", "error")
        return redirect(url_for("dashboard"))
    flash("Project updated.", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/projects/<project_id>/delete", methods=["POST"])
@auth.login_required
def delete_project(project_id: str):
    if storage.delete_project(project_id):
        flash("Project removed.", "success")
    else:
        flash("Project not found.", "error")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/projects/<project_id>/urls", methods=["POST"])
@auth.login_required
def add_url(project_id: str):
    """Add one or many microservice endpoints (multi-row form preferred)."""
    if not storage.get_project(project_id):
        flash("Project not found.", "error")
        return redirect(url_for("dashboard"))

    services = storage.services_from_form(request.form)
    # Backward-compatible single fields
    if not services:
        name = (request.form.get("name") or "").strip()
        url = (request.form.get("url") or "").strip()
        if name or url:
            services = [
                {
                    "name": name,
                    "url": url,
                    "expected_status": request.form.get("expected_status") or 200,
                    "timeout_seconds": request.form.get("timeout_seconds") or 10,
                }
            ]

    if not services:
        flash("Add at least one microservice name and URL.", "error")
        return redirect(url_for("project_detail", project_id=project_id))

    added, errors = _add_services_to_project(project_id, services)
    if added:
        flash(f"{added} microservice(s) added and checked.", "success")
    for err in errors:
        flash(err, "error")
    if not added and not errors:
        flash("No services were added.", "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/projects/<project_id>/urls/<url_id>/edit", methods=["POST"])
@auth.login_required
def edit_url(project_id: str, url_id: str):
    name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    expected = request.form.get("expected_status") or "200"
    timeout = request.form.get("timeout_seconds") or "10"
    enabled = request.form.get("enabled") == "on"
    if not name or not url:
        flash("URL name and address are required.", "error")
        return redirect(url_for("project_detail", project_id=project_id))
    if not _valid_monitor_url(url):
        flash("URL must start with http:// or https://", "error")
        return redirect(url_for("project_detail", project_id=project_id))
    try:
        expected_i = int(expected)
        timeout_i = int(timeout)
    except ValueError:
        flash("Expected status and timeout must be numbers.", "error")
        return redirect(url_for("project_detail", project_id=project_id))
    updated = storage.update_url(
        project_id,
        url_id,
        name=name,
        url=url,
        expected_status=expected_i,
        timeout_seconds=timeout_i,
        enabled=enabled,
    )
    if not updated:
        flash("URL not found.", "error")
    else:
        flash("URL updated.", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/projects/<project_id>/urls/<url_id>/delete", methods=["POST"])
@auth.login_required
def delete_url(project_id: str, url_id: str):
    if storage.delete_url(project_id, url_id):
        flash("URL removed.", "success")
    else:
        flash("URL not found.", "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/projects/<project_id>/check", methods=["POST"])
@auth.login_required
def check_project_now(project_id: str):
    results = checker.run_project(project_id)
    flash(f"Checked {len(results)} microservice(s).", "success")
    if request.args.get("next") == "dashboard" or request.form.get("next") == "dashboard":
        return redirect(url_for("dashboard"))
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/projects/<project_id>/urls/<url_id>/check", methods=["POST"])
@auth.login_required
def check_url_now(project_id: str, url_id: str):
    result = checker.run_single(project_id, url_id)
    if not result:
        flash("URL not found.", "error")
    elif result.get("ok"):
        flash("Check passed.", "success")
    else:
        flash(result.get("message") or "Check failed.", "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/dashboard/settings", methods=["GET", "POST"])
@auth.login_required
def settings():
    settings_data = storage.get_settings()
    email_cfg = dict(settings_data.get("email") or storage.default_email_settings())
    ai_cfg = dict(settings_data.get("ai") or storage.default_ai_settings())
    active_tab = request.args.get("tab") or "email"

    if request.method == "POST":
        action = (request.form.get("action") or "").strip()
        active_tab = (request.form.get("tab") or active_tab or "email").strip()

        if action == "save_email":
            recipients_raw = request.form.get("recipients") or ""
            recipients = [
                part.strip()
                for part in recipients_raw.replace(";", ",").split(",")
                if part.strip()
            ]
            password = request.form.get("smtp_password")
            if password is None or password == "":
                password = email_cfg.get("smtp_password") or ""
            new_email = {
                "enabled": request.form.get("enabled") == "on",
                "smtp_host": (request.form.get("smtp_host") or "").strip(),
                "smtp_port": int(request.form.get("smtp_port") or 587),
                "encryption": (request.form.get("encryption") or "starttls").strip().lower(),
                "smtp_user": (request.form.get("smtp_user") or "").strip(),
                "smtp_password": password,
                "from_address": (request.form.get("from_address") or "").strip(),
                "recipients": recipients,
            }
            storage.update_settings(email=new_email)
            flash("Email configuration saved.", "success")
            return redirect(url_for("settings", tab="email"))

        if action == "test_email":
            import mailer

            # Prefer posted form values for test (unsaved draft), else saved
            recipients_raw = request.form.get("recipients") or ""
            recipients = [
                part.strip()
                for part in recipients_raw.replace(";", ",").split(",")
                if part.strip()
            ]
            password = request.form.get("smtp_password")
            if password is None or password == "":
                password = email_cfg.get("smtp_password") or ""
            draft = {
                "settings": {
                    "email": {
                        "enabled": True,
                        "smtp_host": (request.form.get("smtp_host") or email_cfg.get("smtp_host") or "").strip(),
                        "smtp_port": int(request.form.get("smtp_port") or email_cfg.get("smtp_port") or 587),
                        "encryption": (
                            request.form.get("encryption") or email_cfg.get("encryption") or "starttls"
                        )
                        .strip()
                        .lower(),
                        "smtp_user": (request.form.get("smtp_user") or email_cfg.get("smtp_user") or "").strip(),
                        "smtp_password": password,
                        "from_address": (
                            request.form.get("from_address") or email_cfg.get("from_address") or ""
                        ).strip(),
                        "recipients": recipients or list(email_cfg.get("recipients") or []),
                    }
                }
            }
            result = mailer.send_email(
                "Ping Tester — Test email",
                "This is a test message from Ping Tester Email Config.",
                settings=draft["settings"],
            )
            if result.get("ok"):
                flash(f"Test email sent to {', '.join(result.get('to') or [])}.", "success")
            else:
                flash(f"Test email failed: {result.get('error')}", "error")
            return redirect(url_for("settings", tab="email"))

        if action == "save_ai":
            from agents.llm import reset_llm_cache

            api_key = request.form.get("api_key")
            if api_key is None or api_key.strip() == "":
                api_key = ai_cfg.get("api_key") or ""
            else:
                api_key = api_key.strip()
            new_ai = {
                "api_key": api_key,
                "base_url": (request.form.get("base_url") or storage.default_ai_settings()["base_url"]).strip(),
                "analysis_model": (request.form.get("analysis_model") or "").strip(),
                "chat_model": (request.form.get("chat_model") or "").strip(),
            }
            storage.update_settings(ai=new_ai)
            reset_llm_cache()
            flash("AI configuration saved.", "success")
            return redirect(url_for("settings", tab="ai"))

        if action == "change_password":
            current = request.form.get("current_password") or ""
            new_password = request.form.get("new_password") or ""
            confirm = request.form.get("confirm_password") or ""
            if not auth.verify_credentials(auth.ADMIN_USERNAME, current):
                flash("Current password is incorrect.", "error")
            elif len(new_password) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif new_password != confirm:
                flash("Password confirmation does not match.", "error")
            else:
                auth.set_admin_password(new_password)
                flash("Admin password updated.", "success")
            return redirect(url_for("settings", tab=active_tab))

    api_key = ai_cfg.get("api_key") or ""
    ai_cfg_view = {
        **ai_cfg,
        "api_key_set": bool(api_key),
        "api_key_masked": ("••••" + api_key[-4:]) if len(api_key) >= 4 else ("••••" if api_key else ""),
    }
    email_cfg_view = {
        **email_cfg,
        "recipients_text": ", ".join(email_cfg.get("recipients") or []),
        "smtp_password_set": bool(email_cfg.get("smtp_password")),
    }
    return render_template(
        "settings.html",
        email_cfg=email_cfg_view,
        ai_cfg=ai_cfg_view,
        active_tab=active_tab,
        agents_ready=agents_configured(),
        admin_user=auth.ADMIN_USERNAME,
    )


@app.route("/dashboard/api/settings/ai/models", methods=["POST"])
@auth.login_required
def api_ai_models():
    from agents.llm import list_models

    data = request.get_json(silent=True) or {}
    settings_data = storage.get_settings()
    ai_cfg = settings_data.get("ai") or {}
    api_key = (data.get("api_key") or "").strip() or (ai_cfg.get("api_key") or "").strip()
    base_url = (data.get("base_url") or "").strip() or (ai_cfg.get("base_url") or "").strip()
    try:
        models = list_models(api_key=api_key or None, base_url=base_url or None)
        return jsonify({"ok": True, "models": models})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc), "models": []}), 400


@app.route("/dashboard/api/status")
@auth.login_required
def api_status():
    projects = storage.list_projects()
    payload = []
    fleet = {
        "projects": 0,
        "ok_projects": 0,
        "bad_projects": 0,
        "pending_projects": 0,
        "empty_projects": 0,
        "up": 0,
        "down": 0,
        "unknown": 0,
    }
    for project in projects:
        health = storage.project_health(project)
        fleet["projects"] += 1
        fleet["up"] += health["up"]
        fleet["down"] += health["down"]
        fleet["unknown"] += health["unknown"]
        if health["total"] == 0:
            fleet["empty_projects"] += 1
        elif health["down"] > 0:
            fleet["bad_projects"] += 1
        elif health["unknown"] > 0:
            fleet["pending_projects"] += 1
        else:
            fleet["ok_projects"] += 1
        urls = []
        for entry in project.get("urls") or []:
            analysis = entry.get("last_analysis") or None
            urls.append(
                {
                    "id": entry["id"],
                    "name": entry["name"],
                    "url": entry.get("url"),
                    "enabled": entry.get("enabled", True),
                    "last_result": entry.get("last_result"),
                    "last_analysis": analysis,
                }
            )
        payload.append(
            {
                "id": project["id"],
                "name": project["name"],
                "health": health,
                "urls": urls,
            }
        )
    return jsonify(
        {
            "projects": payload,
            "fleet": fleet,
            "interval": storage.get_settings().get("check_interval_seconds", 60),
            "agents_ready": agents_configured(),
            "server_time": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }
    )


@app.route("/dashboard/api/helper/chat", methods=["GET", "POST"])
@auth.login_required
def api_helper_chat():
    if request.method == "GET":
        return jsonify({"history": get_chat_history(), "agents_ready": agents_configured()})
    data = request.get_json(silent=True) or {}
    message = data.get("message") or request.form.get("message") or ""
    result = helper_chat(message)
    return jsonify(result)


@app.route("/dashboard/api/helper/clear", methods=["POST"])
@auth.login_required
def api_helper_clear():
    clear_chat_history()
    return jsonify({"ok": True})


def create_app() -> Flask:
    storage.load()
    if not scheduler.running:
        _schedule_jobs()
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
    return app


create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)
