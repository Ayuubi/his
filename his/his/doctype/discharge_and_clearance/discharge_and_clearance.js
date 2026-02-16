// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Discharge And Clearance', {
	refresh: function(frm) {
		if(!frm.is_new()){
			if(frm.doc.patient_balance){
				var refurn_btn=  frm.add_custom_button(__("Transfer Balance"), function(){
					let from_c = frm.doc.customer
					let amount = frm.doc.patient_balance
					transfer_balance(from_c,amount)
				});
				var refurn_btn=  frm.add_custom_button(__("Receipt"), function(){
					let d = new frappe.ui.Dialog({
						title: 'Receipt details',
						fields: [
							{
								label: 'Posting Date',
								fieldname: 'posting_date',
								fieldtype: 'Date',
								reqd : 1,
								default: frappe.datetime.get_today()
							},
							{
								fieldname: "party_account",
								label: __("Receivable Account"),
								fieldtype: "Link",
								options: "Account",
								hidden: 1,
								get_query: () => {
									var company = frappe.query_report.get_filter_value('company');
									return {
										filters: {
											'company': company,
											'account_type': 'Receivable',
											'is_group': 0
										}
									};
								}
							},
							{
								label: 'Paid Amount',
								fieldname: 'paid_amount',
								fieldtype: 'Currency',
								reqd : 1,
								default : frm.doc.patient_balance
							},
							{
								label: 'Discount',
								fieldname: 'discount',
								fieldtype: 'Currency',
								reqd : 0
							},
						],
						primary_action_label: 'Submit',
						primary_action(values) {
							frappe.call({
								method: "his.api.create_p_e.payment_re",
								args: {
								  
								  
								  party: frm.doc.customer,
								  posting_date: values.posting_date,
								  paid_amount: values.paid_amount,
								  discount: values.discount,
								  company: frappe.user_defaults.company,
								  party_account: values.party_account,
								  inpatient_record : frm.doc.inpatient_record,
								  
								},
								callback: function (r) {
									frm.reload_doc();
					
								frappe.utils.play_sound("submit")

								frappe.show_alert({
								message:__('Recieved Succesfully'),
								indicator:'green',
								
							}, 5);
								}
							  });
							//   frappe.call({
							// 	method: "erpnext.accounts.utils.get_balance_on",
							// 	args: {
							// 		company: frappe.defaults.get_user_default("Company"),
							// 		party_type: "Customer",
							// 		party: frm.doc.customer,
							// 		date: get_today(),
							// 	},
							// 	callback: function(r, rt) {
								
							// 		if(!r.message) {

							// 			frappe.call({
							// 				method: "his.api.inpatient_record.clear_patient", //dotted path to server method
							// 				args: {
							// 					inpatient_record : frm.doc.inpatient_record,
	   
							// 				   },
							// 						callback: function(r) {
							// 							console.log(r)
							// 									frappe.utils.play_sound("submit")
							// 									frappe.show_alert({
							// 										message:__('Patient: '+frm.doc.patient+' Cleared Successfully!!'),
							// 										indicator:'green',
							// 									}, 5);
							// 										}
							// 								});
							// 		}
							// 	}
							// });
							d.hide();
						}
					});

				d.show()

					});

			}
			
					var refurn_btn=  frm.add_custom_button(__("Clearance"), function(){
						
					let d = new frappe.ui.Dialog({
					    title: 'Enter the reason',
					    fields: [
					        {
					            label: 'Reason',
					            fieldname: 'reason',
					            fieldtype: 'Small Text',
					            reqd:0
					           
					        },
					  
					    ],
					    primary_action_label: 'Submit',
					    primary_action(values) {
								frappe.call({
					            method: "his.api.inpatient_record.clearance", //dotted path to server method
					            args: {
					            		 "reason": values.reason,
					            		 "name":frm.doc.name,
					               		"inpatient_record" : frm.doc.inpatient_record,

					                    },
								 callback: function(r) {
								//  console.log(r)
                    			frappe.utils.play_sound("submit")
								frappe.show_alert({
									message:__('Patient: '+frm.doc.patient+' Cleared Successfully!!'),
									indicator:'green',
								}, 5);
									 

					        d.hide();
					    }
					});

					
				}
					});
					d.show();
					
					
			// 	frm.add_custom_button(__("Clearance"), function(){
			// 		frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Clear patient <strong>${frm.doc.patient_name}</strong> ?`,
			// 		() => {
									
			// frappe.call({
            // method: "his.api.inpatient_record.clearance", //dotted path to server method
            // args: {
            //    		"inpatient_record" : frm.doc.inpatient_record
            //         },
            //         callback: function(r) {
            //         	console.log(r)
            //         			frappe.utils.play_sound("submit")
			// 					frappe.show_alert({
			// 						message:__('Patient: '+frm.doc.patient+' Cleared Successfully!!'),
			// 						indicator:'green',
			// 					}, 5);
            //       				  }
			// 				});
			// 			},)
			// 		});
		})
		}
	},
	customer: function(frm){
		

		// let cost_centers
		// let data = []
		// frappe.db.get_list('Cost Center', {
        //     fields: ['name'],
        //     filters: {
        //         is_group: 0
        //     }
        // }).then(function(records) {
        //     if (records) {
        //         // do something with the list of Cost Centers
        //      cost_centers = records.map(function(r) {
        //             return r.name;
        //         });
        //         // console.log(cost_centers);
		// 		// let centers = []
		// 		cost_centers.forEach(row=>{
		// 			frappe.call({
		// 				method: "erpnext.accounts.utils.get_balance_on",
		// 				args: {
		// 					company: frappe.defaults.get_user_default("Company"),
		// 					party_type: "Customer",
		// 					party: frm.doc.customer,
		// 					date: get_today(),
		// 					cost_center: row
		// 				},
		// 				callback: function(r) {
		// 					if(r.message) {
		// 						// console.log(r.message)
		// 						// console.log(row)
		// 					centers.push({"cost_center" : row , "amount" : r.message})
		// 					}
							
		// 				}
		// 			});
		// 			})
		// 	console.log(cost_centers)
		// 	setTimeout(() => {
		// 		frm.set_value("patient_receivables" , centers)
				
		// 	}, 100);
			
		// 	}});
		// cost_centers.forEach(row=>{	
		// frappe.call({
		// method: "erpnext.accounts.utils.get_balance_on",
		// args: {
		// 	company: frappe.defaults.get_user_default("Company"),
		// 	party_type: "Customer",
		// 	party: frm.doc.customer,
		// 	date: get_today(),
		// 	cost_center: row,
		// },
		// callback: function(r, rt) {
		// 	if(r.message) {
		// 		console.log(data)

		// 	data.push({"cost_center" : row , "amount" : r.message})
		// 				}
			
		// }
		// });
		// })
		// setTimeout(() => {
		// frm.set_value("patient_receivables" , data)
		// }, 200);
		frappe.call({
			method: "erpnext.accounts.utils.get_balance_on",
			args: {
				company: frappe.defaults.get_user_default("Company"),
				party_type: "Customer",
				party: frm.doc.customer,
				date: frappe.datetime.get_today()
			},
			callback: function(r, rt) {
				if(r.message) {
				    // alert(r.message)
				frm.set_value("patient_balance", r.message)
				}
			}
		});
		frappe.call({
			method: "his.api.api.patient_clearance",
			args: {
				"patient": "AHMED CALI GEEDI"
			},
			callback: function(r) {
				let centers = [];
				if (r.message) {
					r.message.forEach(row => {
						centers.push({
							"cost_center": row.cost_center,
							"amount": row.amount
						});
					});
				}
				frm.set_value("patient_receivables", centers);
			}
		});
		
		
		
		// frappe.call({
        //     method: "his.api.api.patient_clearance", //dotted path to server method
        //     args: {
        //        		"patient" : frm.doc.patient
        //             },
        //             callback: function(r) {
		// 				let centers= []
        //             	// frm.set_value("patient_receivables" , [{"cost_center" : "Demo - D" , "amount" : r.message[0].outstanding}])
        //             	r.message.forEach(row=>{
        //             		// alert(row.amount)
        //             		// alert(r.message[0].outstanding)
		// 					centers.push({"cost_center" : row.cost_center , "amount" : row.amount})
							

        //             	})
		// 			// console.log(centers)
        //             frm.set_value("patient_receivables" , centers)
        //             }});
	
	},

	onload: function(frm){

		// let cost_centers
		// let data = []
		// frappe.db.get_list('Cost Center', {
        //     fields: ['name'],
        //     filters: {
        //         is_group: 0
        //     }
        // }).then(function(records) {
        //     if (records) {
        //         // do something with the list of Cost Centers
        //      cost_centers = records.map(function(r) {
        //             return r.name;
        //         });
        //         // console.log(cost_centers);
		// 		// let centers = []
		// 		// cost_centers.forEach(row=>{
		// 		// 	// frappe.call({
		// 		// 	// 	method: "erpnext.accounts.utils.get_balance_on",
		// 		// 	// 	args: {
		// 		// 	// 		company: frappe.defaults.get_user_default("Company"),
		// 		// 	// 		party_type: "Customer",
		// 		// 	// 		party: frm.doc.customer,
		// 		// 	// 		date: get_today(),
		// 		// 	// 		cost_center: row
		// 		// 	// 	},
		// 		// 	// 	callback: function(r) {
		// 		// 	// 		if(r.message) {
		// 		// 	// 			// console.log(r.message)
		// 		// 	// 			// console.log(row)
		// 		// 	// 		centers.push({"cost_center" : row , "amount" : r.message})
		// 		// 	// 		}
							
		// 		// 	// 	}
		// 		// 	// });
		// 		// 	})
		// 	// console.log(cost_centers)
		// 	// setTimeout(() => {
		// 	// 	frm.set_value("patient_receivables" , centers)
				
		// 	// }, 100);
			
		// 	}});
		// cost_centers.forEach(row=>{	
		// frappe.call({
		// method: "erpnext.accounts.utils.get_balance_on",
		// args: {
		// 	company: frappe.defaults.get_user_default("Company"),
		// 	party_type: "Customer",
		// 	party: frm.doc.customer,
		// 	date: get_today(),
		// 	cost_center: row,
		// },
		// callback: function(r, rt) {
		// 	if(r.message) {
		// 		// console.log(r.message)
		// 	data.push({"cost_center" : row , "amount" : r.message})
		// 				}
			
		// }
		// });
		// })
		// setTimeout(() => {
		// frm.set_value("patient_receivables" , data)
		// }, 200);
				frappe.call({
					method: "erpnext.accounts.utils.get_balance_on",
					args: {
						company: frappe.defaults.get_user_default("Company"),
						party_type: "Customer",
						party: frm.doc.customer,
						date: frappe.datetime.get_today()
					},
					callback: function(r, rt) {
						if(r.message) {
							// alert(r.message)
						frm.set_value("patient_balance", r.message)
						}
					}
				});

		frappe.call({
            method: "his.api.api.patient_clearance", //dotted path to server method
            args: {
               		"patient" : frm.doc.patient
                    },
                    callback: function(r) {
						console.log(r);
						let centers= []
                    	// frm.set_value("patient_receivables" , [{"cost_center" : "Demo - D" , "amount" : r.message[0].outstanding}])
                    	r.message.forEach(row=>{
							
                    		// alert(row.amount)
                    		// alert(r.message[0].outstanding)
							centers.push({"cost_center" : row.cost_center , "amount" : row.amount})
							

                    	})
                    frm.set_value("patient_receivables" , centers)
					frm.save()
                    }
});
frm.save()
	}
});
