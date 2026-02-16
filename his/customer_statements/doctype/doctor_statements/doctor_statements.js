// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
function set_employee_from_doctor(frm) {
  var doctor = frm.doc.doctor;

  if (!doctor) {
    frm.set_value('employee', null);
    return;
  }

  // You can pass the name directly OR a filter object:
  // get_value('Doctype', name, field)  OR  get_value('Doctype', {name: ...}, field)
  frappe.db
    .get_value('Healthcare Practitioner', doctor, 'employee')
    .then(function (r) {
      var employee = r && r.message ? r.message.employee : null;
      return frm.set_value('employee', employee);
    })
    .catch(function (e) {
      console.error('Failed to fetch employee:', e);
      frm.set_value('employee', null);
    });
}
frappe.ui.form.on('Doctor Statements', {
	doctor: function (frm) {
    set_employee_from_doctor(frm);
  },
	// refresh: function(frm) {

	// }
		refresh: function (frm) {
			    set_employee_from_doctor(frm);

		// setTimeout(() => {
		// 	frm.set_value("payable_account", "2110 - Creditors - SH")
		//   }, 500);
	  // Default values in From and To Dates
	  var today = frappe.datetime.nowdate();
	  frm.set_value('from_date', frappe.datetime.month_start(today));
	  frm.set_value('to_date', today);
  
	  frm.set_query("payable_account", function() {
		return {
			"filters": {
			  'company': frm.doc.company,
			  'account_type': ['in',['Payable','Receivable']],
			  
			}
		};
	});
	if(!frappe.user_roles.includes("Main Cashier")){
    
		frm.set_df_property('payable_account',  'read_only', 1);
	
	  }
  
	},
	get_customer_emails: function (frm) {
	  frappe.call({
		method: "populate_recipient_list",
		doc: frm.doc,
		callback: function (r) {
		  cur_frm.refresh_field('recipients');
		  cur_frm.save();
		}
	  });
	},
	send_customer_statements: function (frm) {
	  let validRecipients = frm.doc.recipients.filter(c => c.send_statement === "Yes").length;
	  frappe.confirm(
		'Are you sure you want to send Customer Statement Emails to <b>' + validRecipients + '</b> customers?',
		function () {
		  frappe.call({
			method: "his.api.api.statements_sender_scheduler",
			args: {
			  manual: true
			},
			callback: function (r) {
			}
		  });
		},
		function () {
		  window.close();
		}
	  );
	},
	enqueue_sending_statements: function (frm) {
	  let validRecipients = frm.doc.recipients.filter(c => c.send_statement === "Yes").length;
	  frappe.confirm(
		'Are you sure you want to enqueue Customer Statement Emails to <b>' + validRecipients + '</b> customers?',
		function () {
		  frappe.call({
			method: "his.api.api.statements_sender_scheduler",
			args: {
			  manual: false
			},
			callback: function (r) {
			}
		  });
		},
		function () {
		  window.close();
		}
	  );
	},
	preview: function (frm) {
	  if (frm.doc.employee != undefined && frm.doc.employee != "") {
		frappe.call({
		  method: "his.api.api.get_report_content_3",
		  args: {
			account : frm.doc.payable_account,
			company: frm.doc.company,
			employee_name: frm.doc.employee,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date
		  },
		  callback: function (r) {
			
			var x = window.open();
			x.document.open().write(r.message);
		  }
		});
	  }
	  else {
		frappe.msgprint('Please select a employee');
	  }
	},
	letter_head: function (frm) {
	  cur_frm.save();
	},
	no_ageing: function (frm) {
	  cur_frm.save();
	},
	send_email: function (frm) {
	  if (frm.doc.customer != undefined && frm.doc.customer != "") {
		frappe.call({
		  method: "his.api.api.send_individual_statement",
		  args: {
			company: frm.doc.company,
			customer: frm.doc.customer,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date,
			email_id: "to_find"
		  },
		  callback: function (r) {
			frappe.msgprint(__("Email queued to be sent to customer"))
		  }
		});
	  }
	  else {
		frappe.msgprint('Please select a customer');
	  }
	},
  
});
