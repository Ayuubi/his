frappe.pages["legacy-history"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Legacy Patient History"),
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
            <input class="form-control legacy-search" placeholder="${__("Search...")}" />
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

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Encounter")}</div>
            <div class="legacy-meta-value legacy-encounter"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Last Vitals")}</div>
            <div class="legacy-meta-value legacy-last-vitals"></div>
          </div>

          <div class="legacy-meta-item">
            <div class="legacy-meta-label">${__("Last Lab")}</div>
            <div class="legacy-meta-value legacy-last-labs"></div>
          </div>
        </div>
      </div>

      <ul class="nav nav-tabs legacy-tabs">
        <li class="active"><a data-tab="vitals" href="#">${__("Vitals")} <span class="badge badge-light legacy-badge-vitals">0</span></a></li>
        <li><a data-tab="labs" href="#">${__("Lab Results")} <span class="badge badge-light legacy-badge-labs">0</span></a></li>
		<li><a data-tab="diagnostics" href="#">${__("Diagnostics")} <span class="badge badge-light legacy-badge-diagnostics">0</span></a></li>
		<li><a data-tab="medications" href="#">${__("Medications")} <span class="badge badge-light legacy-badge-medications">0</span></a></li>

      </ul>

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
        margin-bottom: 12px;
        background: var(--card-bg, var(--bg-color, #fff));
      }
      .legacy-meta-grid {
        display:grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 12px;
      }
      @media (max-width: 1000px) {
        .legacy-meta-grid { grid-template-columns: 1fr 1fr; }
      }
      @media (max-width: 640px) {
        .legacy-meta-grid { grid-template-columns: 1fr; }
      }
      .legacy-meta-label { font-size: 12px; color: var(--text-muted, #777); }
      .legacy-meta-value { font-weight: 600; margin-top: 2px; }

      .legacy-tabs { margin-bottom: 12px; }
      .legacy-tabs li.disabled { opacity: .55; pointer-events:none; }

      .legacy-empty {
        padding: 18px;
        border: 1px dashed var(--border-color, #ddd);
        border-radius: 12px;
        background: var(--control-bg, #fcfcfc);
      }

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

      .legacy-flag {
        display:inline-block;
        padding: 1px 8px;
        border-radius: 999px;
        font-size: 12px;
        border: 1px solid var(--border-color, #e6e6e6);
        background: var(--control-bg, #f7f7f7);
        margin-left: 8px;
      }
      .legacy-flag.high { border-color: rgba(255,0,0,.25); }
      .legacy-flag.low  { border-color: rgba(0,0,255,.25); }
    </style>
  `);

  // -------------------------
  // Params + state
  // -------------------------
  const params = new URLSearchParams(window.location.search);
  const patient = params.get("patient");
  const encounter = params.get("encounter");
  const defaultTab = (params.get("tab") || "vitals").toLowerCase();

  const state = {
    activeTab: "vitals",
    vitals: { rows: [], filtered: [], collapsed: {}, loaded: false, cached: 0 },
    labs:   { rows: [], filtered: [], collapsed: {}, loaded: false, cached: 0 },
	diagnostics: { rows: [], filtered: [], collapsed: {}, loaded: false, cached: 0 },
	medications: { rows: [], filtered: [], collapsed: {}, loaded: false, cached: 0 },
  };

  function safe(x) {
    return frappe.utils.escape_html(x || "");
  }
  function fmtDate(dt) {
    if (!dt) return "-";
    return frappe.datetime.str_to_user(dt);
  }

  function setStats(text) {
    $root.find(".legacy-stats").text(text || "");
  }

  function setSearchPlaceholder() {
	const ph =
		state.activeTab === "vitals"
		? __("Search vital / result / UOM...")
		: state.activeTab === "labs"
		? __("Search test / parameter / result...")
		: __("Search medication / dosage / frequency / doctor...");
	$root.find(".legacy-search").attr("placeholder", ph);
	}



  function getActiveBucket() {
    return state[state.activeTab];
  }

  function groupByDate(rows, dtGetter) {
    const map = {};
    for (const r of rows) {
      const dt = dtGetter(r) || "";
      const d = dt.slice(0, 10);
      if (!d) continue;
      map[d] = map[d] || [];
      map[d].push(r);
    }
    return Object.keys(map)
      .sort()
      .reverse()
      .map((k) => ({ date: k, rows: map[k] }));
  }

  // -------------------------
  // Labs flag helpers (reuse your logic)
  // -------------------------
  function parseReference(ref) {
    ref = (ref || "").toString().trim();
    if (!ref || ref === "-----") return null;

    const lt = ref.match(/^\s*<\s*([0-9]+(?:\.[0-9]+)?)/);
    if (lt) return { lt: parseFloat(lt[1]) };

    const gt = ref.match(/^\s*>\s*([0-9]+(?:\.[0-9]+)?)/);
    if (gt) return { gt: parseFloat(gt[1]) };

    const range = ref.match(/([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)/);
    if (range) return { min: parseFloat(range[1]), max: parseFloat(range[2]) };

    return null;
  }

  function parseResultNumber(val) {
    val = (val || "").toString().trim();
    const m = val.match(/-?\d+(?:\.\d+)?/);
    if (!m) return null;
    const n = parseFloat(m[0]);
    return Number.isFinite(n) ? n : null;
  }

  function getFlag(resultVal, refVal) {
    const n = parseResultNumber(resultVal);
    const ref = parseReference(refVal);
    if (n == null || !ref) return null;

    if (ref.min != null && ref.max != null) {
      if (n < ref.min) return { type: "low", label: __("L") };
      if (n > ref.max) return { type: "high", label: __("H") };
      return null;
    }
    if (ref.lt != null) {
      if (n >= ref.lt) return { type: "high", label: __("H") };
      return null;
    }
    if (ref.gt != null) {
      if (n <= ref.gt) return { type: "low", label: __("L") };
      return null;
    }
    return null;
  }

  // -------------------------
  // Renderers
  // -------------------------
  function renderVitals() {
    const bucket = state.vitals;
    const rows = bucket.filtered || [];
    const $content = $root.find(".legacy-content");

    const total = bucket.rows.length || 0;
    const shown = rows.length || 0;
    const q = ($root.find(".legacy-search").val() || "").trim();
    setStats(total ? __("Vitals: showing {0} of {1}", [shown, total]) + (q ? ` · ${__("Filter")}: ${q}` : "") : __("No vitals"));

    if (!rows.length) {
      $content.html(`<div class="legacy-empty">${__("No legacy vitals found.")}</div>`);
      return;
    }

    const groups = groupByDate(rows, (r) => r.DateRecorded || r.ServiceDate || "");

    const html = groups
      .map((g) => {
        const isCollapsed = !!bucket.collapsed[g.date];
        const body = g.rows
          .map((r) => {
            const dt = r.DateRecorded || r.ServiceDate || "";
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
                <span>${__("{0} entries", [g.rows.length])}</span>
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

  function renderLabs() {
    const bucket = state.labs;
    const rows = bucket.filtered || [];
    const $content = $root.find(".legacy-content");

    const total = bucket.rows.length || 0;
    const shown = rows.length || 0;
    const q = ($root.find(".legacy-search").val() || "").trim();
    setStats(total ? __("Labs: showing {0} of {1}", [shown, total]) + (q ? ` · ${__("Filter")}: ${q}` : "") : __("No labs"));

    if (!rows.length) {
      $content.html(`<div class="legacy-empty">${__("No legacy lab results found.")}</div>`);
      return;
    }

    const groups = groupByDate(rows, (r) => r.DatePerformed || "");

    const html = groups
      .map((g) => {
        const isCollapsed = !!bucket.collapsed[g.date];

        const body = g.rows
          .map((r) => {
            const flag = getFlag(r.LabTestResults, r.Reference);
            const flagHtml = flag
              ? `<span class="legacy-flag ${flag.type}" title="${__("Out of reference")}">${safe(flag.label)}</span>`
              : "";

            return `
              <tr>
                <td style="white-space:nowrap">${fmtDate(r.DatePerformed)}</td>
                <td>
                  <div><b>${safe(r.ProcedureID)}</b></div>
                  <div class="legacy-muted">${safe(r.ParameterID)}</div>
                </td>
                <td>${safe(r.LabTestResults)} ${flagHtml}</td>
                <td>${safe(r.Reference)}</td>
                <td>${safe(r.DoctorName)}</td>
                <td><span class="legacy-pill">${safe(r.PatientStatus)}</span></td>
              </tr>
            `;
          })
          .join("");

        return `
          <div class="legacy-group ${isCollapsed ? "collapsed" : ""}" data-date="${safe(g.date)}">
            <div class="legacy-group-head">
              <div class="legacy-group-title">${safe(g.date)}</div>
              <div class="legacy-group-meta">
                <span>${__("{0} tests", [g.rows.length])}</span>
                <span class="legacy-chevron">${frappe.utils.icon("chevron-down", "sm")}</span>
              </div>
            </div>

            <div class="legacy-card" style="${isCollapsed ? "display:none;" : ""}">
              <div class="legacy-table-wrap">
                <table class="legacy-table">
                  <thead>
                    <tr>
                      <th style="width:190px">${__("Date/Time")}</th>
                      <th>${__("Test")}</th>
                      <th style="width:190px">${__("Result")}</th>
                      <th style="width:190px">${__("Reference")}</th>
                      <th style="width:260px">${__("Doctor")}</th>
                      <th style="width:140px">${__("Status")}</th>
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


  function renderMedications() {
  const bucket = state.medications;
  const rows = bucket.filtered || [];
  const $content = $root.find(".legacy-content");

  const total = bucket.rows.length || 0;
  const shown = rows.length || 0;
  const q = ($root.find(".legacy-search").val() || "").trim();
  setStats(
    total
      ? __("Medications: showing {0} of {1}", [shown, total]) + (q ? ` · ${__("Filter")}: ${q}` : "")
      : __("No medications")
  );

  if (!rows.length) {
    $content.html(`<div class="legacy-empty">${__("No legacy medications found.")}</div>`);
    return;
  }

  const groups = groupByDate(rows, (r) => r.ServiceDate || "");

  const html = groups
    .map((g) => {
      const isCollapsed = !!bucket.collapsed[g.date];

      const body = g.rows
        .map((r) => {
          const dt = r.ServiceDate || "";
          const item = r.ItemName || r.ItemID || "";
          const dose = r.Dosage || "";
          const freq = r.Frequency || "";
          const route = r.RouteID || "";
          const days = r.NoOfDays || "";
          const qty = r.Quantity || "";
          const uom = r.ItemUOM || "";
          const doc = r.DoctorName || "";
          const ref = r.ServiceReference || "";
          const instr = r.InstrMsg || "";

          return `
            <tr>
              <td style="white-space:nowrap">${fmtDate(dt)}</td>
              <td>
                <div><b>${safe(item)}</b></div>
                ${ref ? `<div class="legacy-muted">${__("Ref")}: ${safe(ref)}</div>` : ``}
                ${instr ? `<div class="legacy-muted">${safe(instr)}</div>` : ``}
              </td>
              <td style="white-space:nowrap">${safe(dose)}</td>
              <td style="white-space:nowrap">${safe(freq)}</td>
              <td style="white-space:nowrap">${safe(route)}</td>
              <td style="white-space:nowrap">${safe(days)}</td>
              <td style="white-space:nowrap">${safe(qty)} ${safe(uom)}</td>
              <td>${safe(doc)}</td>
            </tr>
          `;
        })
        .join("");

      return `
        <div class="legacy-group ${isCollapsed ? "collapsed" : ""}" data-date="${safe(g.date)}">
          <div class="legacy-group-head">
            <div class="legacy-group-title">${safe(g.date)}</div>
            <div class="legacy-group-meta">
              <span>${__("{0} items", [g.rows.length])}</span>
              <span class="legacy-chevron">${frappe.utils.icon("chevron-down", "sm")}</span>
            </div>
          </div>

          <div class="legacy-card" style="${isCollapsed ? "display:none;" : ""}">
            <div class="legacy-table-wrap">
              <table class="legacy-table">
                <thead>
                  <tr>
                    <th style="width:190px">${__("Date")}</th>
                    <th>${__("Medication")}</th>
                    <th style="width:160px">${__("Dosage")}</th>
                    <th style="width:150px">${__("Frequency")}</th>
                    <th style="width:120px">${__("Route")}</th>
                    <th style="width:110px">${__("Days")}</th>
                    <th style="width:150px">${__("Qty")}</th>
                    <th style="width:220px">${__("Doctor")}</th>
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


  function renderDiagnostics() {
  const bucket = state.diagnostics;
  const rows = bucket.filtered || [];
  const $content = $root.find(".legacy-content");

  const total = bucket.rows.length || 0;
  const shown = rows.length || 0;
  const q = ($root.find(".legacy-search").val() || "").trim();
  setStats(
    total
      ? __("Diagnostics: showing {0} of {1}", [shown, total]) + (q ? ` · ${__("Filter")}: ${q}` : "")
      : __("No diagnostics")
  );

  if (!rows.length) {
    $content.html(`<div class="legacy-empty">${__("No legacy diagnostics found.")}</div>`);
    return;
  }

  const groups = groupByDate(rows, (r) => r.DateTimeIn || r.ServiceDate || "");

  const html = groups
    .map((g) => {
      const isCollapsed = !!bucket.collapsed[g.date];

      const body = g.rows
        .map((r) => {
          const dt = r.DateTimeIn || r.ServiceDate || "";
          const doctor = r.DoctorName || r.DoctorID || "";
          const type = r.ConsultDescription || "";
          const diag = r.Diagnosis || "";
          const cc = r.ChiefComplaint || "";
          const notes = r.ClinicalNotes || r.ClinicalHpi || "";
          const preview = (diag || notes || "").toString().trim();

          return `
            <tr>
              <td style="white-space:nowrap">${fmtDate(dt)}</td>
              <td>
                <div><b>${safe(doctor)}</b></div>
                ${type ? `<div class="legacy-muted">${safe(type)}</div>` : ``}
              </td>
              <td>
                <div>${safe(preview.slice(0, 200))}${preview.length > 200 ? "..." : ""}</div>
                ${r.DiagnosisCategory ? `<div class="legacy-muted">${__("Category")}: ${safe(r.DiagnosisCategory)}</div>` : ``}
              </td>
              <td>
                <div>${safe(cc)}</div>
              </td>
              <td style="white-space:nowrap">
                <button class="btn btn-xs btn-primary legacy-dx-view" data-row='${safe(JSON.stringify(r))}'>
                  ${__("View")}
                </button>
              </td>
            </tr>
          `;
        })
        .join("");

      return `
        <div class="legacy-group ${isCollapsed ? "collapsed" : ""}" data-date="${safe(g.date)}">
          <div class="legacy-group-head">
            <div class="legacy-group-title">${safe(g.date)}</div>
            <div class="legacy-group-meta">
              <span>${__("{0} entries", [g.rows.length])}</span>
              <span class="legacy-chevron">${frappe.utils.icon("chevron-down", "sm")}</span>
            </div>
          </div>

          <div class="legacy-card" style="${isCollapsed ? "display:none;" : ""}">
            <div class="legacy-table-wrap">
              <table class="legacy-table">
                <thead>
                  <tr>
                    <th style="width:190px">${__("Date/Time")}</th>
                    <th style="width:260px">${__("Doctor / Type")}</th>
                    <th>${__("Diagnosis / Notes")}</th>
                    <th style="width:260px">${__("Chief Complaint")}</th>
                    <th style="width:110px">${__("Action")}</th>
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


  function renderActive() {
    if (state.activeTab === "vitals") return renderVitals();
    if (state.activeTab === "labs") return renderLabs();
	if (state.activeTab === "diagnostics") return renderDiagnostics();
	if (state.activeTab === "medications") return renderMedications();
  }

  // -------------------------
  // Search apply
  // -------------------------
  function applySearch(q) {
    q = (q || "").trim().toLowerCase();
    $root.find(".legacy-clear").toggle(!!q);

    const bucket = getActiveBucket();

    if (!q) {
      bucket.filtered = [...bucket.rows];
      renderActive();
      return;
    }

    bucket.filtered = bucket.rows.filter((r) => {
		const hay =
			state.activeTab === "vitals"
			? [
				r.DateRecorded, r.ServiceDate, r.VitalStatistic, r.Result,
				r.VitalUOM, r.Remark, r.ServiceReference,
				].join(" ")
			: state.activeTab === "labs"
			? [
				r.DatePerformed, r.ProcedureID, r.ParameterID, r.LabTestResults,
				r.Reference, r.DoctorName, r.PatientStatus,
				].join(" ")
			: state.activeTab === "diagnostics"
			? [
				r.ServiceDate, r.DateTimeIn, r.DateTimeOut, r.ServiceReference,
				r.ConsultDescription, r.DoctorID, r.DoctorName, r.ChiefComplaint,
				r.DiagnosisCategory, r.Diagnosis, r.ClinicalHpi, r.ClinicalNotes,
				r.Investigation, r.InvestigationRemarks, r.Treatment, r.TreatmentRemarks,
				r.Medication, r.Management,
				].join(" ")
			: [
				r.ServiceReference, r.ServiceDate, r.PatientNumber, r.PatientName,
				r.DoctorName, r.ItemName, r.ItemID, r.Dosage, r.NoOfDays,
				r.Quantity, r.ItemUOM, r.Frequency, r.RouteID, r.InstrMsg,
				].join(" ");

		return (hay || "").toLowerCase().includes(q);
		});


    renderActive();
  }



  function clearSearch() {
    $root.find(".legacy-search").val("");
    $root.find(".legacy-clear").hide();
    const bucket = getActiveBucket();
    bucket.filtered = [...bucket.rows];
    renderActive();
  }

  // -------------------------
  // Loaders
  // -------------------------
  async function loadMeta() {
    $root.find(".legacy-subtitle").text(encounter ? __("From Encounter: {0}", [encounter]) : "");
    $root.find(".legacy-patient").text(patient || "-");
    $root.find(".legacy-encounter").text(encounter || "-");
    $root.find(".legacy-legacyid").text("-");
    $root.find(".legacy-name").text("-");
    $root.find(".legacy-gender").text("-");
    $root.find(".legacy-dob").text("-");
    $root.find(".legacy-last-vitals").text("-");
    $root.find(".legacy-last-labs").text("-");

    const r = await frappe.call({
      method: "his.legacy.legacy_meta.get_legacy_meta",
      args: { patient },
    });

    const data = r.message || {};
    if (!data.ok) {
      $root.find(".legacy-content").html(`<div class="legacy-empty">${safe(data.message || "Error")}</div>`);
      return false;
    }

    $root.find(".legacy-legacyid").text(data.legacy_patient_number || "-");

    const meta = data.patient_meta || {};
    $root.find(".legacy-name").text(meta.PatientName || "-");
    $root.find(".legacy-gender").text(meta.Gender || "-");
    $root.find(".legacy-dob").text(meta.BirthDate ? fmtDate(meta.BirthDate) : "-");
    return true;
  }

  async function loadVitals(refresh_cache = 0) {
    const bucket = state.vitals;
    $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Loading vitals...")}</div>`);

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

    bucket.rows = data.rows || [];
    bucket.filtered = [...bucket.rows];
    bucket.loaded = true;
    bucket.cached = data.cached ? 1 : 0;

    $root.find(".legacy-badge-vitals").text(bucket.rows.length || 0);

    const first_dt = bucket.rows[0] ? (bucket.rows[0].DateRecorded || bucket.rows[0].ServiceDate) : "";
    $root.find(".legacy-last-vitals").text(first_dt ? fmtDate(first_dt) : "-");

    applySearch($root.find(".legacy-search").val() || "");
  }

  async function loadLabs(refresh_cache = 0) {
    const bucket = state.labs;
    $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Loading lab results...")}</div>`);

    const r = await frappe.call({
      method: "his.legacy.legacy_labs.get_legacy_labs",
      args: { patient, limit: 800, refresh_cache },
      freeze: true,
      freeze_message: __("Fetching legacy lab results..."),
    });

    const data = r.message || {};
    if (!data.ok) {
      $root.find(".legacy-content").html(`<div class="legacy-empty">${safe(data.message || "Error")}</div>`);
      return;
    }

    bucket.rows = data.rows || [];
    bucket.filtered = [...bucket.rows];
    bucket.loaded = true;
    bucket.cached = data.cached ? 1 : 0;

    $root.find(".legacy-badge-labs").text(bucket.rows.length || 0);

    const first_dt = bucket.rows[0]?.DatePerformed || "";
    $root.find(".legacy-last-labs").text(first_dt ? fmtDate(first_dt) : "-");

    applySearch($root.find(".legacy-search").val() || "");
  }

  async function loadMedications(refresh_cache = 0) {
  const bucket = state.medications;
  $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Loading medications...")}</div>`);

  const r = await frappe.call({
    method: "his.legacy.legacy_medications.get_legacy_medications",
    args: { patient, limit: 800, refresh_cache },
    freeze: true,
    freeze_message: __("Fetching legacy medications..."),
  });

  const data = r.message || {};
  if (!data.ok) {
    $root.find(".legacy-content").html(`<div class="legacy-empty">${safe(data.message || "Error")}</div>`);
    return;
  }

  bucket.rows = data.rows || [];
  bucket.filtered = [...bucket.rows];
  bucket.loaded = true;
  bucket.cached = data.cached ? 1 : 0;

  $root.find(".legacy-badge-medications").text(bucket.rows.length || 0);

  applySearch($root.find(".legacy-search").val() || "");
}


  async function loadDiagnostics(refresh_cache = 0) {
  const bucket = state.diagnostics;
  $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Loading diagnostics...")}</div>`);

  const r = await frappe.call({
    method: "his.legacy.legacy_diagnostics.get_legacy_diagnostics",
    args: { patient, limit: 600, refresh_cache },
    freeze: true,
    freeze_message: __("Fetching legacy diagnostics..."),
  });

  const data = r.message || {};
  if (!data.ok) {
    $root.find(".legacy-content").html(`<div class="legacy-empty">${safe(data.message || "Error")}</div>`);
    return;
  }

  bucket.rows = data.rows || [];
  bucket.filtered = [...bucket.rows];
  bucket.loaded = true;
  bucket.cached = data.cached ? 1 : 0;

  $root.find(".legacy-badge-diagnostics").text(bucket.rows.length || 0);

  // Optional: if you add a meta field later, you can set "Last Diagnostics" here

  applySearch($root.find(".legacy-search").val() || "");
}


  async function ensureLoaded(tab) {
    if (tab === "vitals" && !state.vitals.loaded) return loadVitals(0);
    if (tab === "labs" && !state.labs.loaded) return loadLabs(0);
	if (tab === "diagnostics" && !state.diagnostics.loaded) return loadDiagnostics(0);
	if (tab === "medications" && !state.medications.loaded) return loadMedications(0);
  }

  // -------------------------
  // Tab switching
  // -------------------------
  async function activateTab(tab) {
    tab = (tab || "vitals").toLowerCase();
    if (!["vitals", "labs", "diagnostics", "medications"].includes(tab)) tab = "vitals";

    state.activeTab = tab;
    setSearchPlaceholder();

    // ui
    $root.find(".legacy-tabs li").removeClass("active");
    $root.find(`.legacy-tabs a[data-tab="${tab}"]`).closest("li").addClass("active");

    await ensureLoaded(tab);

    // keep search applied
    applySearch($root.find(".legacy-search").val() || "");
  }

  // -------------------------
  // Events
  // -------------------------
  $root.on("click", ".legacy-tabs a[data-tab]", function (e) {
    e.preventDefault();
    const tab = $(this).attr("data-tab");
    clearSearch(); // optional: remove if you prefer to keep the query when switching
    activateTab(tab);
  });

  $root.on("input", ".legacy-search", (e) => applySearch(e.target.value));

  $root.on("click", ".legacy-clear", () => clearSearch());

  $root.on("click", ".legacy-refresh", async () => {
    clearSearch();
    const bucket = getActiveBucket();
    bucket.collapsed = {};

    if (state.activeTab === "vitals") return loadVitals(1);
    if (state.activeTab === "labs") return loadLabs(1);
	if (state.activeTab === "diagnostics") return loadDiagnostics(1);
	if (state.activeTab === "medications") return loadMedications(1);

  });
  

  $root.on("click", ".legacy-group-head", function () {
    const bucket = getActiveBucket();
    const $g = $(this).closest(".legacy-group");
    const date = $g.attr("data-date");
    bucket.collapsed[date] = !bucket.collapsed[date];
    renderActive();
  });

  $root.on("click", ".legacy-dx-view", function () {
  let row = {};
  try {
    row = JSON.parse($(this).attr("data-row") || "{}");
  } catch (e) {}

  const fmt = (v) => safe((v || "").toString()).replace(/\n/g, "<br>");

  const d = new frappe.ui.Dialog({
    title: __("Legacy Diagnostics"),
    size: "large",
    fields: [{ fieldtype: "HTML", fieldname: "body" }],
  });

  d.fields_dict.body.$wrapper.html(`
    <div style="line-height:1.6">
      <div><b>${__("Date")}:</b> ${safe(row.DateTimeIn || row.ServiceDate || "")}</div>
      <div><b>${__("Doctor")}:</b> ${safe(row.DoctorName || row.DoctorID || "")}</div>
      <div><b>${__("Type")}:</b> ${safe(row.ConsultDescription || "")}</div>
      <hr>
      <div><b>${__("Diagnosis Category")}:</b> ${safe(row.DiagnosisCategory || "")}</div>
      <div class="mt-2"><b>${__("Diagnosis")}:</b><div class="mt-1">${fmt(row.Diagnosis)}</div></div>
      <hr>
      <div>
        <b>${__("Chief Complaint")}:</b>
        <div class="mt-1">${fmt(row.ChiefComplaint)}</div>
      </div>
      <hr>
      <div><b>${__("HPI")}:</b><div class="mt-1">${fmt(row.ClinicalHpi)}</div></div>
      <div class="mt-2"><b>${__("Clinical Notes")}:</b><div class="mt-1">${fmt(row.ClinicalNotes)}</div></div>
      <hr>
      <div><b>${__("Investigation")}:</b><div class="mt-1">${fmt(row.Investigation)}</div></div>
      <div class="mt-2"><b>${__("Investigation Remarks")}:</b><div class="mt-1">${fmt(row.InvestigationRemarks)}</div></div>
      <hr>
      <div><b>${__("Treatment")}:</b><div class="mt-1">${fmt(row.Treatment)}</div></div>
      <div class="mt-2"><b>${__("Treatment Remarks")}:</b><div class="mt-1">${fmt(row.TreatmentRemarks)}</div></div>
      <hr>
      <div><b>${__("Medication")}:</b><div class="mt-1">${fmt(row.Medication)}</div></div>
      <div class="mt-2"><b>${__("Management")}:</b><div class="mt-1">${fmt(row.Management)}</div></div>
    </div>
  `);

  d.show();
});


  // -------------------------
  // Init
  // -------------------------
  if (!patient) {
    $root.find(".legacy-content").html(`<div class="legacy-empty">${__("Missing patient parameter in URL.")}</div>`);
    return;
  }

  (async () => {
    const ok = await loadMeta();
    if (!ok) return;

    // set initial tab
    setSearchPlaceholder();
    await activateTab(defaultTab);
  })();
};
