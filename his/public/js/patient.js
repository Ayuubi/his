frappe.ui.form.on('Patient', {
	refresh(frm) {
		// alert()
		if (frappe.user_roles.includes('Cashier')) {   
			frm.set_df_property("is_employee" , "hidden" , 1)
			frm.set_df_property("is_insurance" , "hidden" , 1)
			frm.set_df_property("ref_insturance" , "hidden" , 1)
			frm.set_df_property("insurance_number" , "hidden" , 1)
		}
       
// 		    frm.set_query('ref_insturance', () => {
//     return {
//         filters: {
//             customer_group: 'INSURANCE'
//         }
//     }
// })
	}
})
 

