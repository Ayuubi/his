/* global frappe, flt */

frappe.ui.form.on("Expenses", {
  onload(frm) {
    // Paid From: only Bank/Cash, non-group, company
    frm.set_query("paid_from", function () {
      return {
        filters: {
          is_group: 0,
          account_type: ["in", ["Bank", "Cash"]],
          company: frm.doc.company,
        },
      };
    });

    // Expense Account: only Expense root_type, non-group, company
    frm.set_query("expense_account", "expense_lines", function () {
      return {
        filters: {
          is_group: 0,
          root_type: "Expense",
          company: frm.doc.company,
        },
      };
    });

    // Party: depends on party_type
    frm.set_query("party_type", "expense_lines", function () {
		return {
			filters: {
			name: ["in", ["Customer", "Supplier", "Employee"]],
			},
		};
		});
  },

  company(frm) {
    // refresh filters when company changes
    frm.refresh_field("paid_from");
    frm.refresh_field("expense_lines");
  },

  refresh(frm) {
    frm.trigger("recalc_total_amount");
  },

  recalc_total_amount(frm) {
    const total = (frm.doc.expense_lines || []).reduce((sum, r) => sum + flt(r.amount), 0);
    frm.set_value("total_amount", total);
  },
});

frappe.ui.form.on("Expense Line", {
  amount(frm) {
    frm.trigger("recalc_total_amount");
  },

  expense_lines_remove(frm) {
    frm.trigger("recalc_total_amount");
  },

  party_type(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    // clear party when party_type changes
    row.party = "";
    frm.refresh_field("expense_lines");
  },
});



// // Copyright (c) 2021, Rasiin and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Expenses', {
// 	// refresh: function(frm) {
// 	// 	frappe.call({
// 	// 		method: "his.api.get_mode_of_payments.mode_of_payments",
// 	// 		args: {
// 	// 		  company: frappe.defaults.get_default('Company'),
// 	// 		},
// 	// 		callback: function (r) {
// 	// 		  console.log(r.message);
// 	// 		  frm.set_value("paid_from" , r.message[0])
// 	// 		  frm.set_value("cost_center" , r.message[1])
// 	// 		}
// 	// 	  });
// 	// }
// });
