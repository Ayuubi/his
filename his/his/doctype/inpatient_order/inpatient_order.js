// // Copyright (c) 2023, Rasiin Tech and contributors
// // For license information, please see license.txt

frappe.ui.form.on('Inpatient Order', {
    refresh(frm){
 
        frm.set_query('drug_code', 'drug_prescription', function() {
            return {
                // query: "his.api.dp_drug_pr_link_query.my_custom_query",
                filters: {
                    "item_group": "drug"
                }
                
            };
        })

        frm.set_query('service', 'services_prescription', function() {
            return {
                // query: "his.api.dp_drug_pr_link_query.my_custom_query",
                filters: {
                    "item_group": ['!=', 'drug']
                }
                
            };
        })
    },
    select_lab_tests: function(frm){
        select_lab_tests(frm)
    },
    new_select_lab_test: function(frm){
        open_selector_dialog(frm, get_lab_config());
    },

    select_imaging: function(frm){
        // alert("ok")
        select_imaging(frm)
    },


    
    
    })

function open_selector_dialog(frm, cfg) {
  // Ensure table field exists (prevents ".options" crash)
  const table_df = frm.meta.fields.find(
    (f) => f.fieldtype === "Table" && f.fieldname === cfg.target_childtable
  );
  if (!table_df) {
    frappe.msgprint({
      title: __("Configuration error"),
      message: __(
        "Child table field '{0}' not found on Patient Encounter. Check Customize Form fieldname.",
        [cfg.target_childtable]
      ),
      indicator: "red",
    });
    return;
  }

  // Existing rows (avoid duplicates)
  const existing = new Set(
    (frm.doc[cfg.target_childtable] || [])
      .map((r) => (r[cfg.target_field] || "").trim())
      .filter(Boolean)
  );

  // Selected starts with existing
  const selected = new Set([...existing]);

  // Track open groups (all collapsed initially)
  const open_groups = new Set();

  const d = new frappe.ui.Dialog({
    title: cfg.title,
    size: "extra-large",
    fields: [
      {
        fieldtype: "Data",
        fieldname: "q",
        label: __("Search"),
        placeholder: __("Type to filter..."),
        onchange() {
          render();
        },
      },
      { fieldtype: "HTML", fieldname: "body" },
    ],
    primary_action_label: __("Add Selected"),
    primary_action() {
      let added = 0;

      for (const name of selected) {
        if (!existing.has(name)) {
          const row = frm.add_child(cfg.target_childtable);
          row[cfg.target_field] = name;
          added += 1;
        }
      }

      frm.refresh_field(cfg.target_childtable);

      frappe.show_alert(
        {
          message: __("Added {0} item(s)", [added]),
          indicator: "green",
        },
        3
      );

      d.hide();
    },
  });

  const css = `
    <style>
      .sel-accordion .card { border: 1px solid #ddd; margin-bottom: 8px; border-radius: 6px; overflow: hidden; }
      .sel-accordion .card-header { background:#f7f7f7; padding:10px 12px; cursor:pointer; user-select:none; display:flex; align-items:center; justify-content:space-between; }
      .sel-accordion .card-header h5 { margin:0; font-size:14px; font-weight:700; }
      .sel-accordion .card-body { padding: 10px 12px; display:none; }
      .sel-accordion .card-body.open { display:block; }

      /* ✅ column-first layout */
      .sel-grid { display:flex; gap: 10px; }
      .sel-col { flex: 1; display:flex; flex-direction:column; gap: 6px; min-width: 0; }

      @media (max-width: 1200px){
        .sel-grid { flex-wrap: wrap; }
        .sel-col { flex: 0 0 calc(33.333% - 10px); }
      }
      @media (max-width: 900px){
        .sel-col { flex: 0 0 calc(50% - 10px); }
      }
      @media (max-width: 600px){
        .sel-col { flex: 0 0 100%; }
      }

      .sel-item { display:flex; align-items:center; gap:8px; padding:6px 8px; border:1px solid #eee; border-radius:6px; }
      .sel-item:hover { background:#fafafa; }
      .sel-item label { margin:0; cursor:pointer; font-size: 13px; }
      .sel-tools { display:flex; gap:8px; align-items:center; }
      .sel-mini { font-size:12px; color:#666; }
      .sel-link { color:#1a73e8; cursor:pointer; font-size:12px; }
    </style>
  `;

  let all_rows = [];

  frappe.db
    .get_list(cfg.source_doctype, {
      fields: cfg.source_fields,
      filters: cfg.source_filters || {},
      limit: 5000,
      order_by: cfg.source_order_by || "modified desc",
    })
    .then((rows) => {
      all_rows = (rows || []).filter((r) => cfg.item_label(r));
      render(); // all collapsed initially
      d.show();
      d.$wrapper.find(".modal-dialog").css({ "max-width": "98%", width: "98%" });
    });

  function render() {
    const q = (d.get_value("q") || "").trim().toLowerCase();

    const filtered = !q
      ? all_rows
      : all_rows.filter((r) => cfg.item_label(r).toLowerCase().includes(q));

    // Group
    const groups = {};
    for (const r of filtered) {
      const key = (cfg.group_key(r) || "OTHERS").trim();
      (groups[key] = groups[key] || []).push(r);
    }

    const keys = Object.keys(groups).sort((a, b) => a.localeCompare(b));
    let html = css + `<div class="sel-accordion">`;

    if (!keys.length) {
      html += `<div class="text-muted" style="padding:10px;">${__("No items found")}</div>`;
    }

    keys.forEach((key) => {
      const items = groups[key] || [];
      const open = open_groups.has(key);

      const checkedCount = items.reduce(
        (acc, r) => acc + (selected.has(cfg.item_label(r)) ? 1 : 0),
        0
      );

      html += `
        <div class="card" data-group="${frappe.utils.escape_html(key)}">
          <div class="card-header" data-action="toggle">
            <h5>${frappe.utils.escape_html(key)} <span class="sel-mini">(${checkedCount}/${items.length})</span></h5>
            <div class="sel-tools">
              <span class="sel-link" data-action="select-all">${__("Select all")}</span>
              <span class="sel-link" data-action="clear">${__("Clear")}</span>
              <span class="sel-mini">${open ? "▾" : "▸"}</span>
            </div>
          </div>
          <div class="card-body ${open ? "open" : ""}">
      `;

      // ✅ Sort alphabetically then split column-first
      const sorted_items = [...items].sort((a, b) =>
        cfg.item_label(a).localeCompare(cfg.item_label(b))
      );

      const COLS = 4;
      const perCol = Math.ceil(sorted_items.length / COLS);
      const columns = Array.from({ length: COLS }, (_, i) =>
        sorted_items.slice(i * perCol, (i + 1) * perCol)
      );

      html += `<div class="sel-grid">`;

      columns.forEach((colItems, colIndex) => {
        html += `<div class="sel-col" data-col="${colIndex}">`;

        colItems.forEach((r) => {
          const name = cfg.item_label(r);
          const safeId = frappe.utils
            .escape_html(`${key}_${name}`)
            .replace(/\s+/g, "_");
          const isChecked = selected.has(name) ? "checked" : "";

          html += `
            <div class="sel-item">
              <input type="checkbox" class="sel-check" id="${safeId}" data-item="${frappe.utils.escape_html(name)}" ${isChecked}/>
              <label for="${safeId}">${frappe.utils.escape_html(name)}</label>
            </div>
          `;
        });

        html += `</div>`;
      });

      html += `</div>`; // sel-grid
      html += `</div></div>`; // card-body + card
    });

    html += `</div>`; // sel-accordion

    d.fields_dict.body.$wrapper.html(html);
    bind_events();
  }

  function bind_events() {
    const $wrap = d.fields_dict.body.$wrapper;

    // Toggle only when clicking header (not select/clear)
    $wrap.find('[data-action="toggle"]').off("click").on("click", function (e) {
      if ($(e.target).closest('[data-action="select-all"], [data-action="clear"]').length) return;

      const $card = $(this).closest(".card");
      const key = ($card.attr("data-group") || "").trim();
      const $body = $card.find(".card-body");
      const nowOpen = !$body.hasClass("open");

      $body.toggleClass("open", nowOpen);
      if (nowOpen) open_groups.add(key);
      else open_groups.delete(key);

      $(this).find(".sel-mini").last().text(nowOpen ? "▾" : "▸");
    });

    // Select all in group
    $wrap.find('[data-action="select-all"]').off("click").on("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const $card = $(this).closest(".card");
      const key = ($card.attr("data-group") || "").trim();
      open_groups.add(key);

      $card.find(".sel-check").each(function () {
        const item = ($(this).data("item") || "").trim();
        if (item) selected.add(item);
        $(this).prop("checked", true);
      });

      render();
    });

    // Clear group
    $wrap.find('[data-action="clear"]').off("click").on("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const $card = $(this).closest(".card");
      const key = ($card.attr("data-group") || "").trim();
      open_groups.add(key);

      $card.find(".sel-check").each(function () {
        const item = ($(this).data("item") || "").trim();
        if (item) selected.delete(item);
        $(this).prop("checked", false);
      });

      render();
    });

    // Single checkbox change
    $wrap.find(".sel-check").off("change").on("change", function () {
      const item = ($(this).data("item") || "").trim();
      if (!item) return;

      const $card = $(this).closest(".card");
      const key = ($card.attr("data-group") || "").trim();
      open_groups.add(key);

      if ($(this).is(":checked")) selected.add(item);
      else selected.delete(item);

      render();
    });
  }
}

