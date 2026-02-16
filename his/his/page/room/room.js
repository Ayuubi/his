
frappe.pages['room'].on_page_load = function(wrapper) {
	new Room(wrapper)
}

Room = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Rooms",
				single_column : true
			});
			$('.page-head').empty()
			this.make()
			
			// this.make_grouping_btn()
			// this.grouping_cols()
		},
		make:function(){
			let pinfo_se = $('#pinfo')
			if(frappe.route_options.patient){
				let pinfo = `
				<span>${frappe.route_options.patient}</span>
 
			 `
			}
			
			pinfo_se.html("test")
			let me = this
			let room_field = this.page.add_field({
				fieldtype: 'Link',
				options: 'Healthcare Service Unit Type',
				fieldname: 'room',
				placeholder: __('Select Room'),
				only_select: true,
				change: () => {
					me.get_beds(room_field.get_value());
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});

			let type_field = this.page.add_field({
				label: 'Type',
				fieldname: 'type',
				fieldtype: 'Link',
				options :'Inpatient Type',
				placeholder: __('Select Room'),
				only_select: true,
				change: () => {
					// get_beds(room_field.get_value());
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});

			
			if (frappe.route_options) {
				room_field.set_value(frappe.route_options.room);
				type_field.set_value(frappe.route_options.type);
				// console.log(frappe.route_options.inp_doc)
				// this.patient_id = frappe.route_options.room;
			}
			$(frappe.render_template("room", me)).appendTo(me.page.main)
			me.get_beds(room_field.get_value());


		
		
			
			
			




		
		},
		get_beds:function(room_name){
			me = this
			frappe.db.get_list('Healthcare Service Unit', {
				fields: ['name', 'occupancy_status'],
				filters: {
					service_unit_type: room_name,
					"disabled" : 0
				}
			}).then(records => {
				// console.log(records);
				let bed = ``
				let sts_bg_class= "card_one_occupied_single"
				btn = ``
				records.forEach(element => {
					
					if(element.occupancy_status === "Occupied"){
						sts_bg_class = "card_one_occupied_single"
						btn = `` 
					}
					else if(element.occupancy_status === "Vacant"){
						sts_bg_class = "card_one_vocant_single"
						btn = `<button class="btn btn-success mb-3" onclick = "me.admit('${element.name}')"> Admit </button>`
					}
					else{
						sts_bg_class = "card_one_cleaning_single"
						btn = ``
					}
					bed += `
					<div class="${sts_bg_class}">
					<div class="bed_icon">
					  <span><i class="fa fa-bed"></i></span>
					</div>
					<span class="bed_tex">${element.name}</span>
					<span class="bed_tex">${element.occupancy_status}</span> 
					${btn}
				  </div>
				 
					`
				});
				// console.log(bed)
				let beds = `
				
				<div class="room1_single mobile">
				<h1>${room_name}</h1>
				<div class="my_main_cards_single">
				
		  
				 
				${bed}
				
		  
				</div>
			  </div>
				`
				
				// Append beds to rooms section
				$('#single_room').empty()
				$(beds).appendTo('#single_room')
			})
		},

		admit:function(bed){
			let me = this
			frappe.db.get_doc("Patient" , frappe.route_options.patient)
			.then(data => {
				is_insurance = ""
				if (data.is_insurance){


					let d = new frappe.ui.Dialog({

						title: `This patient in insurance <strong>${data.patient_name}</strong> is in insurance <strong>${data.ref_insturance} </strong> do you want to Charge Patient or insurance

						  <br>

						`,
						fields: [
						{
						 label: 'Insurance',
						 fieldname: 'btn',
						 fieldtype: 'HTML',
						 options: `<button type="button" class="btn btn-success" onclick='me.admit_p("${data.is_insurance}" , "${bed}","${data.patient_name}"); $(".modal-dialog").hide()'>Patient</button>
								  <button type="button" class="btn btn-danger" onclick='me.admit_p_insurence("${data.ref_insturance}" ,"${bed}", "${data.patient_name}"); $(".modal-dialog").hide()'>insurance</button>`,
						 
						 }]

						  
						  
					});

					d.show();

					
					// frappe.warn('This patient in insurance ',
					// 		data.patient_name+ ', is in insurance '+ data.ref_insturance+' do you want to Charge Patient or insurance',
					// 		() => {
					// 			// frappe.model.set_value(frm.doctype, frm.docname, 'is_insurance', 1);
					// 			// action to perform if Continue is selected
					// 			// is_insurance = data.ref_insturance
					// 			frappe.call({
					
					// 				method: 'his.api.admit.admit_p',
					// 				args:{

					// 					"inp_doc" :frappe.route_options.inp_doc,
					// 					'service_unit': bed,
					// 					"is_insurance" : data.ref_insturance
					// 					// 'check_in': Date(),
					// 					// 'expected_discharge': expected_discharge
					// 				},
					// 				callback: function(data) {}
					// 			})
					// 		},
					// 		'insurance',
					// 		true // Sets dialog as minimizable
					// 	)
					
				}
				else{

					frappe.confirm(`Are you sure you want to Admit Patient <strong> ${data.patient_name} </storng>?`,
    () => {
		me.admit_p(bed,data.patient_name)


		// frappe.call({
					
		// 	method: 'his.api.admit.admit_p',
		// 	args:{
				
		// 		"inp_doc" :frappe.route_options.inp_doc,
		// 		'service_unit': bed,
		// 		// "is_insurance" : data.ref_insturance
		// 		// 'check_in': Date(),
		// 		// 'expected_discharge': expected_discharge
		// 	},
		// 	callback: function(data) {}
		// })
        // action to perform if Yes is selected
    }, () => {
        // action to perform if No is selected
    })


					
				}
				// alert(bed)
			

			})
		

			

		},
		admit_p_insurence : function(insurence , bed,patient_name){
					// is_insurance = data.ref_insturance
					// pat_name=data.patient_name
					frappe.call({
					
						method: 'his.api.admit.admit_p',
						args:{

							"inp_doc" :frappe.route_options.inp_doc,
							'service_unit': bed,
							"is_insurance" :insurence,
							"patient":patient_name
							
							// 'check_in': Date(),
							// 'expected_discharge': expected_discharge
						},
						callback: function(data) {
							frappe.msgprint("Admited")
						}
					})
		},
		admit_p:function(bed,patient_name){
			frappe.call({
					
				method: 'his.api.admit.admit_p',
				args:{
					
					"inp_doc" :frappe.route_options.inp_doc,
					'service_unit': bed,
					"patient":patient_name,
					"type": frappe.route_options.type,
					// "is_insurance" : data.ref_insturance
					// 'check_in': Date(),
					// 'expected_discharge': expected_discharge
				},
				callback: function(data) {
					frappe.msgprint("Admited")
				}
			})

		}

	})


	