

frappe.pages['blood-bank'].on_page_load = function(wrapper) {
	new Room(wrapper)
}

Room = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Blood Bank",
				single_column : true
			});
			// $('.page-head').empty()
			this.make()
			
			// this.make_grouping_btn()
			// this.grouping_cols()
		},
		make:function(){
			let pinfo_se = $('#pinfo_blood')
			
			
			pinfo_se.html("Blood Bank")
			let me = this
			// let room_field = this.page.add_field({
			// 	fieldtype: 'Link',
			// 	options: 'Healthcare Service Unit Type',
			// 	fieldname: 'room',
			// 	placeholder: __('Select Room'),
			// 	only_select: true,
			// 	change: () => {
			// 		me.get_beds(room_field.get_value());
			// 		// me.curMonth = field.get_value()
			// 		// me.setup_datatable()
			// 	}
			// });

			// let type_field = this.page.add_field({
			// 	label: 'Type',
			// 	fieldname: 'type',
			// 	fieldtype: 'Link',
			// 	options :'Inpatient Type',
			// 	placeholder: __('Select Room'),
			// 	only_select: true,
			// 	change: () => {
			// 		// get_beds(room_field.get_value());
			// 		// me.curMonth = field.get_value()
			// 		// me.setup_datatable()
			// 	}
			// });

			
			// if (frappe.route_options) {
			// 	room_field.set_value(frappe.route_options.room);
			// 	type_field.set_value(frappe.route_options.type);
			// 	// console.log(frappe.route_options.inp_doc)
			// 	// this.patient_id = frappe.route_options.room;
			// }
			$(frappe.render_template("blood_bank", me)).appendTo(me.page.main)
			me.get_blood();


		
		
			
			
			




		
		},
		get_blood:function(){
			me = this
			frappe.call({
				method: "his.api.get_blood_bank.get_blood_store_balance", //dotted path to server method
				callback: function(r) {
					let records = r.message
				console.log(r);
				
				let bl = ``
				let sts_bg_class= "card_one_vocant_single"
				btn = ``
				records.forEach(element => {
					
				
					bl += `
					<div class="${sts_bg_class}">
					<div class="bed_icon">
					  <span><img src = "/files/icons8-blood-48.png"  /></span>
					</div>
					<span class="bed_tex">${element.blood_group}</span>
					<span class="bed_tex">${element.units} Unit</span> 
					${element.patient_name}
					<button class="btn-success" onclick ="reqest_blood('${element.patient}' , '${element.blood_group}')">Request </button>
				  </div>
				 
					`
				});
				// console.log(bed)
				let blood_bn = `
				
				<div class="room1_single mobile">
				
				<div class="my_main_cards_single">
				
		  
				 
				${bl}
				
		  
				</div>
			  </div>
				`
				
				// Append beds to rooms section
				$('#blood_bank').empty()
				$(blood_bn).appendTo('#blood_bank')
			}
			})
		},

		
	

	})


	function reqest_blood(patient , blood_group){
		frappe.new_doc("Blood Request form" , {"patient" : patient , "blood_group" : blood_group})
		// alert(patient)
	}


	