function get_lab_config() {
  return {
    title: __("Select Lab Tests"),
    source_doctype: "Lab Test Template",
    source_fields: ["lab_test_name", "department", "profile"],
    source_filters: { is_billable: 1, disabled: 0 },
    source_order_by: "department asc, lab_test_name asc",

    group_key(row) {
      const p = (row.profile || "").trim();
      if (p) return p.toUpperCase();
      const dep = (row.department || "").trim();
      if (dep) return dep.toUpperCase();
      return "OTHERS";
    },

    item_label(row) {
      return (row.lab_test_name || "").trim();
    },

    target_childtable: "lab_test_prescription",
    target_field: "lab_test_code",
  };
}

// frappe.ui.form.on('Inpatient Order', {
//     refresh(frm){
 
//         // frm.set_query('drug_code', 'drug_prescription', function() {
//         //     return {
//         //         // query: "his.api.dp_drug_pr_link_query.my_custom_query",
//         //         filters: {
//         //             parent: "DP-000016"
//         //         }
                
//         //     };
//         // }),
//     },
// 	// bed: function(frm) {
//     //     setTimeout(() => {
//     //         var filed = frappe.meta.get_docfield("Nurse Drug Prescription", "drug_code", frm.docname);
    
       
//     //         filed.options = "Item";
//     //         console.log(filed)
//     //         // frm.refresh_field("drug_prescription")
//     //         frm.get_field("drug_prescription").grid.refresh();
//     //         frm.refresh_field("drug_prescription")
            
