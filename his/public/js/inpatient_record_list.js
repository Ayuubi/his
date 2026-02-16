frappe.listview_settings['Inpatient Record'] = {
			// button: {
			// 	"type" : "btn",
			// 	color : "success",
			// 	status : ['Open'],
			// 	show: function(doc) {
			// 		if(doc.status=='Admitted'){
			// 			return true;
			// 		}
			// 	},
			// 	get_label: function() {
			// 		return __('Open Dotor Plan');
			// 	},
			// 	get_description: function(doc) {
			// 		return __('Print {0}', [doc.name])
			// 	},
			// 	action: function(doc) {
			// 		if(doc.doctor_plan){
			// 			frappe.set_route('Form', 'Doctor Plan', doc.doctor_plan);
			// 		}else if(doc.status=='Admitted'){
			// 			frappe.new_doc("Doctor Plan",{"patient": doc.patient,"ref_practitioner" : doc.primary_practitioner,}) 
			// 		}
												  
			// 	}
			// }

			button: {
				"type" : "btn",
				color : "success",
				status : ['Open'],
				show: function(doc) {
					if(doc.status=='Admitted' && doc.admitted_status=='Accepted'){
						return true;
					}
				},
				get_label: function() {
					return __('Inpatient Order');
				},
				get_description: function(doc) {
					return __('Print {0}', [doc.name])
				},
				action: function(doc) {
					
						frappe.new_doc("Inpatient Order",{"patient": doc.patient,"practitioner" : doc.primary_practitioner,}) 
				
												  
				}
			}

			// button: {
			// 	"type" : "btn",
			// 	color : "success",
			// 	status : ['Open'],
			// 	show: function(doc) {
			// 		if(doc.status=='Admitted'){
			// 			return true;
			// 		}
					
			// 	},
			// 	get_label: function() {
			// 		return __('Inpatient Medication');
			// 	},
			// 	get_description: function(doc) {
			// 		return __('Print {0}', [doc.name])
			// 	},
			// 	action: function(doc) {
				
			// 			frappe.new_doc("Inpatient Medication",{"patient": doc.patient,"practitioner" : doc.primary_practitioner,}) 
					
												  
			// 	}
			// }

		
	
};

