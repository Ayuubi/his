/* global frappe, $ */

frappe.pages["patient-history-view"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Patient History",
    single_column: true,
  });

  const patient =
    frappe.get_route() && frappe.get_route()[1] ? frappe.get_route()[1] : "";

  const esc = (x) => frappe.utils.escape_html(String(x || ""));

  function todayISO(d = new Date()) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }
  function yearAgoISO() {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return todayISO(d);
  }

  function labelize(key) {
    return String(key || "")
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/\b\w/g, (m) => m.toUpperCase());
  }

  function isEmptyValue(v) {
    return v === null || v === undefined || v === "" || v === 0;
  }

  // Build dynamic column list from rows (array of dict)
  // - excludes keys in excludeKeys
  // - keeps preferredOrder first if present, then the rest
  function buildColumns(rows, preferredOrder = [], excludeKeys = []) {
    const exclude = new Set(excludeKeys || []);
    const keys = new Set();

    (rows || []).forEach((r) => {
      Object.keys(r || {}).forEach((k) => {
        if (!exclude.has(k)) keys.add(k);
      });
    });

    const all = Array.from(keys);

    const order = [];
    const seen = new Set();
    preferredOrder.forEach((k) => {
      if (keys.has(k) && !seen.has(k)) {
        order.push(k);
        seen.add(k);
      }
    });

    all
      .filter((k) => !seen.has(k))
      .forEach((k) => {
        order.push(k);
        seen.add(k);
      });

    return order.map((k) => ({
      key: k,
      label: labelize(k),
    }));
  }

  function renderTable({ rows, columns, rightAlignKeys = [] }) {
    const rAlign = new Set(rightAlignKeys || []);

    if (!rows || !rows.length) {
      return `<div class="phv-empty">No rows</div>`;
    }
    if (!columns || !columns.length) {
      return `<div class="phv-empty">No columns</div>`;
    }

    const thead = columns
      .map((c) => `<th class="${rAlign.has(c.key) ? "phv-rightcol" : ""}">${esc(c.label)}</th>`)
      .join("");

    const tbody = rows
      .map((r) => {
        const tds = columns
          .map((c) => {
            const v = r ? r[c.key] : "";
            return `<td class="${rAlign.has(c.key) ? "phv-rightcol" : ""}">${esc(
              isEmptyValue(v) ? "" : v
            )}</td>`;
          })
          .join("");
        return `<tr>${tds}</tr>`;
      })
      .join("");

    return `
      <table class="phv-table">
        <thead><tr>${thead}</tr></thead>
        <tbody>${tbody}</tbody>
      </table>
    `;
  }

  const styleId = "phv-style";
  if (!document.getElementById(styleId)) {
    $(`<style id="${styleId}">
      .phv-wrap{display:flex; gap:14px; min-height:72vh;}
      .phv-left{width:340px; border-right:1px solid var(--border-color, #eee); padding-right:14px;}
      .phv-right{flex:1; min-width:0;}
      .phv-card{border:1px solid var(--border-color, #eee); border-radius:18px; padding:12px; margin-bottom:12px; background:var(--card-bg, #fff);}
      .phv-card-head{display:flex; justify-content:space-between; align-items:flex-start; gap:12px;}
      .phv-title{font-weight:900; font-size:14px; color:var(--text-color, #222);}
      .phv-sub{font-size:12px; color:var(--text-muted, #666); margin-top:2px;}
      .phv-badges{display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end;}
      .phv-badge{font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--border-color, #eee); color:#444; background:#fafafa;}
      .phv-chip{font-size:11px; padding:3px 10px; border-radius:999px; border:1px solid #eaeaea; background:#fff; cursor:pointer;}
      .phv-chip:hover{background:#fafafa;}
      .phv-chip.active{border-color:#333; box-shadow:0 0 0 1px #333 inset;}
      .phv-section-title{font-weight:900; margin:14px 0 8px; color:#444; letter-spacing:.2px;}
      .phv-sticky{position:sticky; top:0; background:var(--page-bg, #fff); padding:10px 0; z-index:2;}
      .phv-kv{display:flex; gap:12px; padding:7px 0; border-bottom:1px dashed #f0f0f0;}
      .phv-k{width:220px; font-size:12px; color:var(--text-muted, #666);}
      .phv-v{flex:1; font-size:12px; color:var(--text-color, #222); min-width:0; word-break:break-word;}
      .phv-table{width:100%; border-collapse:separate; border-spacing:0; margin-top:10px; font-size:12px;}
      .phv-table th,.phv-table td{border:1px solid var(--border-color, #eee); padding:7px 8px; vertical-align:top;}
      .phv-table th{background:#fafafa; font-weight:800;}
      .phv-rightcol{text-align:right;}
      .phv-empty{color:var(--text-muted, #666); padding:12px;}
      .phv-search{margin-top:10px;}
      .phv-hr{height:1px; background:var(--border-color, #eee); margin:12px 0;}
      .phv-grid{display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px;}
      .phv-mini{border:1px solid #eee; border-radius:14px; padding:10px; background:#fff;}
      .phv-mini .t{font-size:11px; color:#777; font-weight:800;}
      .phv-mini .v{font-size:13px; font-weight:900; margin-top:2px;}
      .phv-muted{color:var(--text-muted, #666);}
	  .phv-chip-mini{
		display:inline-flex;
		align-items:center;
		gap:6px;
		max-width:260px;
		padding:2px 10px;
		border-radius:999px;
		border:1px solid var(--border-color,#eee);
		background:#fafafa;
		font-size:11px;
		white-space:nowrap;
		overflow:hidden;
		text-overflow:ellipsis;
		}
		.phv-chip-mini b{font-weight:800;}
    </style>`).appendTo("head");
  }

  page.set_primary_action("Print Full Report", () => {
    if (!patient) return;
    const url = `/api/method/his.api.p_history.get_history?patient=${encodeURIComponent(
      patient
    )}`;
    window.open(url, "_blank");
  });

  $(wrapper).html(`
    <div class="phv-wrap">
      <div class="phv-left">
        <div class="phv-sticky">

          <div class="phv-card">
            <div class="phv-title">Patient Summary</div>
            <div class="phv-sub">Quick clinical snapshot</div>

            <div class="phv-grid" id="phv-summary">
              <div class="phv-mini"><div class="t">Last Vitals</div><div class="v">—</div></div>
              <div class="phv-mini"><div class="t">Abnormal Labs</div><div class="v">—</div></div>
              <div class="phv-mini"><div class="t">Last Procedure</div><div class="v">—</div></div>
              <div class="phv-mini"><div class="t">Medications</div><div class="v">—</div></div>
            </div>
          </div>

          <div class="phv-card">
            <div class="phv-title">Filters</div>
            <div class="phv-sub">Doctor viewer (fast)</div>

            <div style="margin-top:12px;">
              <label class="text-muted" style="font-size:12px;">From</label>
              <input type="date" class="form-control" id="phv-from">
            </div>

            <div style="margin-top:10px;">
              <label class="text-muted" style="font-size:12px;">To</label>
              <input type="date" class="form-control" id="phv-to">
            </div>

            <div class="phv-search">
              <label class="text-muted" style="font-size:12px;">Search (drug/test/doctor)</label>
              <input type="text" class="form-control" id="phv-q" placeholder="e.g. albumin, clexane, suufi">
            </div>

            <div style="margin-top:12px; display:flex; gap:8px; align-items:center;">
              <button class="btn btn-primary btn-sm" id="phv-refresh">Refresh</button>
              <button class="btn btn-default btn-sm" id="phv-clear">Clear</button>
            </div>

            <div class="phv-hr"></div>
            <div class="phv-sub" style="font-weight:700;">Sections</div>
            <div style="margin-top:8px;" id="phv-sections"></div>
          </div>

        </div>
      </div>

      <div class="phv-right">
        <div class="phv-card">
          <div class="phv-card-head">
            <div>
              <div class="phv-title">${patient ? esc(patient) : "No patient selected"}</div>
			  <div class="phv-title" id="phv-patient-name">—</div>
              <div class="phv-sub">Timeline • grouped by clinical meaning</div>
            </div>
            <div class="phv-badges" id="phv-top-badges"></div>
          </div>
        </div>

        <div id="phv-content" class="phv-empty">Loading…</div>
      </div>
    </div>
  `);

  $("#phv-from").val(yearAgoISO());
  $("#phv-to").val(todayISO());

  function render_badges(summary) {
    const $b = $("#phv-top-badges");
    $b.empty();
    if (!summary) return;

    const items = [];
    if (summary.total_cards != null)
      items.push({ t: `Cards: ${summary.total_cards}` });
    if (summary.sections != null)
      items.push({ t: `Sections: ${summary.sections}` });
    if (summary.abnormal != null)
      items.push({ t: `Abnormal: ${summary.abnormal}` });

    items.forEach((x) => $b.append(`<span class="phv-badge">${esc(x.t)}</span>`));
  }

  function matches_query(card, q) {
    if (!q) return true;
    const s = JSON.stringify(card || {}).toLowerCase();
    return s.includes(q.toLowerCase());
  }

  let last_payload = null;
  let active_tab_idx = 0;

  function build_summary(payload) {
    const sections = payload.sections || [];

    let lastVitals = "";
    let abnormal = 0;
    let lastProcedure = "";
    let medsCount = 0;

    sections.forEach((s) => {
      (s.cards || []).forEach((c) => {
        if (c.type === "vitals" && (c.rows || []).length) {
          const r0 = c.rows[0] || {};
          const bp = r0.bp ? `BP ${r0.bp}` : "";
          const pulse = r0.pulse ? `P ${r0.pulse}` : "";
          lastVitals = `${r0.date || ""} ${[bp, pulse].filter(Boolean).join(" • ")}`.trim();
        }

        if (c.type === "lab") {
          // flag may exist, but if you add more lab columns it still works
          abnormal += (c.tests || []).filter((t) => t.flag).length;
        }

        if (c.type === "medication") {
          medsCount += (c.lines || []).length;
        }

        if (
          c.type === "event" &&
          !lastProcedure &&
          /procedure|ot/i.test(String(s.heading || ""))
        ) {
          lastProcedure = c.title || "";
        }
      });
    });

    const $sum = $("#phv-summary").children();
    $sum.eq(0).find(".v").text(lastVitals || "—");
    $sum.eq(1).find(".v").text(String(abnormal || 0));
    $sum
      .eq(2)
      .find(".v")
      .text(lastProcedure ? lastProcedure.replace(/^.*—\s*/, "") : "—");
    $sum.eq(3).find(".v").text(String(medsCount || 0));
  }

  function kv_from_fields(card) {
    const fields = (card.fields || []).filter(
      (f) => f && !isEmptyValue(f.value)
    );
    if (fields.length) return fields;

    // fallback: auto from raw without hardcoding
    const raw = card.raw || {};
    const exclude = new Set([
      "doctype",
      "owner",
      "modified_by",
      "creation",
      "modified",
      "idx",
      "docstatus",
      "parent",
      "parenttype",
      "parentfield",
      "_user_tags",
      "_comments",
      "_assign",
      "_liked_by",
      "patient", // you already know patient
      "name", // internal id
    ]);

    const out = [];
    Object.keys(raw || {}).forEach((k) => {
      if (exclude.has(k)) return;
      const v = raw[k];
      if (isEmptyValue(v)) return;
      out.push({ label: labelize(k), value: String(v) });
    });

    return out.slice(0, 40);
  }

  function card_html(card) {
    const title = esc(card.title || "");
    const sub = esc(card.sub || "");
    const type = String(card.type || "note");

    // ✅ Medication: dynamic table from lines keys (no hardcoded headers)
    if (type === "medication") {
      const lines = card.lines || [];
      const columns = buildColumns(lines, ["drug", "qty", "dosage"]);
      const table = renderTable({ rows: lines.slice(0, 30), columns });

      return `
        <div class="phv-card">
          <div class="phv-card-head">
            <div>
              <div class="phv-title">${title}</div>
              ${sub ? `<div class="phv-sub">${sub}</div>` : ""}
            </div>
            <div class="phv-badges">
              <span class="phv-badge">Medication</span>
              <span class="phv-badge">${esc(lines.length)} items</span>
            </div>
          </div>
          ${table}
        </div>
      `;
    }

    // ✅ Lab: dynamic columns from tests keys (no hardcoded Test/Result/Normal/Flag)
    if (type === "lab") {
      const tests = card.tests || [];
      const abnormal_count = tests.filter((t) => t.flag).length;

      // preferred order (if exists). If you add new keys, they appear automatically.
      const columns = buildColumns(tests, ["name", "result", "uom", "range", "flag"]);

      // Right align numeric-ish columns if you want (safe list)
      const table = renderTable({
        rows: tests,
        columns,
        rightAlignKeys: ["result"],
      });

      return `
        <div class="phv-card">
          <div class="phv-card-head">
            <div>
              <div class="phv-title">${title}</div>
              ${sub ? `<div class="phv-sub">${sub}</div>` : ""}
            </div>
            <div class="phv-badges">
              <span class="phv-badge">Lab</span>
              <span class="phv-badge">${esc(tests.length)} rows</span>
              <span class="phv-badge">Abn: ${esc(abnormal_count)}</span>
            </div>
          </div>
          ${table}
        </div>
      `;
    }

    // ✅ Vitals: dynamic columns from rows keys (no hardcoded Pulse/Temp/RR…)
    if (type === "vitals") {
      const rows = card.rows || [];

      // Put date first if present, then whatever else exists
      const columns = buildColumns(rows, ["date"], []);

      // usually right-align numbers (everything except date)
      const rightAlign = columns
        .map((c) => c.key)
        .filter((k) => k !== "date");

      const table = renderTable({
        rows: rows.slice(0, 80),
        columns,
        rightAlignKeys: rightAlign,
      });

      return `
        <div class="phv-card">
          <div class="phv-card-head">
            <div>
              <div class="phv-title">${title}</div>
              ${sub ? `<div class="phv-sub">${sub}</div>` : ""}
            </div>
            <div class="phv-badges">
              <span class="phv-badge">Vitals</span>
              <span class="phv-badge">${esc(rows.length)} rows</span>
            </div>
          </div>
          ${table}
        </div>
      `;
    }

    // ✅ Event: show dynamic kv from card.fields (or raw fallback)
    if (type === "event") {
      const fields = kv_from_fields(card);
      function short_text(s, n = 28) {
		s = String(s || "").replace(/\s+/g, " ").trim();
		if (!s) return "";
		return s.length > n ? s.slice(0, n - 1) + "…" : s;
		}

		function strip_html(s) {
		return String(s || "").replace(/<[^>]*>/g, "");
		}

		// ...

		const chips = fields
		.slice(0, 3)
		.map((f) => {
			const lbl = esc(f.label || "");
			const rawVal = f.is_html ? strip_html(f.value) : String(f.value || "");
			const val = esc(short_text(rawVal, 26));
			// tooltip shows full text on hover
			const title = esc(rawVal);
			return `<span class="phv-chip-mini" title="${title}">
					<b>${lbl}:</b> ${val || "—"}
					</span>`;
		})
		.join("");


      const kv = fields
        .slice(0, 20)
        .map(
          (f) => `
            <div class="phv-kv">
              <div class="phv-k">${esc(f.label || "")}</div>
              <div class="phv-v">${render_value(f)}</div>


              </div>
          `
        )
        .join("");

      return `
        <div class="phv-card">
          <div class="phv-card-head">
            <div>
              <div class="phv-title">${title}</div>
              ${sub ? `<div class="phv-sub">${sub}</div>` : ""}
            </div>
            <div class="phv-badges">
              <span class="phv-badge">Event</span>
              ${chips}
            </div>
          </div>
          <div style="margin-top:8px;">${kv || `<div class="phv-empty">No details</div>`}</div>
        </div>
      `;
    }

    // ✅ Default note: dynamic kv (fields or raw fallback)
    const fields = kv_from_fields(card)
      .slice(0, 40)
      .map(
        (f) => `
          <div class="phv-kv">
            <div class="phv-k">${esc(f.label || "")}</div>
            <div class="phv-v">${render_value(f)}</div>

          </div>
        `
      )
      .join("");

    return `
      <div class="phv-card">
        <div class="phv-card-head">
          <div>
            <div class="phv-title">${title}</div>
            ${sub ? `<div class="phv-sub">${sub}</div>` : ""}
          </div>
          <div class="phv-badges">
            <span class="phv-badge">${esc(type)}</span>
          </div>
        </div>
        <div style="margin-top:8px;">${fields || `<div class="phv-empty">No details</div>`}</div>
      </div>
    `;
  }

  function render_value(field) {
    const v = String(field?.value || "");
    if (field?.is_html) {
      // Already sanitized on the server in Python (_sanitize)
      return v;
    }
    return esc(v);
  }

  function render(payload, q) {
    const sections = payload.sections || [];
    if (!sections.length) {
      $("#phv-content").html(`<div class="phv-empty">No history found for this patient in this date range.</div>`);
      $("#phv-sections").html(`<div class="phv-empty">No sections</div>`);
      render_badges({ total_cards: 0, sections: 0, abnormal: 0 });
      return;
    }

    const $content = $("#phv-content");
    const $sec = $("#phv-sections");

    build_summary(payload);

    $sec.empty();

    // Build tabs + body
    const tabsHtml = `
      <div class="phv-card" style="padding:10px;">
        <div style="display:flex; gap:8px; flex-wrap:wrap;" id="phv-tabs"></div>
      </div>
      <div id="phv-tab-body"></div>
    `;
    $content.html(tabsHtml);

    const $tabs = $("#phv-tabs");
    const $body = $("#phv-tab-body");

    function render_one_section(idx) {
      const s = sections[idx];
      if (!s) {
        $body.html(`<div class="phv-empty">No section.</div>`);
        return;
      }

      const cards = (s.cards || []).filter((c) => matches_query(c, q));
      if (!cards.length) {
        $body.html(
          `<div class="phv-empty">No data in "${esc(
            s.heading
          )}" for this range / filters.</div>`
        );
        render_badges({
          total_cards: 0,
          sections: sections.length,
          abnormal: 0,
        });
        return;
      }

      let html = `<div class="phv-section-title">${esc(s.heading || "")}</div>`;
      let abnormal_count = 0;

      cards.forEach((card) => {
        if (card.type === "lab") {
          abnormal_count += (card.tests || []).filter((t) => t.flag).length;
        }
        html += card_html(card);
      });

      render_badges({
        total_cards: cards.length,
        sections: sections.length,
        abnormal: abnormal_count,
      });

      $body.html(html);
    }

    // Build tabs
    sections.forEach((s, idx) => {
      const count = (s.cards || []).length;

      $tabs.append(`
        <button class="phv-chip ${idx === active_tab_idx ? "active" : ""}" data-tab="${idx}">
          ${esc(s.heading || "")} <span class="text-muted">(${esc(count)})</span>
        </button>
      `);

      $sec.append(`
        <div style="margin:6px 0; font-size:12px;">
          <span class="text-muted">•</span> ${esc(s.heading || "")}
          <span class="text-muted">(${esc(count)})</span>
        </div>
      `);
    });

    $tabs.find("[data-tab]").off("click").on("click", function () {
      active_tab_idx = parseInt($(this).attr("data-tab"), 10);
      $tabs.find(".phv-chip").removeClass("active");
      $(this).addClass("active");
      render_one_section(active_tab_idx);
    });

    // Keep last active tab when refreshing
    active_tab_idx = Math.min(active_tab_idx, Math.max(sections.length - 1, 0));
    render_one_section(active_tab_idx);
  }

  async function load() {
    if (!patient) {
      $("#phv-content").html(`<div class="phv-empty">No patient selected.</div>`);
      return;
    }

    $("#phv-content").html("Loading…");

    const from_date = $("#phv-from").val();
    const to_date = $("#phv-to").val();
    const q = ($("#phv-q").val() || "").trim();

    const r = await frappe.call({
      method: "his.api.p_history.get_history_view",
      args: { patient, from_date, to_date },
    });

    last_payload = r.message || {};
	$("#phv-patient-name").text(esc(last_payload.patient_name || "—"));

    render(last_payload, q);
  }

  $("#phv-refresh").on("click", () => load());
  $("#phv-clear").on("click", () => {
    $("#phv-q").val("");
    if (last_payload) render(last_payload, "");
  });
  $("#phv-q").on(
    "input",
    frappe.utils.debounce(() => {
      const q = ($("#phv-q").val() || "").trim();
      if (last_payload) render(last_payload, q);
    }, 250)
  );

  load();
};
