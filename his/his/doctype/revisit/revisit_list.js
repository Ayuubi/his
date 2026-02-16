let btn = {
    type : "btn",
    color : "success",
    status : ['Open'],
    show: function(doc) {
        if(doc.status == "Cancelled"){
            return false
        }
        return true;
    },
    get_label: function() {
        return __('Open Encounter');
    },
    get_description: function(doc) {
        return __('Print {0}', [doc.name])
    },
    action: function(doc) {
        frappe.db.get_doc("Revisit" , doc.name).then(r => {
        // if(r.patient_encounter){
        //     // frappe.call({
        //     //     method: "his.api.steps.pre", //dotted path to server method
        //     //     args: {
        //     //         "docname":doc.name
        //     //     },
        //     //     callback: function(r) {
        //     //     }
        //     //     });
        //     // frappe.set_route('Form', 'Patient Encounter', r.patient_encounter);
        //     frappe.new_doc("Patient Encounter",{"que": doc.name, "patient": r.patient,"practitioner" : r.practitioner}) 

        // }else{
           
                // console.log(r)
        frappe.new_doc("Patient Encounter",{"revisit" : doc.name,"patient": r.patient,"practitioner" : r.practitioner,}) 
    
          
        //    }
        frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
        // frappe.db.set_value("Revisit" , doc.name , "status" , "Closed")
        // doc.save()
    })
                                      
    }

}
if(frappe.user_roles.includes("Cashier")){
    btn = {
        type : "btn",
        color : "success",
        status : ['Closed'],
        show: function(doc) {
            return true;
        },
        get_label: function() {
            return __('Check FollowUp');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
            //frappe.set_route("/app/print/Invoice/" + doc.name);
            // frappe.msgprint(doc.patient_name)
          
             frappe.call({
                    method: "his.api.checkfollowup.Check_follow_up", //dotted path to server method
                    args: {
                        "patient" : doc.patient
			        
                    
                    },                                  

     callback: function(res) {
        console.log(res)
		// var template = "<table><tbody>{% for (var row in rows) { %}<tr>{% for (var col in rows[row]) { %}<td>rows[row][col]</td>{% } %}</tr>{% } %}</tbody></table>",
        // frm.set_df_property('html_fieldname', 'options', frappe.render(template, {rows: res.message});
        // frm.refresh_field('html_fieldname');
        let htmldata = ''
       
        res.message.forEach(row => {
            htmldata += ` <tr>
        <td>${row.patient_name}</td>
        <td>${row.practitioner}</td>
        <td>${row.start_date}</td>

        <td>${row.valid_till}</td>
        
        <td><button class= 'btn btn-success' id= 'f' onclick='
        frappe.call({
        method: "his.api.Que_to_fee_validity.make_que", //dotted path to server method
        args: {
            
            
            "patient" : "${row.patient}",
            "practitioner" : "${row.practitioner}"
            
        },
        callback: function(r) {
            $(".modal-dialog").hide()
           
            document.getElementById("f").disabled = true;
            // code snippet
            // frappe.msgprint(r)
        // frm.set_value("status" , "Refered")
         frappe.utils.play_sound("submit")
    frappe.show_alert({
        message:__("Que Created Successfully!!"),
        indicator:"green",
        
    }, 5);
        }
});
        ' width='40px'>Que</button></td>
      </tr>`
        })

        // ------------------------------------------------------------

        // -----------------------------

var template=`
<div class="container">
             
  <table class="table table-hover">
    <thead>
      <tr>
        <th>Patient Name</th>
        <th>practitioner Name</th>
        <th>Start Date</th>
        <th>End Date</th>
       
        <th>Action</th>
        
      </tr>
    </thead>
    <tbody>
    
    ${htmldata}
     
    </tbody>
  </table>
</div>

`;
                   		     		    
let d = new frappe.ui.Dialog({
    title: 'Follow Up Lists',
    fields: [
        {
            label: 'Que List',
            fieldname: 'practitioner',
            fieldtype: 'HTML',
            options: template,
            
        }
       
       
     
    ]

    
});

d.show();
d.$wrapper.find('.modal-content').css("width", "800px");
	     	

                        
                    }
        });
     
   
            
           //frappe.msgprint("Name "+doc.name+" Patient: "+doc.patient_name+" practitioner: "+doc.practitioner_name)
           
        }
    }
}
if(frappe.user_roles.includes("Doctor")){
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open Encounter');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
            alert()
            // if(doc.patient_encounter){
                // frappe.call({
                //     method: "his.api.steps.pre", //dotted path to server method
                //     args: {
                //         "docname":doc.name
                //     },
                //     callback: function(r) {
                //     }
                //     });
                frappe.set_route('Form', 'Patient Encounter', doc.patient_encounter);

            // }else{
            //     frappe.new_doc("Patient Encounter",{ "patient": doc.patient,"practitioner" : doc.practitioner,}) 
            // }
            // frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
            // doc.save()
                                          
        }
    }

}
// ------------------------------------------------------------------------------------------------
if(frappe.user_roles.includes("Dental")){
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open Dental');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
            if(doc.patient_encounter){
                // frappe.call({
                //     method: "his.api.steps.pre", //dotted path to server method
                //     args: {
                //         "docname":doc.name
                //     },
                //     callback: function(r) {
                //     }
                //     });
                frappe.set_route('Form', 'Dental', doc.name);

            }else{
                frappe.new_doc("Dental",{"que": doc.name, "patient": doc.patient,"practitioner" : doc.practitioner,}) 
            }
            frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
            // doc.save()
                                          
        }
    }

}
// -------------------------------------------------------------------------------------------------
if(frappe.user_roles.includes("Optometrist")){
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Optometrist');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
          
                frappe.new_doc("Optometrist",{"que": doc.name, "patient": doc.patient,"practitioner" : doc.practitioner,}) 
            
            // frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
            // doc.save()
                                          
        }
    }

}
// -------------------------------------------------------------------------------------------------
if(frappe.user_roles.includes("Nurse")){
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open Vital Signs');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
            // if(doc.patient_encounter){
            //     // frappe.call({
            //     //     method: "his.api.steps.pre", //dotted path to server method
            //     //     args: {
            //     //         "docname":doc.name
            //     //     },
            //     //     callback: function(r) {
            //     //     }
            //     //     });
            //     frappe.set_route('Form', 'Patient Encounter', doc.patient_encounter);

            // }else{
                frappe.new_doc("Vital Signs",{"que": doc.name, "patient": doc.patient}) 
            
            frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
            // doc.save()
                                          
        }
    }

}

