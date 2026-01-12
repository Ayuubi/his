	frappe.pages['admission-scheduled'].on_page_load = function(wrapper) {
	new IPD(wrapper)
}

IPD = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Admission Scheduled",
				single_column : true
			});
			this.groupbyD = []
			this.currDate =  frappe.datetime.get_today()
			this.make()
			this.setupdata_table()
			this.make_grouping_btn()
			let myf_ads = this
			frappe.realtime.on('inp_update', (data) => {
				// alert("in realtime")
				myf_ads.setupdata_table()
					})
			// this.grouping_cols()
		},
		make:function(){

		
			let me_s = this
			// let date = this.page.add_field({
			// 	fieldtype: 'Date',
			
			// 	fieldname: 'date',
			// 	label : "Date",
			// 	default: frappe.datetime.get_today(),
				
				
			// 	change: () => {
			// 		// alert()
			// 		this.currDate = date.get_value()
			// 		me.setupdata_table()
			// 		// me.curMonth = field.get_value()
			// 		// me.setup_datatable()
			// 	}
			// });
   		
   		
			$(frappe.render_template(frappe.dashbard_page.body, me_s)).appendTo(me_s.page.main)




		
		},

		setupdata_table : function(gr_ref){
			
		let tbldata = []
		frappe.db.get_list('Inpatient Record', {
			fields: ['name','patient','patient_name', 'room' , 'type' , 'status' ,'scheduled_date' , 'admission_practitioner', 'diagnose'],
			filters: {
				status: 'Admission Scheduled'
			},
			limit : 1000
		}).then(r => {
			// console.log(r)
			
            // code snippet
            // $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			tbldata = r
        // console.log(r)
   

			// let doct ='Sales Order'.replace(' ' , '-').toLowerCase()
		
	
		//  let fields = frappe.get_meta("Sales Order").fields
		 	columns = [
			// {title:"ID", field:"name"},
			// {title:"Patient", field:"customer"},
			{title:"PID", field:"patient" ,  headerFilter:"input"},
			{title:"Patient Name", field:"patient_name" ,  headerFilter:"input"},
			{title:"Date", field:"scheduled_date" ,  headerFilter:"input"},
			{title:"Doctor Name", field:"admission_practitioner" ,  headerFilter:"input",},
			// {title:"Room", field:"room" ,  headerFilter:"input",},
			
			{title:"Type", field:"type" ,  headerFilter:"input",},
			{title:"Status", field:"status" ,  headerFilter:"input",},
			{title:"Diagnosis", field:"diagnose" ,  headerFilter:"input",},
			

			{title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
			
		 ]
		//  fields.forEach(field => {
		// 	if(field.in_list_view){
		// 		columns.push(
		// 			{title:field.label, field:field.fieldname}
		// 		)
		// 	}
		//  })
		// if(!gr_ref){
		// 	columns.unshift(
		// 		// {formatter:"responsiveCollapse", width:30, minWidth:30, hozAlign:"center", resizable:false, headerSort:false},
    
		// 		{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"left", headerSort:false, checked:function(e, cell){
		// 			// cell.getRow().toggleSelect();
		// 			// alert("ok 2")
		// 			me.toggle_actions_menu_button(true);
		// 		  }}
		// 	)
			
			
			

		// }
		// console.log("this is ",doctype)
		// let list_btns = frappe.listview_settings[`Sales Invoice`]
		// tbldata = tbldata[0]['action'] = "Button"
		let new_data_ad_s = []
		// if(list_btns)
		// console.log(tbldata)
		tbldata.forEach(row => {
			// console.log(row.status)
			// if(row.status === "To Deliver and Bill"){
			// 	row.status = "To Bill"

			// }
			// console.log("this is ",row.per_billed)
			let btnhml = ''
			// if(row.status !== "Draft" && row.status !== "Cancelled" && row.status!= "Completed" ){
			
			btnhml += `
			<button class='btn btn-primary ml-2' onclick = "admit('${row.name}','${row.patient }', '${row.admission_practitioner }')"> Admit</button>
			<button class='btn btn-danger ml-2' onclick = "cancel_admision('${row.name}','${row.patient }')"> Cancel</button>
		
			
			`
			// }
			// else{
			// 	btnhml += `
			// 	<div style="height: 100px; background-color: rgba(255,255,250);"> </div>
		
			
			// `

			// }
			// list_btns.forEach(btn => {
			// 	btnhml += `<button class='btn btn-primary' > ${btn.get_label()}</button>`
			// })
			// for (const key in list_btns) {

			// 	if (list_btns.hasOwnProperty(key) && list_btns[key].type == "btn") {
			
			// 		// console.log(`${key}: ${btn[key].get_label()}`);
			// 		btnhml += `<button class='btn btn-${list_btns[key].color} ml-2' onclick = ""> ${list_btns[key].get_label()}</button>`
			// 	}
			// }
			row['action'] = btnhml
			new_data_ad_s.push(row)
		})
		// console.log(columns)
this.table = new Tabulator("#ad_sche", {
			layout:"fitDataFill",
			// layout:"fitDataStretch",
			//  layout:"fitColumns",
			// responsiveLayout:"collapse",
			 rowHeight:30, 
			//  selectable:true,
			//  dataTree:true,
			//  dataTreeStartExpanded:true,
			 groupStartOpen:false,
			 printAsHtml:true,
			//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
			 printFooter:"<h2>Example Table Footer<h2>",
			 // groupBy:"customer",
			 groupHeader:function(value, count, data, group){
				 //value - the value all members of this group share
				 //count - the number of rows in this group
				 //data - an array of all the row data objects in this group
				 //group - the group component for the group
			 // console.log(group)
				 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
			 },
			 groupToggleElement:"header",
			//  groupBy:groupbyD.length >0 ? groupbyD : "",
			 textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
	 
			 columns: columns,
			 
			 // [
			 // 	{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"center", headerSort:false, cellClick:function(e, cell){
			 // 		cell.getRow().toggleSelect();
			 // 	  }},
			 // 	{
			 // 		title:"Name", field:"name", width:200,
			 // 	},
			 // 	{title:"Group", field:"item_group", width:200},
			 // ],
			 // [
			 // {title:"Name", field:"name" , formatter:"link" , formatterParams:{
			 // 	labelField:"name",
			 // 	urlPrefix:`/app/${doct}/`,
				 
			 // }},
			 // {title:"Customer", field:"customer" },
			 // {title:"Total", field:"net_total" , bottomCalc:"sum",},
		 
			 // ],
			 
			 data: new_data_ad_s
		 });
		 
		 //  table.getSelectedData(); 
		
		//  this.table.on("rowClick", function(e ,rows){
		// 	 let selectedRows = row.table.getSelectedRows(); 
		// 	 // console.log(rows._row.data)
		// 	//  console.log(row.table.getSelectedData())
		// 	//  row.toggle_actions_menu_button(row.table.getSelectedData().length > 0);
		// 	 frappe.set_route("Form" , doct , rows._row.data.name)
		// 	 // document.getElementById("select-stats").innerHTML = data.length;
		//    });
		//    $(document).ready(function() {
		// 	$('.tabulator input[type="checkbox"]').change(function() {
		// 	//   alert ("The element with id " + this.id + " changed.");
		// 	row.toggle_actions_menu_button(row.table.getSelectedData().length > 0);
		//   });
		  
		// 	});
		
	
});
		},


		make_grouping_btn:function(){
			let listitmes_ad_sc = ''
			
			
			let columns = [
				{title:"ID", field:"name"},
				{title:"Customer", field:"customer"},
				{title:"Customer Name", field:"customer"},
			
		 ]
				columns.forEach(field => {
					// console.log(field)
					// if(field.docfield.fieldtype !== "Currency"){
						listitmes_ad_sc += `
 
						<li>
						<input type="checkbox" class="form-check-input groupcheck ml-2"  value = '${field.field}' >
						<label class="form-check-label" for="exampleCheck1">${field.title}</label>
						
					</li>	
						
						`
	
					// }
				
	  
				
			})
			$('.page-heade')
			// 	<button type="button" class="btn btn-default btn-sm" data-toggle="dropdown">
			// 	<span class="dropdown-text">Grouping by</span>
			// 	<ul class="dropdown-menu dropdown-menu-right">
				
					
			// 		${listitmes_ad_sc}
			// 	</ul>
			// </button>
				$(`<div class="mt-2 sort-selector">
				
	
	
	
				<button type="button" class="btn btn-primary" onclick="add_inpatient()">Add New<b class="caret"></b></a>
				</button>
				<ul class="dropdown-menu">
				${listitmes_ad_sc}
			</ul>
				</div>`).appendTo('.page-head')
			
			// this.group_by_control = new frappe.ui.GroupBy(this);
		
		},

		grouping_cols:function(){
		
			let me_set = this
			$('.groupcheck').change(function() {
				// alert ("The element with id " + this.value + " changed.");
				let value = this.value
				if(this.checked) {
				groupbyD.push(this.value)
				}
				else{
					groupbyD = groupbyD.filter(function(e) { return e !== value })
				}
				me_set.setupdata_table(true);
				// setup_datatable()
				
			});
	
		   
		},

 make_sales_invoice : function(source_name) {
	alert("ok ok")
	frappe.model.open_mapped_doc({
		method: "his.api.make_invoice.make_sales_invoice",
		source_name: source_name
	})
},


 make_credit_invoice : function(source_name) {
	frappe.model.open_mapped_doc({
		method: "his.api.make_invoice.make_credit_invoice",
		source_name: source_name
	})
}
	}

	
)
let ScheduleAd = `

<div class="container">
<div class="row">

<div id="ad_sche" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : ScheduleAd
}

get_history = function(patient , patient_name){
	alert(patient)

	// frappe.route_options = { "patient" : patient };
	// frappe.set_route('view-vital-signs');
	frappe.set_route('Form', 'Patient History', { patient: "PID-00265" });


}
formatter = function(cell, formatterParams, onRendered){
			return frappe.datetime.prettyDate(cell.getValue() , 1)
		}



credit_sales = function(source_name){
	frappe.db.get_doc("Sales Order" , source_name)
	.then(r => {
		console.log(r)
		frappe.db.get_value("Customer" , r.customer , "allow_credit")
		.then(cu => {
			if(!cu.message.allow_credit){
				frappe.throw(__('Bukaan looma ogala dayn'))
			}
			else{

				frappe.call({
					method: "erpnext.accounts.utils.get_balance_on",
					args: {
						company: frappe.defaults.get_user_default("Company"),
						party_type: "Customer",
						party: r.customer,
						date: get_today(),
					},
					callback: function(balance) {
						// alert(r.customer)
						frappe.db.get_doc("Customer" , r.customer)
						.then(customer => {
							
							if(balance.message >= customer.credit_limits[0].credit_limit) {
								// alert(r.message)
							// frm.set_value("patient_balance", r.message)
							frappe.throw(__('Bukaankaan Wuu Dhaafay Xadka daynta loo ogolyahay'))
							}
							else{
								frappe.model.open_mapped_doc({
									method: "his.api.make_invoice.make_credit_invoice",
									source_name: source_name
								})

							}

						})
						
					}
				});


				

			}
		})

	})
	

}



function cancel_admision(inpatient_record, patient){
	frappe.confirm('Are you sure you want to Cancelled?',
    () => {
        // action to perform if Yes is selected
		frappe.call({
			
			method: 'his.api.admission_schd.cancel_admision',
			args:{
				
				"inp_doc" :inpatient_record,
			},
			callback: function(data) {
				frappe.msgprint("Cancelled Succesfullyss")
				location.reload();

			}
		})
    }, () => {
        // action to perform if No is selected
    })


}

function admit(inpatient_record, patient, practitioner, type){
	// alert(patient)

	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{fieldtype: 'Link', label: 'Type', fieldname: 'type', options: 'Inpatient Type',reqd: 1 , default: type},
			{fieldtype: 'Link', label: 'Room', fieldname: 'room', options: 'Healthcare Service Unit Type',reqd: 1},
			{fieldtype: 'Link', label: 'Bed', fieldname: 'bed', options: 'Healthcare Service Unit', reqd: 1},
			{fieldtype: 'Link', label: 'Additional Bed', fieldname: 'bed2', options: 'Healthcare Service Unit', reqd: 0, "hidden": 1},
			{fieldtype: 'Datetime', label: 'Check In', fieldname: 'check_in', reqd: 1, default: frappe.datetime.now_datetime()}
			   
	
		],
		primary_action_label: 'Submit',
		primary_action(values) {
			admit_p(inpatient_record ,values.bed , patient, practitioner, values.type )
			// alert("ok")
				// console.log(values.room)
			//    frappe.route_options = {'room': values.room , "type" : values.type  , "inp_doc" : inpatient_record  , "patient" : patient };
			// 	frappe.set_route('room');
			d.hide();
		}
	});
		d.fields_dict['room'].get_query = function(){
		return {
			filters: {
				'inpatient_occupancy': 1,
				'Type':"IPD"
			}
		};
	};

	d.fields_dict['bed'].get_query = function(){
		return {
			filters: {
				'inpatient_occupancy': 1,
				'service_unit_type':d.get_value('room'),
				"occupancy_status": "Vacant"
			}
		};
	};
	
	d.show();
}

function admit_p(inpatient_record, bed,patient_name, practitioner, type){
	frappe.call({
			
		method: 'his.api.admit.admit_p_bed',
		args:{
			
			"inp_doc" :inpatient_record,
			'service_unit': bed,
			"patient":patient_name,
			"practitioner":practitioner,
			'type' : type
			
			// "is_insurance" : data.ref_insturance
			// 'check_in': Date(),
			// 'expected_discharge': expected_discharge
		},
		callback: function(data) {
			frappe.msgprint("Admited")
			window.location.reload();

		}
	})

}


function add_inpatient(){
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'Patient',
				fieldname: 'patient',
				fieldtype: 'Link',
				options: 'Patient',
				change: function () {
                    frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Patient',
							name: d.get_value("patient")
						},
						callback: function (data) {
							if (data && data.message) {
								// Set the fetched patient name in the dialog
								d.set_value('patient_name', data.message.patient_name);
							}
						}
					});
                },
				reqd : 1,
				
			},
			{
				label: 'Patient Name',
				fieldname: 'patient_name',
				fieldtype: 'Data',
				reqd : 0,
				fetch_from : "patient.first_name",
				
			},

			// {
			// 	label: 'Patient Name',
			// 	fieldname: 'diagnosis',
			// 	fieldtype: 'Data',
			// 	fetch_from : "patient.full_name",
			// 	read_only : 1
				
			// },
			{
				label: 'Practitioner',
				fieldname: 'practitioner',
				fieldtype: 'Link',
				options: 'Healthcare Practitioner',
				reqd : 1,
				
			},
			{
				label: 'Diagnosis',
				fieldname: 'diagnosis',
				fieldtype: 'Data',
				
				reqd : 0,
				
			},
		
		 
		],
		primary_action_label: 'Submit',
		primary_action(values) {
			//   let practitioner = d.get_value("practitioner")
			//   let patient = d.get_value("patient")
			 
			  var args = {
				patient: patient = d.get_value("patient"),
				primary_practitioner :  d.get_value("practitioner"),
                diagnosis : d.get_value('diagnosis'),
				// admission_encounter: ""
                
				
			}
		
				frappe.call({
						method: "his.api.admission_schd.schedule_inpatient", //dotted path to server method
						args: {
							args: args
						},
						callback: function(r) {
							// code snippet
							// console.log(r)
						window.location.reload();
						 frappe.utils.play_sound("submit")
	
							frappe.show_alert({
						message:__('You have Refered Patient Succesfully'),
						indicator:'green',
						
					}, 5);
					
						}
	});
			d.hide();
	
		
		}
		
	});
	
	d.show();
				 
} 