//     //     }, 1000);
   
//     //     var field = frappe.meta.get_docfield('Inpatient Order', 'bed', cur_frm.docname);
        
//     //     // Change the datatype to 'Select'
//     //     field.options = 'Item';
        
//     //     // Update the field in the form
//     //     cur_frm.fields_dict['bed'].refresh();
// 	// 	frm.refresh_field('drug_prescription');
        
       
     
// 	// }


// });
// frappe.ui.form.on('Nurse Drug Prescription', {
// 	refresh(frm) {
// 		// your code here
// 	},
//     from:function(frm ,cdt ,cdn){
//         var row= locals[cdt][cdn]
//         // alert(row.from)
//         if(row.from == "Extra")
//         {
//             row.doc = 'Item'

//         }
//         else{
//             row.doc = "Nurse Drug Prescription"
//             frm.set_query('drug_code', 'drug_prescription', function() {
//                 return {
//                     // query: "his.api.dp_drug_pr_link_query.my_custom_query",
//                     filters: {
//                         parent: "DP-000021"
//                     }
                    
//                 };
//             })
//         }
      
//         frm.refresh_field("drug_prescription")

//     },
// 	drug_code: function(frm, cdt, cdn){
//         var row= locals[cdt][cdn]
//         // alert(row.from)
	
//      if(row.from !== "Extra"){
//         // row.doc = 'Item'

//     // var childtable = frm.fields_dict['drug_prescription'];

//     // childtable.grid.grid_rows[row.idx-1].docfields[1].options = 'Item'
//     // frm.get_field("drug_prescription").grid.refresh();

  
//     frm.refresh_field("drug_prescription")
// 	 var drug_code= row.drug_code
	 
// 	 frappe.call({
//     method: 'his.api.inpatient_order.drug_code',
//     args: {
//         'drug_code': drug_code,
//         // doctor_plan: frm.doc.doctor_plan,

//     },
//     callback: function(r) {
//         // console.log(r.message[0].drug_code)
//      row.drug_name=r.message[0].drug_code
//     //  frm.set_value("qty",2)
//     // frm.set_value("item_name", r.message[0].drug_code)
//      frm.refresh_field("drug_prescription")
//     }
// });
// }else{
    
//     row.drug_name = row.drug_code
//     frm.refresh_field("drug_prescription")
// }
// 	}
    
// })

// // frappe.ui.form.on('Nurse Drug Prescription', {
    
// //     from(frm, cdt, cdn) { 
// //         // change_op(frm)
// //         var row = locals[cdt][cdn];
 
// //         if(row.from == "Extra"){
// //             row.doc = 'Item'

// //         // var childtable = frm.fields_dict['drug_prescription'];
   
// //         // childtable.grid.grid_rows[row.idx-1].docfields[1].options = 'Item'
// //         // frm.get_field("drug_prescription").grid.refresh();
   
// //         }else{
// //             row.doc = "IPD Drug Prescription"
// //         }
// //         frm.refresh_field("drug_prescription")
// //     },

// //     // drug_code(frm, cdt, cdn){
// //     //     var row = locals[cdt][cdn];
// //     //     frappe.db.get_value("IPD Drug Prescription" , row.name , "drug_name").then( r => {
// //     //         console.log(r.message)
// //     //     })

// //     // }
// //    })
   

// function change_op(frm){
//    setTimeout(() => {
//     var filed = frappe.meta.get_docfield("Nurse Drug Prescription", "drug_code", frm.docname);


//     filed.options = "eerrr";
//     console.log(filed)
//     // frm.refresh_field("drug_prescription")
//     frm.get_field("drug_prescription").grid.refresh();
//     frm.refresh_field("drug_prescription")
    
// }, 1000);
// }