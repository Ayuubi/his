// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Daily casheir cash closing', {
    
  
	refresh(frm) {
	    
		if(frm.is_new()){
		 //frappe.msgprint(frappe.session.user)
		frappe.call({
               
                method: "his.api.api_cashier.Get_Cashier_Account", //dotted path to server method
                args: {
                "user" : frappe.session.user
                },
            callback: function(r) {
                console.log(r)
                frm.set_value("account",r.message[0].against);
              }
            });
		  let user=  frm.set_value("full_name",frappe.session.user)
		    frm.set_df_property("recash", "read_only", 1);
		    cur_frm.set_df_property("request", "hidden", true);
		    frm.set_df_property("note", "read_only", 1);
		    cur_frm.set_df_property("send", "hidden", true);
		    // frm.disable_save();
		}
		if(!frm.is_new()){
		    
		    frm.set_df_property("cash_in_hand", "read_only", 1);
		}
        if (frappe.user_roles.includes('Main Cashier')) {
        frm.add_custom_button(__("Reject"), function(){
            let d = new frappe.ui.Dialog({
                title: 'Why are you rejecting?',
                fields: [
                    {
                        label: 'Reason',
                        fieldname: 'note',
                        fieldtype: 'Small Text',
                        reqd : 1
                    }
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    console.log(values);
                    frm.set_value("status" , "Rejected")
                    // frm.set_value("note" , values.note)
                    let p_note = frm.doc.note
                    frm.set_value("note",p_note + "\nfrom Main Cashier: " + values.note)
                    frm.refresh_field("note")
                    
                    frm.save()
                    d.hide();
                }
            });
            
            d.show();
            // alert()
            //perform desired action such as routing to new form or fetching etc.
          })
        }
// frm.custom_buttons["Send"].css("background-color", "red");
      
	},
	   
		get_cashier_score: function(frm){
            let cash_ex='';
		 if(frm.doc.cash_in_hand<=0){
		     frappe.msgprint("fadlan gali cash in hand-kaaga maanta");
		 }  
		 else{
		   let cash_in_hand=''; 
		let cashier_name=frm.doc.full_name;
		 
	            frappe.call({
                    method: "get_cashier_score", //dotted path to server method
                    doc : frm.doc,
                    args: {
                        "date" :  get_today()
                
                    },
                    callback: function(r){
                        console.log(r.message)
                        r.message.forEach(element => {
                    frm.set_value("total_sales",element.other_income);
                    frm.set_value("cash_sales",element.cash_sales);
                    frm.set_value("collected_payments",element.reciept);
                    frm.set_value("total_cash_expected",(element.other_income|| 0) + (element.reciept || 0) + (element.cash_sales || 0));
                    //alert(element.total_sales|| 0 + element.reciept || 0 + element.other_income || 0)
                    
                    let total_cash_expected=frm.doc.total_cash_expected;
                     cash_in_hand=frm.doc.cash_in_hand;
                    let diff=total_cash_expected-cash_in_hand;
                    frm.set_value("diffrence",diff);

                            
                        });
                    }
        //             callback: function(r) {
        //             console.log(r) 
        //             //  console.log(r.message.length) 
        //             if(r.message.length>2){
        //                  frm.set_value("total_sales",r.message[1].Total_Sales+r.message[2].Total_Sales);
        //             }
        //             else if(r.message.length==1){
        //                 frm.set_value("total_sales",r.message[0].Total_Sales);
        //             }
        //             else{
        //                 frm.set_value("total_sales",r.message[1].Total_Sales);
        //             }
        //             // frm.set_value("total_sales",r.message[1].Total_Sales+r.message[2].Total_Sales);
        //             frm.set_value("cash_sales",r.message[0].Cash_Sales);
        //             frm.set_value("collected_payments",r.message[0].Collected_Payments);
        //             frm.set_value("total_cash_expected",r.message[0].Total_Cash_Expected);
        //             cash_ex=r.message[0].Total_Cash_Expected;
                    
        //             let total_cash_expected=frm.doc.total_cash_expected;
        //              cash_in_hand=frm.doc.cash_in_hand;
        //             let diff=total_cash_expected-cash_in_hand;
        //             frm.set_value("diffrence",diff);
        //             frm.set_df_property("cash_in_hand", "read_only",1);
        //             //  console.log(frm.doc.total_cash_expected)
        //             let date= frm.doc.posting_date;
        //             let name= frm.doc.full_name
                    
        //             frappe.call({
        //                 method: "his.api.api_cashier.Daily_Cashier_Status", //dotted path to server method
        //                 args: {
        //                     "cash_in_hand" : frm.doc.cash_in_hand,
        //                     "posting_date" : date,
        //                     "user" : name,
        //                     "account": acc,
        //                     "expected" : frm.doc.total_cash_expected
                    
                    
        //                 },
        //                 callback: function(r) {
        //                 //  frappe.msgprint(r)
                          
        //                 console.log(r)
                 
                            
        //                 }
        //     });
        //                   // ---------------------------------------create new doc in cash closing ----------------------------------------
        //         frappe.call({
        //             method: "his.api.api_cashier.Create_new_doc_cash_closing", //dotted path to server method
        //             args: {
                        
        //                 "posting_date" : date,
        //                 "user" : name,
        //                 'account': frm.doc.account,
        //                 "status": "Requesting To Approve",
        //                 "total_sales": frm.doc.total_sales,
        //                 "cash_sales": frm.doc.cash_sales,
        //                 "collected_payments": frm.doc.collected_payments,
        //                 "total_cash_expected": frm.doc.total_cash_expected,
        //                 "cash_in_hand" : frm.doc.cash_in_hand,
        //                 "diffrence": frm.doc.diffrence
                
                
        //             },
        //             callback: function(r) {
        //             frappe.msgprint(r)
        //             frm.refresh();
        //             // console.log(r)
             
                        
        //             }
        // });

             
                        
        //             }
        });
        // ------------------------------------to journal intery--------------------------------------------------
            
	// 	  let date= frm.doc.posting_date;
    //       let name= frm.doc.full_name;
          
	//       let acc=frm.doc.account;
	// //   frappe.msgprint(cash_ex)
    //   console.log(frm.doc.cash_in_hand)
        


        
		 }
		},
        
		
		//-----------------------------------------------------------------------------------------------------------------
		
	send: function(frm){
		  let note=frm.doc.note;
		  let date= frm.doc.posting_date;
          let name= frm.doc.full_name
		  console.log(note)
      	 frappe.call({
                    method: "his.api.api_cashier.note", //dotted path to server method
                    args: {
                        "note" : note,
                        "posting_date" :date,
                        "user" : name
                
                    },
                    callback: function(r) {
                    
                      
                    // console.log(r)
             
                        
                    }
        });
		  
		     frappe.msgprint("send succesfully");
		 } , 
