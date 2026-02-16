// his/his/legacy/legacy_vitals.js

frappe.pages["legacy-vitals"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Legacy Vitals"),
    single_column: true,
  });

  const $root = $(wrapper).find(".layout-main-section");

  $root.html(`
    <div class="legacy-wrap">
      <div class="legacy-toolbar sticky">
        <div class="legacy-left">
          <div class="legacy-subtitle text-muted"></div>
          <div class="legacy-stats text-muted"></div>
        </div>

        <div class="legacy-right">
          <div class="legacy-searchbox">
            <span class="legacy-searchicon">${frappe.utils.icon("search", "sm")}</span>
            <input class="form-control legacy-search" placeholder="${__("Search vital / result / UOM...")}" />
            <button class="btn btn-default btn-sm legacy-clear" title="${__("Clear")}">
              ${frappe.utils.icon("close", "sm")}
            </button>
          </div>

          <button class="btn btn-default legacy-refresh">
            ${frappe.utils.icon("refresh", "sm")} ${__("Refresh")}
          </button>
        </div>
      </div>

      <div class="legacy-meta card">
        <div class="legacy-meta-grid">
          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Patient")}</div>
            <div class="legacy-meta-value legacy-patient"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Legacy PatientNumber")}</div>
            <div class="legacy-meta-value legacy-legacyid"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Last Recorded")}</div>
            <div class="legacy-meta-value legacy-lastdate"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Name")}</div>
            <div class="legacy-meta-value legacy-name"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Gender")}</div>
            <div class="legacy-meta-value legacy-gender"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Birth Date")}</div>
            <div class="legacy-meta-value legacy-dob"></div>
          </div>
        </div>
      </div>

      <div class="legacy-content"></div>
    </div>

    <style>
      .legacy-wrap { max-width: 1180px; margin: 0 auto; }

      .legacy-toolbar {
        display:flex; gap:12px; align-items:center; justify-content:space-between;
        padding: 10px 0 14px; margin-bottom: 10px;
      }
      .legacy-toolbar.sticky {
        position: sticky; top: var(--navbar-height, 0px);
        background: var(--page-bg, var(--bg-color, #fff));
        z-index: 9;
        border-bottom: 1px solid var(--border-color, #eee);
      }

      .legacy-left { display:flex; flex-direction:column; gap:4px; min-width: 220px; }
      .legacy-subtitle { font-size: 12px; }
      .legacy-stats { font-size: 12px; }

      .legacy-right { display:flex; gap:10px; align-items:center; }

      .legacy-searchbox { position: relative; width: min(460px, 52vw); }
      .legacy-search { padding-left: 36px; padding-right: 36px; }
      .legacy-searchicon {
        position:absolute; left: 10px; top: 50%; transform: translateY(-50%);
        opacity: .65;
      }
      .legacy-clear {
        position:absolute; right: 6px; top: 50%; transform: translateY(-50%);
        padding: 4px 6px;
        display:none;
      }

      .legacy-meta.card {
        border-radius: 14px;
        border: 1px solid var(--border-color, #eee);
        padding: 14px 16px;
        margin-bottom: 14px;
        background: var(--card-bg, var(--bg-color, #fff));
      }
      .legacy-meta-grid {
        display:grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
      }
      @media (max-width: 900px) {
        .legacy-meta-grid { grid-template-columns: 1fr; }
      }
      .legacy-meta-label { font-size: 12px; color: var(--text-muted, #777); }
      .legacy-meta-value { font-weight: 600; margin-top: 2px; }

      .legacy-group { margin-bottom: 12px; }
      .legacy-group-head {
        display:flex; align-items:center; justify-content:space-between;
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid var(--border-color, #eee);
        background: var(--card-bg, #fff);
        cursor: pointer;
        user-select: none;
      }
      .legacy-group-title { font-weight: 700; }
      .legacy-group-meta { font-size: 12px; color: var(--text-muted, #777); display:flex; gap:10px; align-items:center; }
      .legacy-chevron { opacity: .65; transition: transform .15s ease; }
      .legacy-group.collapsed .legacy-chevron { transform: rotate(-90deg); }

      .legacy-card {
        margin-top: 8px;
        background: var(--card-bg, #fff);
        border: 1px solid var(--border-color, #eee);
        border-radius: 12px;
        overflow:hidden;
      }

      .legacy-table-wrap { max-height: 56vh; overflow:auto; }
      .legacy-table { width:100%; border-collapse: collapse; }

      .legacy-table thead th {
        position: sticky; top: 0;
        background: var(--control-bg, #fafafa);
        z-index: 1;
        font-size: 12px;
      }

      .legacy-table th, .legacy-table td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border-color, #f0f0f0);
        vertical-align: top;
      }

      .legacy-table tbody tr:hover { background: rgba(0,0,0,.02); }

      .legacy-muted { color: var(--text-muted, #777); font-size: 12px; margin-top: 2px; }

      .legacy-pill {
        display:inline-flex; align-items:center; gap:6px;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid var(--border-color, #e6e6e6);
        background: var(--control-bg, #f7f7f7);
        white-space: nowrap;
      }

      .legacy-empty {
        padding: 18px;
        border: 1px dashed var(--border-color, #ddd);
        border-radius: 12px;
        background: var(--control-bg, #fcfcfc);
      }
    </style>
  `);

  const params = new URLSearchParams(window.location.search);
  const patient = params.get("patient");
  const encounter = params.get("encounter");

  const state = {
    rows: [],
    filtered: [],
    collapsed: {}, // date -> bool
  };

  function safe(x) {
    return frappe.utils.escape_html(x || "");
  }

  function fmtDate(dt) {
    if (!dt) return "";
    return frappe.datetime.str_to_user(dt);
  }

  function getRowDT(r) {
    return r.DateRecorded || r.ServiceDate || "";
  }

  function setStats() {
    const total = state.rows.length || 0;
    const shown = state.filtered.length || 0;
    const q = ($root.find(".legacy-search").val() || "").trim();

    let txt = total ? __("Showing {0} of {1} entries", [shown, total]) : __("No results");
    if (q) txt += " · " + __("Filtered by: {0}", [q]);
    $root.find(".legacy-stats").text(txt);
  }

  function groupByDate(rows) {
    const map = {};
    for (const r of rows) {
      const dt = getRowDT(r);
      const d = (dt || "").slice(0, 10); // YYYY-MM-DD
      if (!d) continue;
      map[d] = map[d] || [];
      map[d].push(r);
    }
    return Object.keys(map)
      .sort()
      .reverse()
      .map((k) => ({ date: k, rows: map[k] }));
  }

  function render() {
    const $content = $root.find(".legacy-content");
    const rows = state.filtered;

    setStats();

    if (!rows.length) {
      $content.html(`<div class="legacy-empty">${__("No legacy vitals found.")}</div>`);
      return;
    }

    const groups = groupByDate(rows);

    const html = groups
      .map((g) => {
        const isCollapsed = !!state.collapsed[g.date];
        const count = g.rows.length;

        const body = g.rows
          .map((r) => {
            const dt = getRowDT(r);
            const vital = r.VitalStatistic || "";
            const res = r.Result || "";
            const uom = r.VitalUOM || "";
            const remark = r.Remark || "";
            const ref = r.ServiceReference || "";
            const sdate = r.ServiceDate || "";

            return `
              <tr>
                <td style="white-space:nowrap">${fmtDate(dt)}</td>
                <td>
                  <div><b>${safe(vital)}</b></div>
                  ${remark ? `<div class="legacy-muted">${safe(remark)}</div>` : ``}
                </td>
                <td style="white-space:nowrap">
                  <span class="legacy-pill">${safe(res)}${uom ? ` ${safe(uom)}` : ""}</span>
                </td>
                <td style="white-space:nowrap">${safe(ref)}</td>
                <td style="white-space:nowrap">${fmtDate(sdate)}</td>
              </tr>
            `;
          })
          .join("");

        return `
          <div class="legacy-group ${isCollapsed ? "collapsed" : ""}" data-date="${safe(g.date)}">
            <div class="legacy-group-head">
              <div class="legacy-group-title">${safe(g.date)}</div>
              <div class="legacy-group-meta">
                <span>${__("{0} entries", [count])}</span>
                <span class="legacy-chevron">${frappe.utils.icon("chevron-down", "sm")}</span>
              </div>
            </div>

            <div class="legacy-card" style="${isCollapsed ? "display:none;" : ""}">
              <div class="legacy-table-wrap">
                <table class="legacy-table">
                  <thead>
                    <tr>
                      <th style="width:190px">${__("Date/Time")}</th>
                      <th>${__("Vital")}</th>
                      <th style="width:210px">${__("Result")}</th>
                      <th style="width:210px">${__("Service Ref")}</th>
                      <th style="width:190px">${__("Service Date")}</th>
                    </tr>
                  </thead>
                  <tbody>${body}</tbody>
                </table>
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    $content.html(html);
  }

  function applySearch(q) {
    q = (q || "").trim().toLowerCase();
    $root.find(".legacy-clear").toggle(!!q);

    if (!q) {
      state.filtered = [...state.rows];
      render();
      return;
    }

    state.filtered = state.rows.filter((r) => {
      const hay = [
        r.DateRecorded,
        r.ServiceDate,
        r.VitalStatistic,
        r.Result,
        r.VitalUOM,
        r.Remark,
        r.ServiceReference,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });

    render();
  }

  function clearSearch() {
    $root.find(".legacy-search").val("");
    $root.find(".legacy-clear").hide();
    state.filtered = [...state.rows];
    render();
  }

  async function load(refresh_cache = 0) {
    $root.find(".legacy-subtitle").text(encounter ? __("From Encounter: {0}", [encounter]) : "");

    $root.find(".legacy-patient").text(patient || "-");
    $root.find(".legacy-legacyid").text("-");
    $root.find(".legacy-lastdate").text("-");
    $root.find(".legacy-name").text("-");
    $root.find(".legacy-gender").text("-");
    $root.find(".legacy-dob").text("-");

    $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Loading...")}</div>`);

    const r = await frappe.call({
      method: "his.legacy.legacy_vitals.get_legacy_vitals",
      args: { patient, limit: 1200, refresh_cache },
      freeze: true,
      freeze_message: __("Fetching legacy vitals..."),
    });

    const data = r.message || {};
    if (!data.ok) {
      $root.find(".legacy-content").html(`<div class="legacy-empty">${safe(data.message || "Error")}</div>`);
      return;
    }

    const rows = data.rows || [];
    state.rows = rows;
    state.filtered = [...rows];

    $root.find(".legacy-legacyid").text(data.legacy_patient_number || "-");

    const first_dt = rows[0] ? (rows[0].DateRecorded || rows[0].ServiceDate) : "";
    $root.find(".legacy-lastdate").text(first_dt ? fmtDate(first_dt) : "-");

    const meta = data.patient_meta || {};
    $root.find(".legacy-name").text(meta.PatientName || "-");
    $root.find(".legacy-gender").text(meta.Gender || "-");
    $root.find(".legacy-dob").text(meta.BirthDate ? fmtDate(meta.BirthDate) : "-");

    applySearch($root.find(".legacy-search").val() || "");
  }

  // Events
  $root.on("input", ".legacy-search", (e) => applySearch(e.target.value));
  $root.on("click", ".legacy-clear", () => clearSearch());
  $root.on("click", ".legacy-refresh", () => {
    clearSearch();
    state.collapsed = {};
    load(1);
  });

  $root.on("click", ".legacy-group-head", function () {
    const $g = $(this).closest(".legacy-group");
    const date = $g.attr("data-date");
    state.collapsed[date] = !state.collapsed[date];
    render();
  });

  // Initial load
  if (!patient) {
    $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Missing patient parameter in URL.")}</div>`);
    return;
  }

  load(0);
};
