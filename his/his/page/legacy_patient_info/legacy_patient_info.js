frappe.pages["legacy-patient-info"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Legacy Patient Info"),
    single_column: true,
  });

  const state = {
    q: "",
    date_field: "LastVisited",
    date_from: "",
    date_to: "",
    page: 1,
    page_length: 50,
    sort_by: "LastVisited",
    sort_order: "DESC",
    total: 0,
  };

  const $body = $(page.body);
  $body.html(`
    <div class="legacy-filters" style="display:flex; gap:8px; flex-wrap:wrap; align-items:end;">
      <div>
        <label class="small text-muted">${__("Search")}</label>
        <input type="text" class="form-control legacy-q" style="min-width:320px"
          placeholder="PatientNumber / Phone / Name"/>
      </div>

      <div>
        <label class="small text-muted">${__("Date Field")}</label>
        <select class="form-control legacy-date-field">
          <option value="LastVisited">${__("Last Visited")}</option>
          <option value="RegistrationDate">${__("Registration Date")}</option>
        </select>
      </div>

      <div>
        <label class="small text-muted">${__("From")}</label>
        <input type="date" class="form-control legacy-from"/>
      </div>

      <div>
        <label class="small text-muted">${__("To")}</label>
        <input type="date" class="form-control legacy-to"/>
      </div>

      <div>
        <label class="small text-muted">${__("Sort By")}</label>
        <select class="form-control legacy-sort-by">
          <option value="LastVisited">${__("Last Visited")}</option>
          <option value="RegistrationDate">${__("Registration Date")}</option>
          <option value="PatientNumber">${__("Patient Number")}</option>
          <option value="PatientName">${__("Patient Name")}</option>
          <option value="PatientCellPhone">${__("Phone")}</option>
          <option value="Age">${__("Age")}</option>
        </select>
      </div>

      <div>
        <label class="small text-muted">${__("Order")}</label>
        <select class="form-control legacy-sort-order">
          <option value="DESC">${__("DESC")}</option>
          <option value="ASC">${__("ASC")}</option>
        </select>
      </div>

      <div>
        <label class="small text-muted">${__("Page Size")}</label>
        <select class="form-control legacy-page-length">
          <option value="25">25</option>
          <option value="50" selected>50</option>
          <option value="100">100</option>
          <option value="200">200</option>
        </select>
      </div>

      <div style="display:flex; gap:8px;">
        <button class="btn btn-primary legacy-search">${__("Search")}</button>
        <button class="btn btn-default legacy-reset">${__("Reset")}</button>
      </div>
    </div>

    <hr/>

    <div class="legacy-results"></div>

    <div class="legacy-pager" style="display:flex; align-items:center; justify-content:space-between; margin-top:10px;">
      <div class="text-muted legacy-page-info"></div>
      <div style="display:flex; gap:8px;">
        <button class="btn btn-default btn-sm legacy-prev">${__("Prev")}</button>
        <button class="btn btn-default btn-sm legacy-next">${__("Next")}</button>
      </div>
    </div>
  `);

  const $q = $body.find(".legacy-q");
  const $dateField = $body.find(".legacy-date-field");
  const $from = $body.find(".legacy-from");
  const $to = $body.find(".legacy-to");
  const $sortBy = $body.find(".legacy-sort-by");
  const $sortOrder = $body.find(".legacy-sort-order");
  const $pageLength = $body.find(".legacy-page-length");
  const $results = $body.find(".legacy-results");
  const $pageInfo = $body.find(".legacy-page-info");

  function render(rows) {
    if (!rows || !rows.length) {
      $results.html(`<p class="text-muted">${__("No results.")}</p>`);
      return;
    }

    $results.html(`
      <div class="table-responsive">
        <table class="table table-bordered table-hover">
          <thead>
            <tr>
              <th>${__("Patient Number")}</th>
              <th>${__("Patient Name")}</th>
              <th>${__("Phone")}</th>
              <th>${__("Gender")}</th>
              <th>${__("Age")}</th>
              <th>${__("Registration Date")}</th>
              <th>${__("Last Visited")}</th>
              <th style="width:140px">${__("Action")}</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(r => `
              <tr class="legacy-row" data-pn="${frappe.utils.escape_html(r.PatientNumber || "")}">
                <td><b>${frappe.utils.escape_html(r.PatientNumber || "")}</b></td>
                <td>${frappe.utils.escape_html(r.PatientName || "")}</td>
                <td>${frappe.utils.escape_html(r.PatientCellPhone || "")}</td>
                <td>${frappe.utils.escape_html(r.Gender || "")}</td>
                <td>${frappe.utils.escape_html((r.Age ?? "") + "")}</td>
                <td>${frappe.utils.escape_html(r.RegistrationDate || "")}</td>
                <td>${frappe.utils.escape_html(r.LastVisited || "")}</td>
                <td>
                  <button
                    class="btn btn-xs btn-primary legacy-open-history"
                    data-legacy="${frappe.utils.escape_html(r.PatientNumber || "")}">
                    ${__("History")}
                  </button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
      <p class="text-muted">${__("Click a row to copy Patient Number.")}</p>
    `);

    $results.find(".legacy-row").on("click", function () {
      const pn = $(this).data("pn");
      frappe.utils.copy_to_clipboard(pn);
      frappe.show_alert({ message: __("Copied: {0}", [pn]), indicator: "green" });
    });
    $results.find(".legacy-open-history").on("click", async function (e) {
      e.preventDefault();
      e.stopPropagation(); // don’t trigger row-copy

      const legacy_no = ($(this).data("legacy") || "").toString().trim();
      if (!legacy_no) return;

      try {
        frappe.dom.freeze(__("Opening history..."));

        const r = await frappe.call({
          method: "his.legacy.legacy_patient_info.resolve_patient_from_legacy",
          args: { legacy_patient_number: legacy_no },
        });

        const msg = r.message || {};
        if (!msg.ok) {
          frappe.msgprint({
            title: __("Patient not linked"),
            message: __(
              "Legacy patient <b>{0}</b> is not linked to a Patient record in this system.<br><br>" +
              "Tip: Create/Update Patient and set <b>legacy_patient_number</b> to <b>{0}</b>.",
              [frappe.utils.escape_html(legacy_no)]
            ),
            indicator: "orange",
          });
          return;
        }

        const url =
          `/app/legacy-history` +
          `?patient=${encodeURIComponent(msg.patient)}` +
          `&tab=vitals`;

        window.open(url, "_blank");
      } finally {
        frappe.dom.unfreeze();
      }
    });

  }

  function updatePager() {
    const totalPages = Math.max(1, Math.ceil((state.total || 0) / state.page_length));
    $pageInfo.text(
      __("Showing page {0} of {1} — Total {2}", [state.page, totalPages, state.total || 0])
    );

    $body.find(".legacy-prev").prop("disabled", state.page <= 1);
    $body.find(".legacy-next").prop("disabled", state.page >= totalPages);
  }

  async function load() {
    $results.html(`<p class="text-muted">${__("Loading...")}</p>`);

    const r = await frappe.call({
      method: "his.legacy.legacy_patient_info.search_legacy_patients_paged",
      args: {
        q: state.q,
        date_field: state.date_field,
        date_from: state.date_from || null,
        date_to: state.date_to || null,
        page: state.page,
        page_length: state.page_length,
        sort_by: state.sort_by,
        sort_order: state.sort_order,
      },
    });

    const msg = r.message || {};
    state.total = msg.total || 0;

    render(msg.rows || []);
    updatePager();
  }

  function syncStateFromUI() {
    state.q = ($q.val() || "").trim();
    state.date_field = $dateField.val();
    state.date_from = $from.val();
    state.date_to = $to.val();
    state.sort_by = $sortBy.val();
    state.sort_order = $sortOrder.val();
    state.page_length = parseInt($pageLength.val(), 10) || 50;
  }

  $body.find(".legacy-search").on("click", () => {
    syncStateFromUI();
    state.page = 1;
    load();
  });

  $body.find(".legacy-reset").on("click", () => {
    $q.val("");
    $dateField.val("LastVisited");
    $from.val("");
    $to.val("");
    $sortBy.val("LastVisited");
    $sortOrder.val("DESC");
    $pageLength.val("50");
    syncStateFromUI();
    state.page = 1;
    load();
  });

  $body.find(".legacy-prev").on("click", () => {
    if (state.page > 1) {
      state.page -= 1;
      load();
    }
  });

  $body.find(".legacy-next").on("click", () => {
    const totalPages = Math.max(1, Math.ceil((state.total || 0) / state.page_length));
    if (state.page < totalPages) {
      state.page += 1;
      load();
    }
  });

  // Enter triggers search
  $q.on("keydown", (e) => {
    if (e.key === "Enter") {
      syncStateFromUI();
      state.page = 1;
      load();
    }
  });

  // initial load: last visited desc, first page
  syncStateFromUI();
  load();
};
