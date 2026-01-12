// Copyright (c) 2022, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Radiology', {
	refresh(frm) {
        let rad_images='';
        frm.doc.attachments.forEach(im=>{
            rad_images+=`\n<div class="col-4">
                        <img src="${im.attachment}" alt="Image" style="width:100% ; height: 80% ; padding : 10px ; border : 1px solid #000">
                      </div>`
        })
            let img=`<div class="row">
                      ${rad_images}
                     
                </div>`
        frm.set_df_property("att","options",img);
        // console.log(records);


if (!frm.is_new() && frm.doc.section === "Endoscopy Unit") {
    frm.add_custom_button(__('Consent Form'), function() {
        frappe.new_doc('Consent Surgery Form', {
            'patient': frm.doc.patient,
            'practitioner': frm.doc.practitioner,
            'surgery_type': frm.doc.eximination,
        });
    });
}

    
    
        


// frappe.db.get_list('File', {
//     fields: ['file_url'],
//     filters: {
//         attached_to_name: frm.doc.name
//     }
// }).then(records => {
//     let images='';
//     records.forEach(im=>{
//         images+=`\n<div class="col-4">
//                     <img src="${im.file_url}" alt="Image" style="width:100% ; height: 80% ; padding : 10px ; border : 1px solid #000">
//                   </div>`
//     })
//     	let img=`<div class="row">
//                   ${images}
                 
//             </div>`
//     frm.set_df_property("att","options",img);
//     // console.log(records);
// })


	}
})