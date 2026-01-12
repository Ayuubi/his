// // Copyright (c) 2023, Rasiin Tech and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Package Template', {
// 	// refresh: function(frm) {

// 	// }
// 	before_save: function(frm){
// 		let total_rate=0;
// 	   var tbl = cur_frm.doc.package_prescription || [];
// 	   for(var i = 0; i < tbl.length; i++) {
// 		   total_rate+=flt(tbl[i].rate * tbl[i].qty);
		   
// 	   }
// 	   frm.set_value("rate",total_rate);
//    }
// });

function recalc_package_total(frm) {
  let total = 0;
  (frm.doc.package_prescription || []).forEach(row => {
    total += flt(row.rate) * flt(row.qty);
  });
  frm.set_value("rate", total);
}

frappe.ui.form.on("Package Template", {
  before_save(frm) {
    recalc_package_total(frm);
  },
  refresh(frm) {
    recalc_package_total(frm);
  }
});

// IMPORTANT: replace "Package Prescription" with your actual CHILD TABLE doctype name
frappe.ui.form.on("Package Prescription", {
  qty(frm, cdt, cdn) {
    recalc_package_total(frm);
  },
  rate(frm, cdt, cdn) {
    recalc_package_total(frm);
  },
  package_prescription_remove(frm) {
    recalc_package_total(frm);
  }
});
