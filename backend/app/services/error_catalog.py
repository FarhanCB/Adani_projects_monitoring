"""Enterprise Error Diagnostic Catalog & Root-Cause Intelligence Engine.

Provides deep technical root-cause explanations, reasons, likely causes, and
actionable developer troubleshooting steps for any HTTP status code or network failure.
"""

from typing import Any, Dict, List, Optional


ERROR_CATALOG: Dict[str, Dict[str, Any]] = {
    # ==================== 5xx Server / Gateway Errors ====================
    "502": {
        "error_code": "HTTP 502",
        "title": "502 Bad Gateway — Upstream Application Service Failure",
        "category": "GATEWAY_UPSTREAM",
        "summary": "The reverse proxy (Nginx, ALB, or Envoy) reached the web server, but the upstream application process (FastAPI/Node.js/Gunicorn/IIS) crashed, is stopped, or failed to return a valid HTTP response.",
        "why_it_came": (
            "A 502 Bad Gateway occurs when the edge or reverse proxy server acts as a gateway to your backend "
            "application. When the proxy forwarded the HTTP request to the internal upstream process (e.g., "
            "127.0.0.1:8000 or an internal Docker/Kubernetes pod IP), the upstream process abruptly dropped the "
            "TCP socket, crashed before sending headers, was killed by the OS (such as Linux Out-Of-Memory OOM killer), "
            "or returned malformed bytes instead of valid HTTP protocol."
        ),
        "likely_causes": [
            "The backend application container or systemd service has crashed or is stuck in a crash loop.",
            "The upstream process ran out of RAM and was terminated by the OS Out-Of-Memory (OOM) killer.",
            "Reverse proxy is misconfigured to forward traffic to the wrong internal host or port (e.g. port mismatch).",
            "An unhandled fatal exception in backend startup code caused the worker process to exit prematurely.",
            "An internal firewall, security group, or Docker bridge network issue blocked communication between proxy and backend."
        ],
        "action_steps": [
            "1. Check backend process status on host: Run `systemctl status <service>` or `docker ps` to verify container is running.",
            "2. Inspect recent application crash logs: Run `docker logs --tail 200 <container>` or view `/var/log/<app>/error.log` for unhandled tracebacks.",
            "3. Check reverse proxy error logs: Inspect `/var/log/nginx/error.log` for 'connect() failed (111: Connection refused) while connecting to upstream'.",
            "4. Verify upstream listening port: Run `netstat -tlpn` or `ss -tulpn` on the server to verify the application is bound to the expected port.",
            "5. Restart the backend service: Run `systemctl restart <service>` or `docker restart <container>`."
        ]
    },
    "504": {
        "error_code": "HTTP 504",
        "title": "504 Gateway Timeout — Upstream Processing Exceeded Limit",
        "category": "GATEWAY_UPSTREAM",
        "summary": "The reverse proxy or load balancer waited for the backend application server to complete the request, but the application took longer than the configured gateway timeout limit.",
        "why_it_came": (
            "A 504 Gateway Timeout means the reverse proxy successfully routed the request to the upstream application, "
            "but the backend took too long to complete execution. The proxy's timeout counter (typically 30s or 60s) "
            "expired before the application sent any response headers, causing the proxy to abort the connection."
        ),
        "likely_causes": [
            "A heavy or unindexed database query blocked the database thread or locked table rows.",
            "The backend application made a synchronous blocking HTTP call to a slow or hung third-party API.",
            "Thread pool or event loop starvation: All server worker threads are tied up handling long requests.",
            "CPU starvation or memory thrashing on the server causing extreme execution latency.",
            "Database connection pool exhausted; incoming requests queued waiting for an available DB connection."
        ],
        "action_steps": [
            "1. Inspect database slow query logs and active transactions: Run `SELECT * FROM pg_stat_activity WHERE state != 'idle';` in PostgreSQL.",
            "2. Profile endpoint latency: Check if external microservices or APIs called in this route are slow or unresponsive.",
            "3. Increase worker concurrency or scale horizontal replicas to handle queue backlog.",
            "4. Check server CPU and memory usage using `htop` or cloud monitoring metrics.",
            "5. If long processing is legitimate (e.g. report generation), offload it to an asynchronous Celery/Redis worker."
        ]
    },
    "500": {
        "error_code": "HTTP 500",
        "title": "500 Internal Server Error — Unhandled Code Exception",
        "category": "SERVER_CRASH",
        "summary": "The web application encountered an unexpected runtime exception or fatal error in its code while processing the request.",
        "why_it_came": (
            "A 500 error indicates that the web server software is running, but your application code crashed during "
            "the execution of this specific HTTP request. The backend web framework caught an unhandled exception "
            "(such as a NullPointerException, KeyError, database connection refusal, or missing environment variable) "
            "and was forced to return HTTP 500."
        ),
        "likely_causes": [
            "Unhandled exception in backend application logic (e.g., accessing a missing dictionary key or null object).",
            "Database connection failed: Invalid database credentials, DB server down, or missing migration table.",
            "Missing environment variable required by the route (e.g., API keys, AWS credentials, secret keys).",
            "Dependency injection or import failure during runtime execution of the route handler."
        ],
        "action_steps": [
            "1. Check the server application error logs for the full stack trace: Look at recent entries in Sentry, CloudWatch, or local log files.",
            "2. Verify database health and migrations: Ensure all tables and columns referenced by the code exist.",
            "3. Verify `.env` configuration on the target server to ensure all required environment variables are set.",
            "4. Test the failing endpoint with the same payload in a staging environment to reproduce and debug."
        ]
    },
    "503": {
        "error_code": "HTTP 503",
        "title": "503 Service Unavailable — Capacity Exhausted or Maintenance",
        "category": "GATEWAY_UPSTREAM",
        "summary": "The server is currently unable to handle incoming requests due to temporary overloading, capacity exhaustion, or scheduled maintenance.",
        "why_it_came": (
            "An HTTP 503 Service Unavailable response indicates that the web server is operating, but has reached its "
            "maximum queue capacity or is undergoing a zero-downtime deployment where no pods/workers are ready to accept traffic."
        ),
        "likely_causes": [
            "Server traffic spike exceeded worker thread pool or maximum connection backlog.",
            "Kubernetes deployment in progress with 0 healthy replica pods passing readiness probes.",
            "Maintenance mode enabled in reverse proxy or load balancer.",
            "Web server application pool (e.g. IIS AppPool or Apache MPM) reached worker crash limits."
        ],
        "action_steps": [
            "1. Verify Kubernetes pod readiness: Run `kubectl get pods` and check `kubectl describe pod <name>` for failed readiness probes.",
            "2. Check server load metrics: Verify if CPU or RAM utilization is above 95%.",
            "3. Scale up replica count or worker process concurrency.",
            "4. Review IIS / Nginx worker connection limits."
        ]
    },

    # ==================== 4xx Client / Configuration Errors ====================
    "404": {
        "error_code": "HTTP 404",
        "title": "404 Not Found — URL Route or File Does Not Exist",
        "category": "CLIENT_CONFIGURATION",
        "summary": "The web server received the request, but no endpoint, route handler, or static file exists at the specified URL path.",
        "why_it_came": (
            "The web server successfully processed the request, but the requested URI path was not matched by any "
            "registered route in the application router, or the static asset file does not exist on disk."
        ),
        "likely_causes": [
            "Typo in the monitored URL path or missing trailing slash.",
            "The API endpoint was renamed, moved, or deprecated in a recent software deployment.",
            "Single Page Application (SPA) routing failure: Nginx is missing `try_files $uri /index.html` fallback."
        ],
        "action_steps": [
            "1. Verify the exact URL path in project settings against API documentation or Swagger UI.",
            "2. Check if a trailing slash is required (e.g. `/details/` vs `/details`).",
            "3. For React/Vue SPAs, ensure Nginx has `try_files $uri $uri/ /index.html;` configured."
        ]
    },
    "403": {
        "error_code": "HTTP 403",
        "title": "403 Forbidden — Access Denied or WAF / VPN Block",
        "category": "CLIENT_CONFIGURATION",
        "summary": "The web server understood the request, but explicitly refuses to authorize access. Often triggered by WAF rules, IP whitelisting, or missing VPN.",
        "why_it_came": (
            "An HTTP 403 Forbidden status indicates that the server's security layer actively rejected the probe. "
            "In enterprise environments, this is very frequently caused by a Web Application Firewall (WAF) "
            "blocking automated monitoring User-Agent headers, or IP restriction rules requiring corporate intranet access."
        ),
        "likely_causes": [
            "Corporate WAF / Cloudflare security rule blocked the monitoring probe's User-Agent string.",
            "The website is restricted to internal corporate IP subnets (VPN required).",
            "File permission restrictions (chmod) on the server directory hosting the application."
        ],
        "action_steps": [
            "1. Verify if the monitored website requires an internal VPN connection.",
            "2. Whitelist the monitoring server's IP address or custom User-Agent in the WAF / Security Group.",
            "3. Check web server directory permissions (`chmod 755` for directories, `644` for files)."
        ]
    },
    "401": {
        "error_code": "HTTP 401",
        "title": "401 Unauthorized — Authentication Required",
        "category": "CLIENT_CONFIGURATION",
        "summary": "The requested endpoint requires authentication credentials (Bearer Token, Basic Auth, or Session Cookie) which were missing or invalid.",
        "why_it_came": (
            "The probe accessed a protected API route that requires an authenticated session. Automated monitoring "
            "should ideally point to an unauthenticated public health check endpoint."
        ),
        "likely_causes": [
            "The monitored URL was set to a private user dashboard route instead of a public health check endpoint.",
            "API key or Bearer token expired."
        ],
        "action_steps": [
            "1. Change the monitored project URL to an unauthenticated health endpoint (e.g. `/health`, `/healthz`, `/api/health`).",
            "2. If monitoring an internal authenticated endpoint, configure probe authentication headers."
        ]
    },
    "429": {
        "error_code": "HTTP 429",
        "title": "429 Too Many Requests — Rate Limiting Triggered",
        "category": "CLIENT_CONFIGURATION",
        "summary": "The target website or API gateway has throttled probe requests because the rate limit quota was exceeded.",
        "why_it_came": (
            "The monitoring frequency or other traffic from the same IP triggered the target server's rate limiter."
        ),
        "likely_causes": [
            "Probe interval is too aggressive (e.g. probing every few seconds).",
            "Target application has a strict API rate limiter (e.g. Redis sliding window or Nginx limit_req)."
        ],
        "action_steps": [
            "1. Increase the project monitoring interval in Website Settings (e.g. 60s or 300s).",
            "2. Whitelist the monitoring server's IP in the target server's rate limiter configuration."
        ]
    },

    # ==================== Network & Infrastructure Failures ====================
    "DNS_ERROR": {
        "error_code": "DNS_RESOLUTION_FAILED",
        "title": "DNS Resolution Failure — Internal Intranet / VPN Required",
        "category": "DNS_INTERNAL",
        "summary": "The domain name cannot be resolved to an IP address by DNS resolvers. Internal Adani UAT/Intranet endpoints require corporate VPN connectivity.",
        "why_it_came": (
            "When the monitoring system attempted to look up the IP address for the hostname via getaddrinfo(), "
            "the DNS server returned NXDOMAIN or failed to respond. For Adani internal websites (e.g. `*.adani.com` "
            "internal UAT portals), DNS records are hosted on private corporate nameservers that are only reachable "
            "when connected to the Adani Corporate Network / VPN."
        ),
        "likely_causes": [
            "The monitoring worker machine is not connected to the Adani Corporate VPN / internal network.",
            "The internal UAT hostname does not exist in public DNS resolvers (8.8.8.8 / 1.1.1.1).",
            "Local DNS cache is stale or primary DNS server is unreachable."
        ],
        "action_steps": [
            "1. Connect the host machine running the monitor to the Adani Corporate VPN.",
            "2. Test resolution directly in terminal: Run `nslookup <hostname>` or `ping <hostname>`.",
            "3. If testing in production, ensure internal corporate DNS servers (10.x.x.x) are configured in `/etc/resolv.conf` or Windows network settings."
        ]
    },
    "CONNECTION_REFUSED": {
        "error_code": "TCP_CONN_REFUSED",
        "title": "TCP Connection Refused — Web Server Service Stopped",
        "category": "NETWORK_CONNECTIVITY",
        "summary": "The server IP was reached, but the server actively refused the connection on port 80/443. The web server daemon is stopped or not listening.",
        "why_it_came": (
            "A TCP Connection Refused error (errno 111 / WSAECONNREFUSED) occurs when the network packet reaches the "
            "target machine, but the operating system kernel rejects the TCP SYN handshake because no application "
            "process has called listen() on port 80 or 443."
        ),
        "likely_causes": [
            "The web server daemon (Nginx, Apache, Caddy, or IIS) is completely stopped or crashed.",
            "The web service is bound to 127.0.0.1 instead of 0.0.0.0 (not accepting external connections).",
            "Host firewall (iptables / Windows Firewall) actively rejects inbound connection attempts."
        ],
        "action_steps": [
            "1. SSH into the server and check web server status: `systemctl status nginx` or `systemctl status apache2`.",
            "2. Start or restart the web service: `systemctl start nginx`.",
            "3. Check listening sockets: Run `ss -tulpn | grep -E ':80|:443'` to confirm binding to 0.0.0.0."
        ]
    },
    "TIMEOUT": {
        "error_code": "NETWORK_TIMEOUT",
        "title": "Network Timeout (>30s) — Server Unresponsive",
        "category": "NETWORK_TIMEOUT",
        "summary": "The probe sent packets to the target server, but received no response within the 30-second timeout window.",
        "why_it_came": (
            "The monitoring agent dispatched a TCP SYN packet, but received neither an ACK nor a RST packet before "
            "the 30-second timeout limit. Packets are being silently dropped along the network path or by the server."
        ),
        "likely_causes": [
            "Network firewall or cloud security group is silently dropping packets (DROP / REJECT).",
            "Target server is powered off, rebooting, or under extreme CPU/network overload.",
            "Routing blackhole or VPN tunnel disconnection."
        ],
        "action_steps": [
            "1. Run `ping <host>` and `traceroute <host>` to identify where network packets are being dropped.",
            "2. Check cloud security group / firewall rules to verify inbound port 443 is open.",
            "3. Verify server physical / VM power state in the hypervisor or cloud portal."
        ]
    },
    "SSL_ERROR": {
        "error_code": "SSL_CERT_ERROR",
        "title": "SSL/TLS Security Handshake Failure",
        "category": "SSL_SECURITY",
        "summary": "The secure HTTPS connection failed because the SSL certificate is expired, self-signed, untrusted, or has a domain mismatch.",
        "why_it_came": (
            "During the TLS handshake, the client was unable to verify the authenticity of the server's certificate. "
            "The certificate may have passed its expiration date, was issued by an untrusted internal CA, or the Subject "
            "Alternative Name (SAN) does not match the URL domain."
        ),
        "likely_causes": [
            "The SSL/TLS certificate has passed its validity expiration date.",
            "Internal enterprise self-signed certificate where root CA is not in the system trust store.",
            "Domain name on certificate does not match the accessed URL."
        ],
        "action_steps": [
            "1. Check certificate expiration: Run `openssl s_client -connect <host>:443 -servername <host>`.",
            "2. Renew the SSL certificate using Let's Encrypt / Certbot or internal enterprise CA.",
            "3. Ensure the certificate SAN contains the exact domain name being monitored."
        ]
    },
    "SLOW_RESPONSE": {
        "error_code": "LATENCY_WARNING",
        "title": "High Latency Warning — Response Time Degradation",
        "category": "LATENCY_PERFORMANCE",
        "summary": "Website is responding with HTTP 200, but the response time exceeded the warning threshold (2000ms).",
        "why_it_came": (
            "The web server is operational, but took longer than acceptable to deliver the first byte. End users "
            "experience sluggish page loads and potential conversion drops."
        ),
        "likely_causes": [
            "Cold start of serverless / containerized backend.",
            "Unoptimized database queries lacking indexes.",
            "High concurrent server load or memory pressure."
        ],
        "action_steps": [
            "1. Profile the endpoint database queries and add missing indexes.",
            "2. Implement Redis or in-memory caching for frequently requested data.",
            "3. Scale up application server resources."
        ]
    }
}


