import requests
import smtplib
import socket
import time
import logging
import threading

from email.message import EmailMessage
from datetime import datetime, timedelta


# ============================================================
# WEBSITE MONITORING CONFIGURATION
# ============================================================

# Website will be checked every 30 minutes
CHECK_INTERVAL = 30 * 60

# Maximum time to wait for website response
REQUEST_TIMEOUT = 30

# Monitoring VM name
MONITOR_NAME = socket.gethostname()


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_SERVER = "smtp.adani.com"
SMTP_PORT = 25

SENDER_EMAIL = "farhan.vhora@adani.com"


# ============================================================
# ADMIN EMAIL CONFIGURATION
#
# These people will receive the daily consolidated report
# every day at 10:30 AM.
#
# You can add any number of admin emails.
# ============================================================

ADMIN_EMAILS = [
    "FarhanVhora@Cognitbotz.com",
    "SyedPasha@cognitbotz.com",
    "vinayreddy@cognitbotz.com",
    "Abhishek.MahadevMane@adani.com",
    "AshaDevi@cognitbotz.com"
]


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECTS = [

    {
        "name": "F & A Report Optimization",
        "url": "https://agel-agents-uat.adani.com/fna/dashboard/financial-summary",
        "developers": [
            "naumanpathan@adani.com",
            "sahil.singh1@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "Akasha Intelligence Cross Platform",
        "url": "https://digitalized-dpr-uat.adani.com/akasha",
        "developers": [
            "praveen.gunja@adani.com",
            "NikithaM@cognitbotz.com"
        ],
        "enabled": True
    },

    {
        "name": "PMAG Cost Process",
        "url": "https://agel-agents-uat.adani.com/pmag/details",
        "developers": [
            "VenkatHarshith@cognitbotz.com",
            "sahil.singh1@adani.com",
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "NDC",
        "url": "https://agel-agents-uat.adani.com/ndc/ndc-reporting/overview",
        "developers": [
            "laxminarayana@adani.com",
            "sahil.singh1@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "ENOC",
        "url": "https://agel-agents-uat.adani.com/enoc",
        "developers": [
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "Landed Tariff",
        "url": "https://agel-agents-uat.adani.com/landed-tariff/dashboard",
        "developers": [
            "SaiManohar@cognitbotz.com",
            "SaiBhargav@cognitbotz.com"
        ],
        "enabled": True
    },

    {
        "name": "Debt Pulse",
        "url": "https://aegis.adani.com/debt-markets/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "GuruPrasad@cognitbotz.com"
        ],
        "enabled": True
    },

    {
        "name": "DPR",
        "url": "https://digitalized-dpr.adani.com/",
        "developers": [
            "praveen.gunja@adani.com",
            "NikithaM@cognitbotz.com"
        ],
        "enabled": True
    },

    {
        "name": "IR",
        "url": "https://aegis.adani.com/equity-dashboard/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "pallavi.namburi@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "AEGIS",
        "url": "https://aegis.adani.com/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "SreejaK@cognitbotz.com",
            "Sreecharan@cognitbotz.com",
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "Carbon Credit",
        "url": "https://agel-agents.adani.com/carbon-credit-tracker/",
        "developers": [
            "Rahul.Chenna@adani.com"
        ],
        "enabled": True
    },

    {
        "name": "Plant Maintenance",
        "url": "https://agel-agents-uat.adani.com/plant-maintenance/",
        "developers": [
            "farhan.vhora@adani.com",
            "naumanpathan@adani.com",
            "FarhanVhora@cognitbotz.com"
        ],
        "enabled": True
    },

    {
        "name": "Cobot Dashboard",
        "url": "http://aegis.adani.com/cobot/home",
        "developers": [
            "praveen.gunja@adani.com"
        ],
        "enabled": True
    }
]


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

# Important for your VM environment.
#
# This prevents Python requests from using proxy settings
# available through environment variables.
#
session.trust_env = False


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename="website_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# CURRENT PROJECT STATUS
#
# Stores the latest monitoring result for every project.
# ============================================================

project_status = {}

status_lock = threading.Lock()


# ============================================================
# CHECK WEBSITE
# ============================================================

def check_website(project):

    start_time = time.time()

    try:

        response = session.get(
            project["url"],
            timeout=REQUEST_TIMEOUT,
            verify=True
        )

        response_time = round(
            (time.time() - start_time) * 1000,
            2
        )

        status_code = response.status_code


        # ----------------------------------------------------
        # WEBSITE UP
        # ----------------------------------------------------

        if 200 <= status_code < 400:

            logging.info(
                f"{project['name']} | "
                f"UP | "
                f"HTTP={status_code} | "
                f"Response={response_time}ms"
            )

            return {
                "status": "UP",
                "http_status": status_code,
                "response_time": response_time,
                "error": None
            }


        # ----------------------------------------------------
        # WEBSITE DOWN
        # ----------------------------------------------------

        else:

            error = f"HTTP {status_code}"

            logging.error(
                f"{project['name']} | "
                f"DOWN | "
                f"HTTP={status_code} | "
                f"Response={response_time}ms"
            )

            return {
                "status": "DOWN",
                "http_status": status_code,
                "response_time": response_time,
                "error": error
            }


    except requests.exceptions.Timeout:

        logging.error(
            f"{project['name']} | "
            f"DOWN | Request timeout"
        )

        return {
            "status": "DOWN",
            "http_status": None,
            "response_time": None,
            "error": "Request timeout"
        }


    except requests.exceptions.ConnectionError:

        logging.error(
            f"{project['name']} | "
            f"DOWN | Connection error"
        )

        return {
            "status": "DOWN",
            "http_status": None,
            "response_time": None,
            "error": "Connection error"
        }


    except requests.exceptions.RequestException as e:

        logging.error(
            f"{project['name']} | "
            f"DOWN | Request error: {e}"
        )

        return {
            "status": "DOWN",
            "http_status": None,
            "response_time": None,
            "error": str(e)
        }


    except Exception as e:

        logging.exception(
            f"{project['name']} | "
            f"Unexpected error"
        )

        return {
            "status": "DOWN",
            "http_status": None,
            "response_time": None,
            "error": str(e)
        }


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(subject, body, recipients, is_html=False):

    try:

        # ----------------------------------------------------
        # Validate recipients
        # ----------------------------------------------------

        if not recipients:

            logging.warning(
                f"No recipients configured | "
                f"Subject={subject}"
            )

            return False


        # ----------------------------------------------------
        # Create email
        # ----------------------------------------------------

        msg = EmailMessage()

        msg["From"] = SENDER_EMAIL

        msg["To"] = ", ".join(recipients)

        msg["Subject"] = subject


        # ----------------------------------------------------
        # HTML EMAIL
        # ----------------------------------------------------

        if is_html:

            msg.set_content(
                "Please open this email in an "
                "HTML-compatible email client."
            )

            msg.add_alternative(
                body,
                subtype="html"
            )


        # ----------------------------------------------------
        # NORMAL TEXT EMAIL
        # ----------------------------------------------------

        else:

            msg.set_content(body)


        # ----------------------------------------------------
        # SMTP SEND
        # ----------------------------------------------------

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as server:

            server.send_message(msg)


        logging.info(
            f"Email sent successfully | "
            f"Subject={subject} | "
            f"Recipients={recipients}"
        )

        return True


    except smtplib.SMTPException as e:

        logging.exception(
            f"SMTP error while sending email: {e}"
        )

        return False


    except Exception as e:

        logging.exception(
            f"Email sending failed: {e}"
        )

        return False


# ============================================================
# SEND DOWN ALERT TO DEVELOPERS
# ============================================================

def send_down_alert(
    project,
    result,
    detection_time
):

    subject = (
        f"🚨 {project['name']} "
        f"Website DOWN"
    )


    http_status = (
        result["http_status"]
        if result["http_status"] is not None
        else "N/A"
    )


    response_time = (
        f"{result['response_time']} ms"
        if result["response_time"] is not None
        else "N/A"
    )


    body = f"""
ALERT: WEBSITE DOWN

==================================================
PROJECT DETAILS
==================================================

Project:
{project['name']}

URL:
{project['url']}

Status:
DOWN

HTTP Status:
{http_status}

Error:
{result['error']}

Response Time:
{response_time}

Detection Time:
{detection_time}

Monitoring VM:
{MONITOR_NAME}


==================================================
ACTION REQUIRED
==================================================

Please check the {project['name']} application
and related server/infrastructure.

This alert was generated automatically by the
Website Monitoring System.


Regards,
Website Monitoring System
"""


    return send_email(
        subject,
        body,
        project["developers"],
        is_html=False
    )


# ============================================================
# CHECK ALL PROJECTS
# ============================================================

def check_all_projects():

    print("")
    print("==============================================")
    print("Starting monitoring cycle")
    print("==============================================")


    for project in PROJECTS:

        # ----------------------------------------------------
        # Skip disabled project
        # ----------------------------------------------------

        if not project.get("enabled", True):

            print(
                f"{project['name']} | DISABLED"
            )

            continue


        current_time = datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )


        # ----------------------------------------------------
        # Check website
        # ----------------------------------------------------

        result = check_website(project)


        # ----------------------------------------------------
        # Save latest project status
        # ----------------------------------------------------

        with status_lock:

            project_status[
                project["name"]
            ] = {

                "name":
                project["name"],

                "url":
                project["url"],

                "status":
                result["status"],

                "http_status":
                result["http_status"],

                "response_time":
                result["response_time"],

                "error":
                result["error"],

                "last_checked":
                current_time
            }


        # ----------------------------------------------------
        # WEBSITE UP
        # ----------------------------------------------------

        if result["status"] == "UP":

            print(
                f"[{current_time}] "
                f"{project['name']} | "
                f"UP | "
                f"HTTP {result['http_status']} | "
                f"{result['response_time']} ms"
            )


        # ----------------------------------------------------
        # WEBSITE DOWN
        # ----------------------------------------------------

        else:

            print(
                f"[{current_time}] "
                f"{project['name']} | "
                f"DOWN | "
                f"Reason: {result['error']}"
            )


            # Send email immediately
            email_sent = send_down_alert(
                project,
                result,
                current_time
            )


            if email_sent:

                print(
                    f"{project['name']} | "
                    f"DOWN alert email sent."
                )

            else:

                print(
                    f"{project['name']} | "
                    f"DOWN alert email FAILED."
                )


# ============================================================
# GENERATE HTML ADMIN REPORT
# ============================================================

def generate_admin_report_html():

    report_date = datetime.now().strftime(
        "%d-%m-%Y"
    )


    total_projects = 0
    up_projects = 0
    down_projects = 0
    warning_projects = 0


    project_data = []


    # ========================================================
    # COLLECT PROJECT STATUS
    # ========================================================

    for project in PROJECTS:

        if not project.get("enabled", True):

            continue


        total_projects += 1


        with status_lock:

            status = project_status.get(
                project["name"]
            )


        if not status:

            current_status = "NOT CHECKED"

        else:

            current_status = status["status"]


        if current_status == "UP":

            up_projects += 1


        elif current_status == "DOWN":

            down_projects += 1


        else:

            warning_projects += 1


        project_data.append(
            (
                project,
                status
            )
        )


    # ========================================================
    # SORT PROJECTS
    #
    # DOWN first
    # WARNING second
    # UP last
    # ========================================================

    def status_priority(item):

        project, status = item

        if not status:

            return 3

        if status["status"] == "DOWN":

            return 0

        if status["status"] == "WARNING":

            return 1

        if status["status"] == "UP":

            return 2

        return 3


    project_data.sort(
        key=status_priority
    )


    # ========================================================
    # PROJECT HTML CARDS
    # ========================================================

    project_cards = []


    for project, status in project_data:

        # ----------------------------------------------------
        # NOT CHECKED
        # ----------------------------------------------------

        if not status:

            project_cards.append(
                f"""
                <div style="
                    padding: 16px;
                    margin-bottom: 12px;
                    border-left: 6px solid #808080;
                    background-color: #f3f3f3;
                    border-radius: 6px;
                ">

                    <div style="
                        font-size: 17px;
                        font-weight: bold;
                        color: #222222;
                    ">

                        {project['name']}

                        <span style="
                            color: #808080;
                            margin-left: 10px;
                        ">
                            ⚪ NOT CHECKED
                        </span>

                    </div>

                </div>
                """
            )

            continue


        # ----------------------------------------------------
        # UP
        # ----------------------------------------------------

        if status["status"] == "UP":

            status_text = "🟢 UP"

            status_color = "#16803c"

            border_color = "#16803c"

            background_color = "#eefaf2"


        # ----------------------------------------------------
        # DOWN
        # ----------------------------------------------------

        elif status["status"] == "DOWN":

            status_text = "🔴 DOWN"

            status_color = "#d93025"

            border_color = "#d93025"

            background_color = "#fff0f0"


        # ----------------------------------------------------
        # WARNING
        # ----------------------------------------------------

        else:

            status_text = "🟡 WARNING"

            status_color = "#d97706"

            border_color = "#d97706"

            background_color = "#fff8e6"


        # ----------------------------------------------------
        # HTTP STATUS
        # ----------------------------------------------------

        if status["http_status"] is not None:

            http_status = status["http_status"]

        else:

            http_status = "N/A"


        # ----------------------------------------------------
        # RESPONSE TIME
        # ----------------------------------------------------

        if status["response_time"] is not None:

            response_time = (
                f"{status['response_time']} ms"
            )

        else:

            response_time = "N/A"


        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if status["error"]:

            error_html = f"""
                <div style="
                    margin-top: 8px;
                    color: #d93025;
                    font-size: 13px;
                ">
                    <b>Error:</b>
                    {status['error']}
                </div>
            """

        else:

            error_html = ""


        # ----------------------------------------------------
        # PROJECT CARD
        # ----------------------------------------------------

        project_cards.append(
            f"""
            <div style="
                padding: 18px;
                margin-bottom: 12px;
                border-left: 6px solid {border_color};
                background-color: {background_color};
                border-radius: 7px;
            ">

                <div style="
                    font-size: 18px;
                    margin-bottom: 10px;
                ">

                    <span style="
                        font-weight: bold;
                        color: #222222;
                    ">
                        {project['name']}
                    </span>

                    <span style="
                        margin-left: 12px;
                        color: {status_color};
                        font-weight: bold;
                        font-size: 17px;
                    ">
                        {status_text}
                    </span>

                </div>


                <div style="
                    font-size: 13px;
                    color: #555555;
                ">

                    <b>HTTP:</b>
                    {http_status}

                    &nbsp;&nbsp;&nbsp;

                    <b>Response:</b>
                    {response_time}

                </div>


                {error_html}


                <div style="
                    margin-top: 8px;
                    font-size: 12px;
                    color: #777777;
                ">

                    Last checked:
                    {status['last_checked']}

                </div>

            </div>
            """
        )


    # ========================================================
    # FINAL HTML
    # ========================================================

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
Daily Website Monitoring Report
</title>

</head>


<body style="
    margin: 0;
    padding: 20px;
    background-color: #f5f6f8;
    font-family: Arial, Helvetica, sans-serif;
">


<div style="
    max-width: 850px;
    margin: auto;
    background-color: #ffffff;
    padding: 25px;
    border-radius: 10px;
">


    <!-- ================================================== -->
    <!-- HEADER -->
    <!-- ================================================== -->

    <div style="
        border-bottom: 2px solid #dddddd;
        padding-bottom: 15px;
        margin-bottom: 20px;
    ">

        <div style="
            font-size: 24px;
            font-weight: bold;
            color: #222222;
        ">
            Website Monitoring Report
        </div>


        <div style="
            margin-top: 6px;
            color: #666666;
            font-size: 14px;
        ">
            Daily Consolidated Report |
            {report_date}
        </div>

    </div>


    <!-- ================================================== -->
    <!-- SUMMARY -->
    <!-- ================================================== -->

    <div style="
        margin-bottom: 25px;
    ">

        <table style="
            width: 100%;
            border-collapse: collapse;
        ">

            <tr>

                <!-- TOTAL -->

                <td style="
                    width: 25%;
                    padding: 10px;
                ">

                    <div style="
                        background-color: #f3f4f6;
                        padding: 15px;
                        text-align: center;
                        border-radius: 7px;
                    ">

                        <div style="
                            font-size: 12px;
                            color: #666666;
                        ">
                            TOTAL
                        </div>

                        <div style="
                            font-size: 25px;
                            font-weight: bold;
                            color: #222222;
                        ">
                            {total_projects}
                        </div>

                    </div>

                </td>


                <!-- UP -->

                <td style="
                    width: 25%;
                    padding: 10px;
                ">

                    <div style="
                        background-color: #eefaf2;
                        padding: 15px;
                        text-align: center;
                        border-radius: 7px;
                    ">

                        <div style="
                            font-size: 12px;
                            color: #16803c;
                        ">
                            UP
                        </div>

                        <div style="
                            font-size: 25px;
                            font-weight: bold;
                            color: #16803c;
                        ">
                            {up_projects}
                        </div>

                    </div>

                </td>


                <!-- DOWN -->

                <td style="
                    width: 25%;
                    padding: 10px;
                ">

                    <div style="
                        background-color: #fff0f0;
                        padding: 15px;
                        text-align: center;
                        border-radius: 7px;
                    ">

                        <div style="
                            font-size: 12px;
                            color: #d93025;
                        ">
                            DOWN
                        </div>

                        <div style="
                            font-size: 25px;
                            font-weight: bold;
                            color: #d93025;
                        ">
                            {down_projects}
                        </div>

                    </div>

                </td>


                <!-- WARNING -->

                <td style="
                    width: 25%;
                    padding: 10px;
                ">

                    <div style="
                        background-color: #fff8e6;
                        padding: 15px;
                        text-align: center;
                        border-radius: 7px;
                    ">

                        <div style="
                            font-size: 12px;
                            color: #d97706;
                        ">
                            WARNING
                        </div>

                        <div style="
                            font-size: 25px;
                            font-weight: bold;
                            color: #d97706;
                        ">
                            {warning_projects}
                        </div>

                    </div>

                </td>

            </tr>

        </table>

    </div>


    <!-- ================================================== -->
    <!-- PROJECT STATUS -->
    <!-- ================================================== -->

    <div style="
        font-size: 19px;
        font-weight: bold;
        color: #222222;
        margin-bottom: 15px;
    ">
        Project Status
    </div>


    {''.join(project_cards)}


    <!-- ================================================== -->
    <!-- MONITORING VM -->
    <!-- ================================================== -->

    <div style="
        margin-top: 25px;
        padding-top: 15px;
        border-top: 1px solid #dddddd;
        font-size: 12px;
        color: #888888;
    ">

        Monitoring VM:
        <b>{MONITOR_NAME}</b>

        <br><br>

        This is an automated report generated by the
        Website Monitoring System.

    </div>


</div>


</body>

</html>
"""

    return html


# ============================================================
# SEND DAILY ADMIN REPORT
# ============================================================

def send_daily_admin_report():

    try:

        html_report = generate_admin_report_html()


        subject = (
            "📊 Daily Website Monitoring Report - "
            f"{datetime.now().strftime('%d-%m-%Y')}"
        )


        success = send_email(
            subject,
            html_report,
            ADMIN_EMAILS,
            is_html=True
        )


        if success:

            print(
                "Daily consolidated admin report "
                "sent successfully."
            )

        else:

            print(
                "Daily consolidated admin report FAILED."
            )


    except Exception as e:

        logging.exception(
            f"Failed to generate admin report: {e}"
        )

        print(
            f"Admin report error: {e}"
        )


# ============================================================
# ADMIN REPORT SCHEDULER
#
# Sends the consolidated report every day at 10:30 AM.
# ============================================================

def admin_report_scheduler():

    print(
        "Admin report scheduler started."
    )


    while True:

        try:

            now = datetime.now()


            # ------------------------------------------------
            # Today's 10:00 AM
            # ------------------------------------------------

            target = now.replace(
                hour=10,
                minute=30,
                second=0,
                microsecond=0
            )


            # ------------------------------------------------
            # If 10 AM has already passed,
            # schedule for tomorrow.
            # ------------------------------------------------

            if now >= target:

                target += timedelta(
                    days=1
                )


            wait_seconds = (
                target - now
            ).total_seconds()


            print(
                "Next admin report scheduled for: "
                f"{target.strftime('%d-%m-%Y %H:%M:%S')}"
            )


            # ------------------------------------------------
            # Wait until 10 AM
            # ------------------------------------------------

            time.sleep(
                wait_seconds
            )


            # ------------------------------------------------
            # Send report
            # ------------------------------------------------

            send_daily_admin_report()


        except Exception as e:

            logging.exception(
                f"Admin scheduler error: {e}"
            )

            # Prevent scheduler from dying permanently
            time.sleep(60)


# ============================================================
# MAIN MONITOR
# ============================================================

def monitor():

    print("")
    print("==============================================")
    print("       WEBSITE MONITORING SYSTEM")
    print("==============================================")

    print(
        f"Monitoring VM      : {MONITOR_NAME}"
    )

    print(
        f"Projects configured: {len(PROJECTS)}"
    )

    print(
        f"Check interval     : "
        f"{CHECK_INTERVAL // 60} minute(s)"
    )

    print(
        "Admin report       : Every day at 10:30 AM"
    )

    print("")


    # ========================================================
    # SHOW PROJECT CONFIGURATION
    # ========================================================

    print(
        "Configured Projects:"
    )

    print(
        "----------------------------------------------"
    )


    for project in PROJECTS:

        if project.get("enabled", True):

            project_state = "ENABLED"

        else:

            project_state = "DISABLED"


        print(
            f"{project['name']} | "
            f"{project_state} | "
            f"Developers: "
            f"{len(project['developers'])}"
        )


    print(
        "----------------------------------------------"
    )

    print("")


    # ========================================================
    # START ADMIN REPORT THREAD
    # ========================================================

    scheduler_thread = threading.Thread(
        target=admin_report_scheduler,
        daemon=True
    )

    scheduler_thread.start()


    # ========================================================
    # MAIN MONITORING LOOP
    # ========================================================

    while True:

        try:

            check_all_projects()

        except Exception as e:

            logging.exception(
                f"Monitoring cycle error: {e}"
            )

            print(
                f"Monitoring cycle error: {e}"
            )


        print("")
        print(
            "=============================================="
        )

        print(
            f"Next monitoring cycle in "
            f"{CHECK_INTERVAL // 60} minute(s)..."
        )

        print(
            "=============================================="
        )

        print("")


        # Wait until next monitoring cycle
        time.sleep(
            CHECK_INTERVAL
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        monitor()


    except KeyboardInterrupt:

        logging.info(
            "Monitoring stopped by user."
        )

        print("")
        print(
            "Monitoring stopped."
        )


    except Exception as e:

        logging.exception(
            f"Fatal monitoring error: {e}"
        )

        print(
            f"Fatal error: {e}"
        )