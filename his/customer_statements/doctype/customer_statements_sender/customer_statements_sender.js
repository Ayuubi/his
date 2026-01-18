// Copyright (c) 2020, Dirk van der Laarse and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Statements Sender', {
  refresh: function (frm) {
    // setTimeout(() => {
    //   frm.set_value("recieable_account", "1310 - Debtors - SH")
    // }, 500);
    // Default values in From and To Dates
    var today = frappe.datetime.nowdate();
    frm.set_value('from_date', frappe.datetime.month_start(today));
    frm.set_value('to_date', today);

    frm.set_query("recieable_account", function() {
      return {
          "filters": {
            'company': frm.doc.company,
						'account_type': 'Receivable',
             
          }
      };
  });

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
    var method= "his.api.api.get_report_content";
    if (frm.doc.detail){
      method= "his.api.api.customer_statement_details"
    }
    if (frm.doc.customer != undefined && frm.doc.customer != "") {
      frappe.call({
        method: method,
        args: {
          account : frm.doc.recieable_account,
          company: frm.doc.company,
          customer_name: frm.doc.customer,
          cost_center: frm.doc.cost_center,
          customer: frm.doc.customer,
          from_date: frm.doc.from_date,
          to_date: frm.doc.to_date,

          
          detail : frm.doc.detail
        },
        callback: function (r) {
          
          var x = window.open();
          x.document.open().write(r.message);
          // let sta_htl = $('#sta_htl')
          // sta_htl.html(r.message)
        }
      });
    }
    else {
      frappe.msgprint('Please select a customer');
    }
  },

  summary_statement: function (frm) {
    if (frm.doc.customer) {
      frappe.call({
        method: "his.api.api.get_summary_statement",
        args: {
          company: frm.doc.company,
          customer: frm.doc.customer, // ✅ make sure this is passed
          from_date: frm.doc.from_date,
          to_date: frm.doc.to_date,
          account: frm.doc.recieable_account
        },
        callback: function (r) {
          const x = window.open();
          x.document.open().write(r.message);
        }
      });
    } else {
      frappe.msgprint('Please select a customer');
    }
  },

  download_excel: function (frm) {
    if (frm.doc.customer) {
      frappe.call({
        method: "his.api.api.download_excel_report",
        args: {
          account: frm.doc.recieable_account,
          company: frm.doc.company,
          customer_name: frm.doc.customer,
          customer: frm.doc.customer,
          from_date: frm.doc.from_date,
          to_date: frm.doc.to_date,
          detail: frm.doc.detail,
        },
        callback: function (r) {
          if (r.message && r.message.file_url) {
            window.open(r.message.file_url);  // triggers download
          } else {
            frappe.msgprint("Failed to generate Excel file.");
          }
        }
      });
    } else {
      frappe.msgprint('Please select a customer');
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
