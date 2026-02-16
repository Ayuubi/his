// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Daily Main cashier Closing', {
   refresh(frm){
         if(frm.is_new()){
       frm.set_value("main_cashier_user",frappe.session.user)
       //console.log(frm.doc.main_cashier_user);
        frappe.call({
                    method: "his.api.api_cashier.get_Main_Cashier", //dotted path to server method
                    args: {
                        
                        "posting_date" : frm.doc.date,
                        "user" : frm.doc.main_cashier_user,
                     
                    },
                    callback: function(r) {
                        frm.set_value("available",r.message[0].Total);
              
                    console.log(r)
                  
                    }
        });
       
         }
   },
     
  
	before_save:function(frm){
	    let total_amount=0;
	    var tbl = cur_frm.doc.accounts || [];
	    for(var i = 0; i < tbl.length; i++) {
	        total_amount+=flt(tbl[i].amount);
	        
	    }
	    frm.set_value("total",total_amount);
    	refresh_field("total");
    	 frm.set_value("balance" , frm.doc.available-total_amount);
    	 frm.set_value("transfer" , total_amount);
	 
	  
	    
	   
	}





})

frappe.ui.form.on('Main Account Entery', {
    accounts_add(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        // frm: current ToDo form
        // cdt: child DocType 'Dynamic Link'
        // cdn: child docname (something like 'a6dfk76')
        // cdt and cdn are useful for identifying which row triggered this event
        frappe.defaults.get_default('Company')
        let abbr= frappe.get_abbr(frappe.defaults.get_default("company"))
        let row = locals[cdt][cdn]
        row.froms = "Main Cashier - MSH";
        frm.refresh_field("accounts")

       // frappe.msgprint('A row has been added to the links table 🎉 ');
    }
 
   })


