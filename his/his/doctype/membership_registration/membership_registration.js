frappe.ui.form.on("Membership Registration", {
  refresh(frm) {
    // Optional beauty card (only if you add the HTML field)
    render_membership_summary(frm);
  },

  register_all(frm) {
    frappe.confirm("Register/Update all unregistered family members?", () => {
      frappe.call({
        method: "his.his.doctype.membership_registration.membership_registration.register_family_members",
        args: { docname: frm.doc.name },
        freeze: true,
        freeze_message: "Processing members...",
        callback(r) {
          const msg = r.message || {};
          const registered = msg.registered || [];
          const skipped = msg.skipped || [];

          if (registered.length) {
            frappe.msgprint({
              title: "Registered / Updated",
              indicator: "green",
              message: registered.join(", ")
            });
          }

          if (skipped.length) {
            frappe.msgprint({
              title: "Skipped",
              indicator: "orange",
              message: skipped.map(x => `${x.name || ("Row " + x.row)}: ${x.reason}`).join("<br>")
            });
          }

          frm.reload_doc();
        }
      });
    });
  }
});

frappe.ui.form.on("Family Members", {
  create_patient(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const action = row.patient ? "Update" : "Create";

    frappe.confirm(`${action} Patient for ${row.full_name || "this row"}?`, () => {
      frappe.call({
        method: "his.his.doctype.membership_registration.membership_registration.register_single_member",
        args: { docname: frm.doc.name, membername: row.name },
        freeze: true,
        freeze_message: `${action} in progress...`,
        callback(r) {
          const msg = r.message || {};
          if (msg.status === "ok") {
            frappe.show_alert(`${action} successful: ${msg.name}`, 5);
            frm.reload_doc();
          } else {
            frappe.show_alert(`${msg.name} already registered`, 5);
          }
        }
      });
    });
  }
});


// --------------------------------------------------
// Optional UI banner (requires HTML field: membership_summary_html)
// --------------------------------------------------
function render_membership_summary(frm) {
  if (!frm.fields_dict.membership_summary_html) return;

  const w = frm.fields_dict.membership_summary_html.$wrapper;
  if (!w) return;

  const status = frm.doc.status || "Inactive";
  const discount = frm.doc.discount_level || 0;
  const card = frm.doc.card_number || "—";
  const start = frm.doc.start_date || "—";
  const end = frm.doc.end_date || "—";
  const total = frm.doc.total || 0;

  // UI-only expiry calc
  let effective = status;
  if (status === "Active" && frm.doc.end_date) {
    const today = frappe.datetime.get_today();
    if (frappe.datetime.str_to_obj(today) > frappe.datetime.str_to_obj(frm.doc.end_date)) {
      effective = "Expired";
    }
  }

  w.html(`
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:14px;background:#fff;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:16px;font-weight:700;">
          Membership Card: <span style="font-weight:800;">${card}</span>
        </div>
        <div style="font-weight:700;">${effective}</div>
      </div>

      <div style="display:flex;gap:18px;margin-top:10px;flex-wrap:wrap;">
        <div><b>Discount:</b> ${discount}%</div>
        <div><b>Validity:</b> ${start} → ${end}</div>
        <div><b>Members:</b> ${total}</div>
      </div>

      <div style="margin-top:10px;color:#6b7280;font-size:12px;">
        Head Patient: select <b>head_patient</b> to UPDATE, leave empty to CREATE.
      </div>
    </div>
  `);
}



// // Copyright (c) 2025, Rasiin Tech and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Membership Registration', {
//     onload: function(frm) {
//         // Store initial value on load
//         frm._last_status = frm.doc.status;
//     },

//     after_save: function(frm) {
//         if (!frm._last_status || frm._last_status === frm.doc.status) return;

//         if (frm.doc.status === "Active") {
//             frappe.show_alert({
//                 message: "Membership reactivated. Benefits restored.",
//                 indicator: "green"
//             });
//         } else if (frm.doc.status === "Inactive") {
//             frappe.show_alert({
//                 message: "Membership deactivated. Members reset.",
//                 indicator: "orange"
//             });
//         }

//         // Update the stored value
//         frm._last_status = frm.doc.status;
//     },
//     register_all: function(frm) {
//         frappe.confirm("Register all unvisited family members?", () => {
//             frappe.call({
//                 method: "his.his.doctype.membership_registration.membership_registration.register_family_members",
//                 args: { docname: frm.doc.name },
//                 freeze: true,
//                 freeze_message: "Registering all members...",
//                 callback: function(r) {
//                     if (r.message.length) {
//                         frappe.msgprint(__('Registered: ') + r.message.join(", "));
//                         frm.reload_doc();
//                     } else {
//                         frappe.show_alert("All members already registered!", 5);
//                     }
//                 }
//             });
//         });
//     }
// });


// frappe.ui.form.on('Family Members', {
// 	create_patient: function(frm, cdt, cdn) {
// 	    const row = locals[cdt][cdn];
// 	    frappe.confirm(`Register ${row.full_name} as Patient?`, () => {
// 	        frappe.call({
// 	            method: "his.his.doctype.membership_registration.membership_registration.register_single_member",
// 	            args: {
// 	                docname: frm.doc.name,
// 	                membername: row.name
// 	            },
// 	            freeze: true,
// 	            freeze_message: "Registering member...",
// 	            callback: function(r) {
// 	                if (r.message.status === "ok") {
// 	                    frappe.msgprint(__('Patient created for ') + r.message.name);
// 	                    frm.reload_doc();
// 	                } else {
// 	                    frappe.show_alert(r.message.name + " is already registered!", 5);
// 	                }
// 	            }
// 	        });
// 	    });
// 	}
// });

