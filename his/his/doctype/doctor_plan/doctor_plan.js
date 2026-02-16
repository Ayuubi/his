frappe.ui.form.on('Doctor Plan', {
    refresh(frm) {
        refresh_field('drug_prescription');
        refresh_field('discharge_drug_prescription');

        frm.set_query('drug_code', 'drug_prescription', function () {
            return {
                filters: {
                    is_stock_item: 1,
                    item_group: "Drug"
                }
            };


        })

        //     frm.set_query('drug_code', 'discharge_drug_prescription', function() {
        //             return {
        //                 filters: {
        //                     is_stock_item: 1,
        //                     item_group: "Drug"
        //                 }
        //             };


        // })
        // if (!frm.is_new()) {
        //     frm.add_custom_button('Today ', () => {
        //         consoleerp_hi(frm.doc.patient , frm.doc.patient_name , true)
        //       }, 'History');
        //       frm.add_custom_button('History', () => {
        //         consoleerp_hi(frm.doc.patient , frm.doc.patient_name )
        //       }, 'History');
        //     // var btn= frm.add_custom_button('Orders', () => {
        //     //      if(frm.doc.inpatient_order){
        //     //          frappe.set_route('Form', 'Inpatient Order', frm.doc.inpatient_order);
        //     //      }else{
        //     //      frappe.new_doc("Inpatient Order",{"doctor_plan": frm.doc.name, "patient": frm.doc.patient,"practitioner" : frm.doc.ref_practitioner}) 
        //     //      }
        //     //  })
        //     //  btn.addClass('btn-primary');
        //     // --------------------------------------------------end of order------------------------------------------------------
        //     if (frappe.user_roles.includes('Doctor')) {
        //         var btn = frm.add_custom_button('Discharge Order', () => {
        //             frappe.new_doc("Discharge Summery", { "patient": frm.doc.patient, "ref_practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
        //             //             frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Discharge patient : <strong>${frm.doc.patient_name}</strong>?`,
        //             //                     () => {
        //             //             frappe.call({
        //             //             method: "his.api.discharge.patient_clearance", //dotted path to server method
        //             //             args: {
        //             //                     "patient" : frm.doc.patient,
        //             //                     "practitioner" : frm.doc.ref_practitioner,
        //             //                     "inpatient_record": frm.doc.inpatient_record
        //             //                     },
        //             //                     callback: function(r) {
    
        //             //                             frappe.utils.play_sound("submit")
        //             //                                 frappe.show_alert({
        //             //                                     message:__('Patient '+ frm.doc.patient+" Discharge Order Successfully!!"),
        //             //                                     indicator:'green',
        //             //                                 }, 5);
        //             //                     }
        //             // });
        //             //             },)
        //         })
        //         btn.addClass('btn-danger');
        //     } 

        //     if (frappe.user_roles.includes('GP')) {
        //         var btn1 = frm.add_custom_button('Order', () => {
        //             frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
            
        //         })
        //     } 

        //     if (frappe.user_roles.includes('Nurse')) {
        //         var btn3 = frm.add_custom_button('Vital Sign', () => {
        //             frappe.new_doc("Vital Signs", { "patient": frm.doc.patient })
            
        //         })
        //         btn3.addClass('btn-primary');
        //         var btn1 = frm.add_custom_button('Order', () => {
        //             frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
            
        //         })
        //         btn1.addClass('btn-danger');
        //         var btn2 = frm.add_custom_button('Medication', () => {
        //             frappe.new_doc("Inpatient Medication", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
            
        //         })
        //         btn2.addClass('btn-danger');

        //     } 


        //     if (frappe.user_roles.includes('ICU')) {
        //         var btn3 = frm.add_custom_button('ICU', () => {
        //             frappe.new_doc("ICU", { "patient": frm.doc.patient , "practitioner": frm.doc.ref_practitioner})
            
        //         })
        //         btn3.addClass('btn-primary');
        //         var btn1 = frm.add_custom_button('Order', () => {
        //             frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
            
        //         })
        //         btn1.addClass('btn-danger');
        //         var btn2 = frm.add_custom_button('Medication', () => {
        //             frappe.new_doc("Inpatient Medication", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
            
        //         })
        //         btn2.addClass('btn-danger');

        //     } 
        // }
        // your code here
    }
})