// 		cash_in_hand:function(frm){
// 		   let total_cash_expected=frm.doc.total_cash_expected;
// 		   let cash_in_hand=frm.doc.cash_in_hand;
// 		   let diff=total_cash_expected-cash_in_hand;
// 		   frm.set_value("diffrence",diff);
// 		},
		
		
// 	--------------------------------------------Request Cash In Hand-----------------------------
	request: function(frm){
	    if(frm.doc.status=="Requesting To Approve"){
	        frappe.msgprint("codisgaada hora ayaad u gudbisay");
	    }
	     else if(frm.doc.status=="Approved!"){
	        frappe.msgprint("Waa lagu approve gareeyey");
	    }
	     else if(frm.doc.recash<=0){
		     frappe.msgprint("fadlan gali cash in hand-kaaga cusub");
		 }
		 else{
		  let recash=frm.doc.recash;
		  let date= frm.doc.posting_date;
          let name= frm.doc.full_name;
          let status=frm.doc.status
          let diff=frm.doc.total_cash_expected-recash;
          frm.set_value("diffrence","");
		  console.log(recash+date+name+status)
      	 frappe.call({
                    method: "his.api.api_cashier.request", //dotted path to server method
                    args: {
                        "recash" : recash,
                        'account': frm.doc.account,
                        "posting_date" :date,
                        "user" : name,
                        "status" :status
                
                    },
                    callback: function(r) {
                    
                    frappe.msgprint(r)  
                    // console.log(r)
                    location.reload();
                        
                    }
        });
		  
		     //frappe.msgprint("Your Request Has been  Reached");
		     
		 }
		 } , 

})
