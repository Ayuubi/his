frappe.ui.form.on('Order', {
	refresh(frm) {
		frm.add_custom_button('Cash', () => {
			let d = new frappe.ui.Dialog({
				title: 'Order Details',
				fields: [
					{
						label: 'Patient ID',
						fieldname: 'patient',
						fieldtype: 'Link',
						options : "Patient"
					},
					{
						label: 'Patient Name',
						fieldname: 'patient_name',
						fieldtype: 'Data'
					},
					{
						label: 'Total',
						fieldname: 'total',
						fieldtype: 'Currency'
					},
					{
						label: 'Lab Ref',
						fieldname: 'lab_ref',
						fieldtype: 'Data'
					}
				],
				primary_action_label: 'Submit',
				primary_action(values) {
					frappe.call({
						method: "his.api.create_inv.create_inv", //dotted path to server method
						
						args: {
							"doc_name": frm.doc.name ,
							"lab_ref" : d.get_value("lab_ref")
					
					},
						callback: function(r) {
							// code snippet
							d.hide();
						}
					});
					
				}
			});
			d.set_values({
				"patient" : frm.doc.patient,
				"patient_name" : frm.doc.patient_name,
				"total" :  frm.doc.grand_total
			})
			d.show();
			// alert("Credit")
			// frappe.set_route('Form', frm.doc.reference_type, frm.doc.reference_name);
		}),
	
		// 	frm.add_custom_button('Credit', () => {
		// 	let d = new frappe.ui.Dialog({
		// 		title: 'Order Details',
		// 		fields: [
		// 			{
		// 				label: 'Patient ID',
		// 				fieldname: 'patient',
		// 				fieldtype: 'Link',
		// 				options : "Patient"
		// 			},
		// 			{
		// 				label: 'Patient Name',
		// 				fieldname: 'patient',
		// 				fieldtype: 'Data'
		// 			},
		// 			{
		// 				label: 'Total',
		// 				fieldname: 'total',
		// 				fieldtype: 'Currency'
		// 			}
		// 		],
		// 		primary_action_label: 'Submit',
		// 		primary_action(values) {
		// 			frappe.call({
		// 				method: "his.api.create_inv.create_inv", //dotted path to server method
						
		// 				args: {"doc_name": frm.doc.name  , is_credit : 1},
		// 				callback: function(r) {
		// 					// code snippet
		// 					d.hide();
		// 				}
		// 			});
					
		// 		}
		// 	});
		// 	d.set_values({
		// 		"patient" : frm.doc.patient,
		// 		"patient_name" : frm.doc.patient_name,
		// 		"total" :  frm.doc.grand_total
		// 	})
		// 	d.show();
		// 	// alert("Credit")
		// 	// frappe.set_route('Form', frm.doc.reference_type, frm.doc.reference_name);
		// }),
		// your code here
		calculate_total(frm)
		frm.save()
	},
	// frappe.realtime.on('event_name', (data) => {
	// 	console.log(data)
	// })
	before_save:function(frm){
		// alert('ok')
		calculate_total(frm)
	}
})

frappe.ui.form.on('Order Items', {
	refresh(frm) {
		// your code here
	},
	item: function(frm , cdt , cdn){
		// alert("ok")
		var row = locals[cdt][cdn]
		row.amount = row.qty * row.rate
		calculate_total(frm)
		frm.refresh_field('order_items')
		
		// alert(row.item)
	},
	qty: function(frm , cdt , cdn){
		// alert("ok")
		var row = locals[cdt][cdn]
		row.amount = row.qty * row.rate
		calculate_total(frm)
		frm.refresh_field('order_items')
		
		// alert(row.item)
	},
	rate: function(frm , cdt , cdn){
		// alert("ok")
		var row = locals[cdt][cdn]
		row.amount = row.qty * row.rate
		calculate_total(frm)
		frm.refresh_field('order_items')
		
		// alert(row.item)
	}
})
function calculate_total(frm){
	let grand_total = 0
	var rows = frm.doc.order_items
	rows.forEach(item => {
		grand_total +=  parseInt(item.qty) * parseFloat(item.rate) 
	});
	frm.set_value('grand_total' , grand_total)
}