if(frappe.user_roles.includes("OBS")){
   
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
            if(doc.type == "GYN"){
                
                frappe.new_doc("GYN",{ "patient": doc.patient,"practitioner" : doc.practitioner, "que":doc.name}) 

            }
            else{
                frappe.new_doc("OBS",{ "patient": doc.patient,"practitioner" : doc.practitioner,"que":doc.name}) 

            }
            frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
         
               
          
    }

}}


if(frappe.user_roles.includes("General Surgery")){
   
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
          
                frappe.new_doc("General Surgery",{ "patient": doc.patient,"practitioner" : doc.practitioner,"que":doc.name}) 

            
            frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
         
               
          
    }

}}


if(frappe.user_roles.includes("ENT")){
   
    btn = {
        type : "btn",
        color : "success",
        status : ['Open'],
        show: function(doc) {
            if(doc.status == "Cancelled"){
                return false
            }
            return true;
        },
        get_label: function() {
            return __('Open');
        },
        get_description: function(doc) {
            return __('Print {0}', [doc.name])
        },
        action: function(doc) {
          
                frappe.new_doc("ENT",{ "patient": doc.patient,"practitioner" : doc.practitioner,"que":doc.name}) 

            
            frappe.db.set_value("Revisit" , doc.name , "que_steps" , "Called")
         
               
          
    }

}}

frappe.listview_settings['Revisit'] = {


    button: btn,
    onload: function(listview) {
        var filters = [["Revisit", "date", "=", frappe.datetime.get_today()]];
        listview.filter_area.add(filters);
        if(!frappe.user_roles.includes("Doctordd")){
    
    listview.page.add_button(__("Stop"), () => table.download("xlsx", "data.xlsx", {sheetName:"My Data"}), {
       
    });
   
        frappe.db.get_value("Healthcare Practitioner" , {"user_id" : frappe.session.user} , ["name" , 'break'])
        .then(r => {
           
                // cur_page.page.list_view.page.clear_actions()
                listview.page.add_button(__("Continue"), () => {
                frappe.db.set_value("Healthcare Practitioner" ,r.message.name, "break" , 0)
                })
         
                // cur_page.page.list_view.page.clear_actions()
                listview.page.add_button(__("Break"), () => {

                    frappe.db.set_value("Healthcare Practitioner" ,r.message.name, "break" , 1)
                  
                    })

            
            

       
       
  

}, {
       
    });
}
}
// }
    
}


   



// }