// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Daily Cashier Status', {
refresh: function(frm) {
//   frm.set_value("user",frm.doc.user)

    
         if (!frm.is_new() && frm.doc.docstatus != 1){
            //   frm.set_value("messege","?");
   
      var start_btn=  frm.add_custom_button(__("Reject"), function(){
          //let message=frm.doc.messege;
        if(!frm.doc.messege){
       frappe.msgprint("Why are you Rejecting? write your massage");
       
       frm.toggle_reqd("messege", true) 
        }
        else{
       
		 if(frm.doc.status=="Rejected!"){
		      let message=frm.doc.message;
		      console.log(message);
	        frappe.msgprint("Alrady Rejected");
	    }
        else{
        var  date=frm.doc.posting_date;
        var user = frm.doc.user;
        let status= frm.doc.status;
        let message= frm.doc.messege;
   
        console.log(message)
         
        
        //console.log(date +' '+user);
        
                    frappe.call({
                    method: "his.api.api_cashier.daily_cashier_closing_status", //dotted path to server method
                    args: {
                        "pos_date" : date,
                        "user" : user,
                        "status" : status,
                        "message" : message,
                        
                        
                     
                    },
                    callback: function(r) {
                        
                //frappe.msgprint(r)
                console.log(r)


                       
                        
                    }
                    
});
}
      
        }
        
    });
    start_btn.addClass('btn-danger');
    

}
  },
  on_submit: function(frm){
    //   frappe.msgprint("akdajsdkjashdkjsajkhkj")
               if (!frm.is_new()){
        var  date=frm.doc.posting_date;
        var user = frm.doc.user;
               frappe.call({
                    method: "his.api.api_cashier.daily_cashier_approved", //dotted path to server method
                    args: {
                        "pos_date" : date,
                        "user" : user,
                   },
                    callback: function(r) {
                        
                frappe.msgprint(r)
                      
                    }
});
      
   
        
 

}
  }
})