def get_error_diagnostic(
    http_status: Optional[int] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    url: Optional[str] = None
) -> Dict[str, Any]:
    """Resolve comprehensive diagnostic profile for an error state."""
    # 1. Match by HTTP Status code
    if http_status:
        code_str = str(http_status)
        if code_str in ERROR_CATALOG:
            item = dict(ERROR_CATALOG[code_str])
            item["http_status"] = http_status
            item["target_url"] = url
            return item

    # 2. Match by Error Type string
    if error_type:
        et = error_type.lower()
        if "dns" in et:
            item = dict(ERROR_CATALOG["DNS_ERROR"])
            item["target_url"] = url
            return item
        if "connection" in et or "refused" in et:
            item = dict(ERROR_CATALOG["CONNECTION_REFUSED"])
            item["target_url"] = url
            return item
        if "timeout" in et:
            item = dict(ERROR_CATALOG["TIMEOUT"])
            item["target_url"] = url
            return item
        if "ssl" in et or "cert" in et:
            item = dict(ERROR_CATALOG["SSL_ERROR"])
            item["target_url"] = url
            return item
        if "slow" in et or "latency" in et:
            item = dict(ERROR_CATALOG["SLOW_RESPONSE"])
            item["target_url"] = url
            return item

    # 3. Match by message keywords
    if error_message:
        msg = error_message.lower()
        if "getaddrinfo" in msg or "dns" in msg or "name resolution" in msg:
            item = dict(ERROR_CATALOG["DNS_ERROR"])
            item["target_url"] = url
            return item
        if "502" in msg or "bad gateway" in msg:
            item = dict(ERROR_CATALOG["502"])
            item["target_url"] = url
            return item
        if "504" in msg or "gateway timeout" in msg:
            item = dict(ERROR_CATALOG["504"])
            item["target_url"] = url
            return item
        if "503" in msg or "unavailable" in msg:
            item = dict(ERROR_CATALOG["503"])
            item["target_url"] = url
            return item
        if "500" in msg:
            item = dict(ERROR_CATALOG["500"])
            item["target_url"] = url
            return item
        if "404" in msg:
            item = dict(ERROR_CATALOG["404"])
            item["target_url"] = url
            return item
        if "403" in msg:
            item = dict(ERROR_CATALOG["403"])
            item["target_url"] = url
            return item
        if "401" in msg:
            item = dict(ERROR_CATALOG["401"])
            item["target_url"] = url
            return item
        if "timed out" in msg:
            item = dict(ERROR_CATALOG["TIMEOUT"])
            item["target_url"] = url
            return item
        if "refused" in msg:
            item = dict(ERROR_CATALOG["CONNECTION_REFUSED"])
            item["target_url"] = url
            return item
        if "ssl" in msg:
            item = dict(ERROR_CATALOG["SSL_ERROR"])
            item["target_url"] = url
            return item

    # Generic Fallback
    return {
        "error_code": f"HTTP {http_status}" if http_status else (error_type or "UNKNOWN_ERROR"),
        "title": f"Service Disruption — {error_type or 'Anomaly Detected'}",
        "category": "GENERAL_INCIDENT",
        "summary": error_message or "An unexpected issue interrupted communication with the target website.",
        "why_it_came": (
            "The monitoring engine attempted to verify website availability, but received an abnormal response or "
            "experienced a communication fault. Review the raw error message and target server logs."
        ),
        "likely_causes": [
            "Temporary network routing anomaly or firewall block.",
            "Web service configuration change or restart in progress.",
            "Resource exhaustion or unresponsive worker thread on host."
        ],
        "action_steps": [
            "1. Test the target URL manually in a browser or via `curl -v <url>`.",
            "2. Review application error logs on the host server.",
            "3. Verify network routing and firewall permissions."
        ],
        "http_status": http_status,
        "target_url": url
    }
