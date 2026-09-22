(() => {
  document.querySelectorAll("[data-open]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-open");
      const dialog = document.getElementById(id);
      if (dialog && typeof dialog.showModal === "function") dialog.showModal();
    });
  });

  document.querySelectorAll("dialog.modal").forEach((dialog) => {
    dialog.querySelectorAll("[data-close]").forEach((btn) => {
      btn.addEventListener("click", () => dialog.close());
    });
    dialog.addEventListener("click", (event) => {
      const rect = dialog.getBoundingClientRect();
      const inside =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (!inside) dialog.close();
    });
  });

  document.querySelectorAll("[data-dev-editor]").forEach((editor) => {
    const rows = editor.querySelector("[data-dev-rows]");
    const addBtn = editor.querySelector("[data-add-dev]");
    if (!rows || !addBtn) return;
    addBtn.addEventListener("click", () => {
      const row = document.createElement("div");
      row.className = "dev-row";
      row.innerHTML =
        '<input type="text" name="developer_name" placeholder="Name" />' +
        '<input type="email" name="developer_email" placeholder="email@company.com" />';
      rows.appendChild(row);
    });
  });

  const serviceRowHtml =
    '<div class="service-row">' +
    '<input type="text" name="service_name" placeholder="Service name (e.g. Auth API)" />' +
    '<input type="url" name="service_url" placeholder="https://api.example.com/health" />' +
    '<input type="number" name="service_expected" value="200" min="100" max="599" title="Expected status" />' +
    '<input type="number" name="service_timeout" value="10" min="1" max="120" title="Timeout seconds" />' +
    "</div>";

  document.querySelectorAll("[data-service-editor]").forEach((editor) => {
    const rows = editor.querySelector("[data-service-rows]");
    const addBtn = editor.querySelector("[data-add-service]");
    if (!rows || !addBtn) return;
    addBtn.addEventListener("click", () => {
      rows.insertAdjacentHTML("beforeend", serviceRowHtml);
    });
  });

  function formatChecked(iso) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleString();
    } catch {
      return iso;
    }
  }

  document.querySelectorAll("[data-checked]").forEach((el) => {
    const raw = (el.textContent || "").replace(/\s+/g, " ").trim();
    // Strip icon labels; keep ISO-looking tail
    const match = raw.match(/\d{4}-\d{2}-\d{2}T[\d:.+-]+Z?/);
    const value = match ? match[0] : raw.replace(/^[^0-9—]+/, "").trim();
    if (value && value !== "—") {
      el.innerHTML =
        '<i data-lucide="calendar-clock" class="icon icon-sm"></i>' +
        formatChecked(value);
    }
  });

  document.querySelectorAll(".history-item span:first-child").forEach((el) => {
    el.textContent = formatChecked(el.textContent.trim());
  });

  document.querySelectorAll(".analysis-head .tiny").forEach((el) => {
    const raw = el.textContent.trim();
    if (raw) el.textContent = formatChecked(raw);
  });

  if (window.lucide) window.lucide.createIcons();

  function badgeHtml(r, enabled) {
    if (enabled === false) {
      return { cls: "badge-muted", html: '<i data-lucide="pause" class="icon"></i>Paused' };
    }
    if (!r) {
      return { cls: "badge-muted", html: '<i data-lucide="clock" class="icon"></i>Still checking' };
    }
    if (r.ok) {
      return { cls: "badge-ok", html: '<i data-lucide="check" class="icon"></i>Working fine' };
    }
    if (r.label === "issue") {
      return { cls: "badge-warn", html: '<i data-lucide="alert-triangle" class="icon"></i>Having a problem' };
    }
    return { cls: "badge-down", html: '<i data-lucide="unplug" class="icon"></i>Not responding' };
  }

  function applyResult(node, r, enabled) {
    const badge = node.querySelector("[data-status-badge]");
    const msg = node.querySelector("[data-status-msg]");
    const latency = node.querySelector("[data-latency]");
    const checked = node.querySelector("[data-checked]");
    if (!badge) return;
    const info = badgeHtml(r, enabled);
    badge.className = "badge " + info.cls;
    badge.innerHTML = info.html;
    if (msg) {
      if (!r) msg.textContent = "Waiting for the first check…";
      else if (r.ok) msg.textContent = "Responding normally";
      else if (r.label === "issue") msg.textContent = "Opened, but the response was unexpected";
      else msg.textContent = "Could not reach this page right now";
    }
    if (latency) {
      let speed = "—";
      if (r && r.response_ms != null) {
        if (r.response_ms < 800) speed = "Fast";
        else if (r.response_ms < 2500) speed = "OK speed";
        else speed = "Slow";
      }
      latency.innerHTML =
        '<i data-lucide="gauge" class="icon icon-sm"></i>' + speed;
    }
    if (checked) {
      checked.innerHTML =
        '<i data-lucide="calendar-clock" class="icon icon-sm"></i>' +
        (r ? formatChecked(r.checked_at) : "—");
    }
    if (window.lucide) window.lucide.createIcons();
  }

  function updateProjectBadge(node, h) {
    const badge = node.querySelector("[data-project-badge]");
    const plain = node.querySelector("[data-plain-status]");
    if (!badge || !h) return;
    if (!h.total) {
      badge.className = "badge badge-muted";
      badge.innerHTML = '<i data-lucide="circle-dashed" class="icon"></i>Not set up';
      node.classList.remove("state-ok", "state-down", "state-pending", "state-empty", "has-down");
      node.classList.add("state-empty");
      if (plain) {
        plain.textContent = "Not set up";
        plain.className = "plain-status plain-status-empty";
      }
    } else if (h.down > 0) {
      badge.className = "badge badge-down";
      badge.innerHTML = `<i data-lucide="triangle-alert" class="icon"></i>${h.down} problem${h.down === 1 ? "" : "s"}`;
      node.classList.remove("state-ok", "state-down", "state-pending", "state-empty");
      node.classList.add("state-down", "has-down");
      if (plain) {
        plain.textContent = "Needs attention";
        plain.className = "plain-status plain-status-down";
      }
    } else if (h.unknown > 0) {
      badge.className = "badge badge-warn";
      badge.innerHTML = '<i data-lucide="clock" class="icon"></i>Still checking';
      node.classList.remove("state-ok", "state-down", "state-pending", "state-empty", "has-down");
      node.classList.add("state-pending");
      if (plain) {
        plain.textContent = "Still checking";
        plain.className = "plain-status plain-status-pending";
      }
    } else {
      badge.className = "badge badge-ok";
      badge.innerHTML = '<i data-lucide="check" class="icon"></i>Working fine';
      node.classList.remove("state-ok", "state-down", "state-pending", "state-empty", "has-down");
      node.classList.add("state-ok");
      if (plain) {
        plain.textContent = "Working fine";
        plain.className = "plain-status plain-status-ok";
      }
    }
    if (!h.total || h.down === 0) {
      node.classList.remove("has-down");
    }
  }

  function updateAnalysisBox(row, url) {
    const box = row.querySelector("[data-analysis-box]");
    if (!box) return;
    const r = url.last_result;
    const a = url.last_analysis;
    if (a && r && !r.ok) {
      box.hidden = false;
      box.innerHTML =
        '<div class="analysis-head"><span class="badge badge-warn"><i data-lucide="sparkles" class="icon"></i>Simple explanation</span></div>' +
        `<p class="analysis-summary" data-analysis-summary>${a.summary || ""}</p>` +
        (a.likely_cause
          ? `<p class="tiny" data-analysis-cause><strong>Likely reason:</strong> ${a.likely_cause}</p>`
          : "");
    } else {
      box.hidden = true;
      box.innerHTML = "";
    }
  }

  function updateFleet(fleet) {
    if (!fleet) return;
    const pending = fleet.pending_projects ?? 0;
    const map = {
      "[data-fleet-projects]": fleet.projects,
      "[data-fleet-ok]": fleet.ok_projects,
      "[data-fleet-bad]": fleet.bad_projects,
      "[data-fleet-pending]": pending,
      "[data-fleet-up]": fleet.up,
      "[data-fleet-down]": fleet.down,
    };
    Object.entries(map).forEach(([sel, val]) => {
      document.querySelectorAll(sel).forEach((el) => {
        el.textContent = val ?? 0;
      });
    });

    const banner = document.getElementById("status-banner");
    const title = document.querySelector("[data-mood-title]");
    const text = document.querySelector("[data-mood-text]");
    if (banner && title && text) {
      let mood = "good";
      let moodTitle = "Everything looks good";
      let moodText = "All monitored apps are responding normally right now.";
      if ((fleet.bad_projects || 0) > 0) {
        mood = "attention";
        moodTitle = "Some apps need attention";
        moodText =
          "One or more apps are not working as expected. Scroll down to see which ones and who to contact.";
      } else if ((fleet.unknown || 0) > 0 || pending > 0) {
        mood = "checking";
        moodTitle = "Still checking a few apps";
        moodText =
          "Most look fine. A few are still being checked — this page updates by itself.";
      }
      banner.className = "status-banner status-" + mood;
      title.textContent = moodTitle;
      text.textContent = moodText;
    }
  }

  async function refreshStatus() {
    try {
      const res = await fetch(window.API_URLS.status, { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const data = await res.json();
      const byProject = Object.fromEntries((data.projects || []).map((p) => [p.id, p]));
      updateFleet(data.fleet);
      const clock = document.querySelector("[data-live-clock], #live-clock");
      if (clock) {
        const t = data.server_time ? new Date(data.server_time) : new Date();
        clock.textContent =
          "· synced " +
          t.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      }
      if (window.PingCharts && typeof window.PingCharts.update === "function") {
        window.PingCharts.update(data);
      }

      document.querySelectorAll("[data-project-id]").forEach((node) => {
        const id = node.getAttribute("data-project-id");
        const project = byProject[id];
        if (!project) return;
        const h = project.health || {};
        const up = node.querySelector("[data-health-up]");
        const down = node.querySelector("[data-health-down]");
        const unknown = node.querySelector("[data-health-unknown]");
        const total = node.querySelector("[data-health-total]");
        const count = node.querySelector("[data-service-count]");
        if (up) up.textContent = h.up ?? 0;
        if (down) down.textContent = h.down ?? 0;
        if (unknown) unknown.textContent = h.unknown ?? 0;
        if (total) total.textContent = h.total ?? 0;
        if (count) count.textContent = (project.urls || []).length;
        updateProjectBadge(node, h);

        const urls = Object.fromEntries((project.urls || []).map((u) => [u.id, u]));
        node.querySelectorAll("[data-url-id]").forEach((row) => {
          const url = urls[row.getAttribute("data-url-id")];
          if (!url) return;
          applyResult(row, url.last_result, url.enabled);
          row.classList.toggle("is-error", !!(url.last_result && !url.last_result.ok));
          row.classList.toggle("is-ok", !!(url.last_result && url.last_result.ok));
          updateAnalysisBox(row, url);
        });
      });

      const list = document.getElementById("url-table");
      if (list) {
        const projectId = document.querySelector(".health-strip")?.getAttribute("data-project-id");
        const project = byProject[projectId];
        if (project) {
          const urls = Object.fromEntries((project.urls || []).map((u) => [u.id, u]));
          list.querySelectorAll("[data-url-id]").forEach((node) => {
            const url = urls[node.getAttribute("data-url-id")];
            if (!url) return;
            applyResult(node, url.last_result, url.enabled);
          });
        }
      }
      if (window.lucide) window.lucide.createIcons();
    } catch {
      /* ignore */
    }
  }

  const refreshMs = document.getElementById("insight-grid") ? 8000 : 15000;
  if (document.querySelector("[data-project-id], #url-table, #insight-grid")) {
    setInterval(refreshStatus, refreshMs);
  }

  /* Helper drawer */
  const drawer = document.getElementById("helper-drawer");
  const backdrop = document.getElementById("helper-backdrop");
  const openBtn = document.getElementById("helper-open");
  const closeBtn = document.getElementById("helper-close");
  const clearBtn = document.getElementById("helper-clear");
  const form = document.getElementById("helper-form");
  const input = document.getElementById("helper-input");
  const messages = document.getElementById("helper-messages");

  function setHelperOpen(open) {
    if (!drawer) return;
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    if (backdrop) backdrop.hidden = !open;
  }

  function addBubble(role, text) {
    if (!messages) return;
    const div = document.createElement("div");
    div.className = `helper-bubble ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function loadHelperHistory() {
    if (!messages) return;
    try {
      const res = await fetch(window.API_URLS.helperChat);
      if (!res.ok) return;
      const data = await res.json();
      messages.innerHTML = "";
      (data.history || []).forEach((item) => {
        addBubble(item.role === "user" ? "user" : "assistant", item.content);
      });
      if (!(data.history || []).length) {
        addBubble(
          "assistant",
          data.agents_ready
            ? "Hi — ask me what’s down, who owns a project, or summarize health."
            : "AI is offline. Add an API key in Settings → AI Config."
        );
      }
    } catch {
      /* ignore */
    }
  }

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      setHelperOpen(true);
      loadHelperHistory();
      input?.focus();
    });
  }
  closeBtn?.addEventListener("click", () => setHelperOpen(false));
  backdrop?.addEventListener("click", () => setHelperOpen(false));
  clearBtn?.addEventListener("click", async () => {
    await fetch(window.API_URLS.helperClear, { method: "POST" });
    if (messages) messages.innerHTML = "";
    addBubble("assistant", "Chat cleared.");
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = (input?.value || "").trim();
    if (!text) return;
    addBubble("user", text);
    input.value = "";
    const thinking = document.createElement("div");
    thinking.className = "helper-bubble assistant thinking";
    thinking.textContent = "Thinking…";
    messages.appendChild(thinking);
    const started = Date.now();
    try {
      const res = await fetch(window.API_URLS.helperChat, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      const ms = Date.now() - started;
      thinking.classList.remove("thinking");
      thinking.textContent = data.reply || "No reply.";
      const meta = document.createElement("div");
      meta.className = "tiny muted";
      meta.style.marginTop = "0.25rem";
      meta.textContent = `${ms} ms`;
      thinking.appendChild(document.createElement("br"));
      thinking.appendChild(meta);
    } catch {
      thinking.classList.remove("thinking");
      thinking.textContent = "Could not reach Helper.";
    }
    messages.scrollTop = messages.scrollHeight;
  });
})();
