// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dental Plan', {
    refresh: function(frm) {
        calculate_total(frm);
    },
    
    validate: function(frm) {
        calculate_total(frm);
    },

    percentage_discount: function (frm) {
        if (frm.doc.percentage_discount > 0 && frm.doc.total > 0) {
            let discount_amount = (frm.doc.total * frm.doc.percentage_discount) / 100;
            frm.set_value("discount", discount_amount);
        } else {
            frm.set_value("discount", 0);
        }
        update_grand_total(frm);
    },

    discount: function (frm) {
        if (frm.doc.discount > 0 && frm.doc.total > 0) {
            let percentage_discount = (frm.doc.discount / frm.doc.total) * 100;
            frm.set_value("percentage_discount", percentage_discount);
        } else {
            frm.set_value("percentage_discount", 0);
        }
        update_grand_total(frm);
    }
});

frappe.ui.form.on('Services Prescription', { 
    service: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.service) {
            frappe.db.get_value('Other Service', {'template': row.service}, 'rate')
                .then(r => {
                    if (r.message.rate) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.rate);
                        // Ensure total is updated after rate is set
                        frappe.model.set_value(cdt, cdn, 'amount', r.message.rate); // Assuming amount = rate
                        frm.refresh_field('dental_plan_details'); // Ensure UI updates
                        calculate_total(frm);
                    }
                });
        }
    },
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.qty && row.rate) {
            let amount = row.qty * row.rate;
            frappe.model.set_value(cdt, cdn, 'amount', amount);
            calculate_total(frm);
        }
    },
    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.qty && row.rate) {
            let amount = row.qty * row.rate;
            frappe.model.set_value(cdt, cdn, 'amount', amount);
            calculate_total(frm);
        }
    },
    dental_plan_details_remove: function (frm) {
        calculate_total(frm);
    },

    // rate: function(frm, cdt, cdn) {
    //     calculate_total(frm);
    // }
});

function calculate_total(frm) {
    let total = 0;
    
    // Loop through the child table to calculate total fee
    frm.doc.dental_plan_details.forEach(row => {
        total += row.amount || 0;
    });

    frm.set_value("total", total);

    // Initially set grand_total equal to total if there's no discount
    if (!frm.doc.discount || frm.doc.discount === 0) {
        frm.set_value("grand_total", total);
    } else {
        update_grand_total(frm);
    }
}

function update_grand_total(frm) {
    let grand_total = (frm.doc.total || 0) - (frm.doc.discount || 0);
    frm.set_value("grand_total", grand_total);
}
