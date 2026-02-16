// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Request", {
  refresh: function (frm) {
    if (frm.is_new()) {
      // frappe.db.get_value("Employee" , {"user_id" : frappe.session.user} , 'department')
      // .then( r => {
      // 	// console.log(r.message)
      // 	frm.set_value("medical_department" , r.message.department)
      // })
    }
    if (frm.doc.docstatus == 0 && !frm.is_new()) {
      frm.add_custom_button(__("Reject"), function () {
        frappe.confirm(
          "Are you sure to Reject?",
          () => {
            // action to perform if Yes is selected
            frm.set_value("status", "Rejected");
            frm.savesubmit();
          },
          () => {
            // action to perform if No is selected
          }
        );

        //perform desired action such as routing to new form or fetching etc.
      });
    }
  },
});
