frappe.listview_settings['Sales Order'] = {
    
    
          button: {
        show: function(doc) {
            return true;
        },
        get_label: function() {
            return __('CASH');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.customer])
        },
        action: function(doc) {
           let d = new frappe.ui.Dialog({
         title: 'Cash Payment',
    fields: [
        {
            label: 'Customer',
            fieldname: 'customer',
            fieldtype: 'Data',
            // cust: frm.doc.customer,
            // read_only: 1
           
           
            
           
        }
        ,
        {
            label: 'Paid Amount',
            fieldname: 'total',
            fieldtype: 'Currency',
            reqd:1
            
           
        },
         {
            label: 'Discount',
            fieldname: 'discount_amount',
            fieldtype: 'Currency',
            
           
        },
     
    ],
    
    primary_action_label: 'Submit',
    	
    
    primary_action(values) {
          frappe.call({
                method: "his.api.make_invoice.make_sales_invoice", //dotted path to server method
                args: {
                    source_name : doc.name, 
                    paid_amount: values.total,
                    discount: values.discount_amount,
                    // company: frappe.defaults.get_default('Company'),
                    // party_account: values.party_account,
                },
            callback: function(r) {
                console.log(r)
                
              }
            });
        




          
          d.hide();
          //frm.disable_save();
    }
    // primary_action(values) {
    //       let cust= d.get_value("customer")
    //       let msg = d.get_value("massage");
    //       let reff=frm.doc.return_against;
          
    //       d.hide();
    //       frm.disable_save();
    // primary_action_label: 'Send Request',
   
	
});
d.set_value("customer",doc.customer_name);


d.show();
        //     console.log(customer)
        //   frappe.msgprint(customer)
        },
        
    },
}
     
     
    
    
    