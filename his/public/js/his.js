frappe.provide('frappe.ui.form');

frappe.ui.form.PatientQuickEntryForm = class PatientQuickEntryForm extends frappe.ui.form.QuickEntryForm {

	constructor(doctype, after_insert, init_callback, doc, force) {
		super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	}

	render_dialog() {
		// if (frappe.user_roles.includes('HR Manager')) {
		// 	frm.set_df_property("is_employee" , "hidden" , 1)
		// }

		// filter fields for quick entry which are not wired in standard_fields
		let custom_fields = this.mandatory.filter(
			field => !this.get_standard_fields().map(field => field.fieldname).includes(field.fieldname)
		);

		this.mandatory = this.get_standard_fields();

		// preserve standard_fields order, splice custom fields after Patient name fields
		this.mandatory.splice(3, 0, ...custom_fields);

		super.render_dialog();
	}

	get_standard_fields() {




		return [
			{
				label: __('First Name'),
				fieldname: 'first_name',
				fieldtype: 'Data',
				hidden: 1
			},

			{
				label: __('Middle Name'),
				fieldname: 'middle_name',
				fieldtype: 'Data'
			},
			{
				label: __('last Name'),
				fieldname: 'last_name',
				fieldtype: 'Data'
			},
			{
				fieldtype: 'Section Break',
				collapsible: 0
			},
			{
				label: __('Gender'),
				fieldname: 'sex',
				fieldtype: 'Link',
				options: 'Gender'
			},

			{
				label: __('Blood Group'),
				fieldname: 'blood_group',
				fieldtype: 'Select',
				options: frappe.meta.get_docfield('Patient', 'blood_group').options
			},
			{
				fieldtype: 'Column Break'
			},
			{
				label: __('Birth Date'),
				fieldname: 'dob',
				fieldtype: 'Date'
			},
			{
				label: __('Identification Number (UID)'),
				fieldname: 'uid',
				fieldtype: 'Data'
			},
			{
				fieldtype: 'Section Break',
				label: __('Primary Contact'),
				collapsible: 1,
				hidden: 1
			},

			{
				label: __('Email Id'),
				fieldname: 'email',
				fieldtype: 'Data',
				options: 'Email'
			},
			{
				label: __('Invite as User'),
				fieldname: 'invite_user',
				fieldtype: 'Check',
				hidden: 1
			},
			{
				fieldtype: 'Column Break'
			},
			{
				label: __('Mobile Number'),
				fieldname: 'mobile',
				fieldtype: 'Data',
				options: 'Phone',
				hidden: 1
			},
			{
				fieldtype: 'Section Break',
				label: __('Primary Address'),
				collapsible: 1,
				hidden: 1
			},
			{
				label: __('Address Line 1'),
				fieldname: 'address_line1',
				fieldtype: 'Data'
			},
			{
				label: __('Address Line 2'),
				fieldname: 'address_line2',
				fieldtype: 'Data'
			},
			{
				label: __('ZIP Code'),
				fieldname: 'pincode',
				fieldtype: 'Data'
			},
			{
				fieldtype: 'Column Break'
			},
			{
				label: __('City'),
				fieldname: 'city',
				fieldtype: 'Data'
			},
			{
				label: __('State'),
				fieldname: 'state',
				fieldtype: 'Data'
			},
			{
				label: __('Country'),
				fieldname: 'country',
				fieldtype: 'Link',
				options: 'Country'
			}
		];
	}
}


frappe.ui.form.on('Clinical Procedure', {

	refresh: function (frm) {
		frm.set_query('item_code', 'consumable_items', function () {
			return {
				filters: {
					is_stock_item: 1
				}
			};
		});

		// if(frm.doc.status == 'Completed'){
		// 	var transfer_btn=  frm.add_custom_button(__("Transfer To Recovery"), function(){
		// 		frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want  Transfer </strong> to Recovery?`,
		// 		() => {
		// 			// action to perform if Yes is selected
		// 			frappe.call({
		// 				method: 'his.his.doctype.aneasthesia_sheet.aneasthesia_sheet.transfer',
		// 				args: {
		// 					service_unit:frm.doc.service_unit,
		// 					// docname: frm.doc.name,
		// 					patient: frm.doc.patient,
		// 					clinical_procedure : frm.doc.procedure_template,
		// 					practitioner : frm.doc.practitioner
		// 				},
		// 				callback: function(r) {
		// 					//frappe.msgprint(r)
		// 					console.log(r)
		// 					frappe.utils.play_sound("submit")
		// 					frappe.show_alert({
		// 						message:__('Patient Transfered Succesfully'),
		// 						indicator:'green',
		// 					}, 5);
		// 				}
		// 			});
		// 			},)
		// 		});
		// 		transfer_btn.addClass('btn-success');
		// }



	}
});



frappe.ui.form.on('Patient Encounter', {
	refresh(frm) {


		// your code here

	},

})

let select_lab_tests = function (frm) {
	var d = new frappe.ui.Dialog({
		'fields': [

			{ 'fieldname': 'ht', 'fieldtype': 'HTML' },

		],

		primary_action: function () {

			var test = []
			var labs = []
			$("input[name='lab']:checked").each(function () {
				if (!$(this).is(':checked')) {
					//  console.log($(this))
				}

				var selectedlabs = []
				cur_frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => selectedlabs.push(r.doc.lab_test_code))
				if (selectedlabs) {
					if (!selectedlabs.includes($(this).val())) {
						labs.push($(this).val())
						//   var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
						//     row.lab_test_code = $(this).val()

						//     refresh_field("lab_test_prescription");

						// test.push($(this).val());
					}
				}
				else {
					labs.push($(this).val())
					//  var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
					// row.lab_test_code = $(this).val()

					// refresh_field("lab_test_prescription");
				}

			});
			labs.forEach(lab => {
				var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
				row.lab_test_code = lab

				refresh_field("lab_test_prescription");
			})
			//   console.log(test)
			//   test = []

			//   var va = $('input:checked').map(function(i, e) {return e.value}).toArray();
			//   console.log(va)
			// //  var va = [];
			//     $(':checkbox:checked').each(function(i){
			//         va = []
			//       va.push($(this).val());
			//       console.log(va)
			//     });

			d.hide();


		}
	});

	var td = ''

	// frappe.client.get_list('Lab Test Template', {
	//      page_length:2,
	//     fields: ['lab_test_name' , 'department'],
	//     filters: {
	//         is_billable: 1,

	//     },
	// frappe.db.get_list('Lab Test Template', {
	//     fields: ['lab_test_name' , 'department'],
	//     filters: {
	//         is_billable: 1
	//     },
	//     limit : 1000
	// }).then(records => {
	//      var pr_selectedlabs= []
	//      cur_frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => pr_selectedlabs.push(r.doc.lab_test_code))

	//     records.forEach(r =>  { 
	//          if (pr_selectedlabs.includes(r.lab_test_name)){
	//               td += `${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}" checked>`
	//          }
	//          else{
	//                td += `${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}">`
	//          }

	//         var htm = td
	//         d.fields_dict.ht.$wrapper.html(htm);
	//     })
	// })

	var td = "";
	frappe.db
		.get_list("Lab Test Template", {
			fields: ["lab_test_name", "department", "profile"],
			filters: {
				is_billable: 1,
				disabled: 0
			},
			limit: 500,
			order_by: "department"
		})
		.then((records) => {
			records.forEach((r) => {
				// 	td += ` <span class ="text-primary h4" >${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}"></span>`

				// 		   var htm = td
				// 		   var row= `<div class="container">
				// 	 <div class="row">
				// 	   <div class="col-sm-6">
				// 		${td}
				// 	   </div>

				// 	 </div>
				//    </div>`

				const re_arr = [records];
				let row = ``;
				const groupByDept = records.reduce((group, dep) => {
					// console.log(group)
					const { profile } = dep;
					if (profile) {
						group[profile.toUpperCase().trim()] = group[profile.toUpperCase().trim()] || [];
						group[profile.toUpperCase().trim()].push(dep);
					}
					else {
						group[profile] = group[profile] || [];
						group[profile].push(dep);

					}

					return group;
				}, {});
				//   console.log(groupByDept);
				var pr_selectedlabs = []
				frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => pr_selectedlabs.push(r.doc.lab_test_code))

				Object.keys(groupByDept).forEach((key) => {
					// console.log(key, groupByDept[key]);
					let td = ``;
					groupByDept[key].forEach((test) => {
						if (pr_selectedlabs.includes(test.lab_test_name)) {
							td += `
      
      <div class="form-group form-check">
      
          <input type="checkbox"  class="form-check-input" name = "lab" id="${test.lab_test_name}"  value="${test.lab_test_name}" checked>
          <label class="form-check-label" >${test.lab_test_name}</label>
          
      </div>
      `;
						}
						else {
							td += `
      
            <div class="form-group form-check">
            
                <input type="checkbox"  class="form-check-input" name = "lab" id="${test.lab_test_name}"  value="${test.lab_test_name}">
                <label class="form-check-label" >${test.lab_test_name}</label>
                
            </div>
            `;

						}
					});
					row += `
      
      <div class = "col-md-2" id = "${key}" style = "border: 1px solid #000 ; margin: 5px">
          <h4> <strong> ${key}  </strong> </h4>
		  <div >
          ${td}
		  </div>
          
      </div>
      `;
				});
				var continaer = `<div class="container">
<div class="row">

 ${row}



</div>
</div>`;
				d.fields_dict.ht.$wrapper.html(continaer);
				d.$wrapper.find(".modal-dialog").css("max-width", "100%", "width", "100%");

				d.show();
				// d.$wrapper.find('.modal-content').css("width", "800px");
			})
		})
}


let select_imaging = function (frm) {
	var d = new frappe.ui.Dialog({
		'fields': [

			{ 'fieldname': 'ht', 'fieldtype': 'HTML' },

		],

		primary_action: function () {


			var test = []
			var images = []
			$("input[name='imaging']:checked").each(function () {
				if (!$(this).is(':checked')) {
					//  console.log($(this))
				}

				var selectedimaging = []
				cur_frm.get_field("radiology_prescription").grid.grid_rows.forEach(r => selectedimaging.push(r.doc.image))

				if (selectedimaging) {
					if (!selectedimaging.includes($(this).val())) {

						images.push($(this).val())
						//   var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
						//     row.lab_test_code = $(this).val()

						//     refresh_field("lab_test_prescription");

						// test.push($(this).val());
					}
				}
				else {
					images.push($(this).val())
					alert()
					//  var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
					// row.lab_test_code = $(this).val()

					// refresh_field("lab_test_prescription");
				}

			});
			images.forEach(img => {

				var row = frappe.model.add_child(cur_frm.doc, "Radiology Prescription", "radiology_prescription");
				row.image = img

				refresh_field("radiology_prescription");
			})
			//   console.log(test)
			//   test = []

			//   var va = $('input:checked').map(function(i, e) {return e.value}).toArray();
			//   console.log(va)
			// //  var va = [];
			//     $(':checkbox:checked').each(function(i){
			//         va = []
			//       va.push($(this).val());
			//       console.log(va)
			//     });

			d.hide();


		}
	});

	var td = ''




	var td = "";
	frappe.db
		.get_list("Radiology Template", {
			fields: ["template", "section"],
			filters: {
				is_billable: 1,
				disabled: 0
			},
			limit: 500,
			order_by: "section"
		})
		.then((records) => {
			records.forEach((r) => {
				// 	td += ` <span class ="text-primary h4" >${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}"></span>`

				// 		   var htm = td
				// 		   var row= `<div class="container">
				// 	 <div class="row">
				// 	   <div class="col-sm-6">
				// 		${td}
				// 	   </div>

				// 	 </div>
				//    </div>`

				const re_arr = [records];
				let row = ``;
				const groupByDept = records.reduce((group, dep) => {
					// console.log(group)
					const { section } = dep;
					if (section) {
						group[section.toUpperCase().trim()] = group[section.toUpperCase().trim()] || [];
						group[section.toUpperCase().trim()].push(dep);
					}
					else {
						group[section] = group[section] || [];
						group[section].push(dep);

					}

					return group;
				}, {});
				//   console.log(groupByDept);
				var pr_selectedimages = []
				frm.get_field("radiology_prescription").grid.grid_rows.forEach(r => pr_selectedimages.push(r.doc.image))

				Object.keys(groupByDept).forEach((key) => {
					// console.log(key, groupByDept[key]);
					let td = ``;
					groupByDept[key].forEach((test) => {
						if (pr_selectedimages.includes(test.template)) {
							td += `
      
      <div class="form-group form-check">
      
          <input type="checkbox"  class="form-check-input" name = "imaging" id="${test.template}"  value="${test.template}" checked>
          <label class="form-check-label" >${test.template}</label>
          
      </div>
      `;
						}
						else {
							td += `
      
            <div class="form-group form-check">
            
                <input type="checkbox"  class="form-check-input" name = "imaging" id="${test.template}"  value="${test.template}">
                <label class="form-check-label" >${test.template}</label>
                
            </div>
            `;

						}
					});
					row += `
      
      <div class = "col-md-2" id = "${key}">
          <h4>${key}</h4>
          ${td}
          
      </div>
      `;
				});
				var continaer = `<div class="container">
<div class="row">

 ${row}



</div>
</div>`;
				d.fields_dict.ht.$wrapper.html(continaer);
				d.$wrapper.find(".modal-dialog").css("max-width", "100%", "width", "100%");

				d.show();
				// d.$wrapper.find('.modal-content').css("width", "800px");
			})
		})
}



function get_history(patient, tab) {
	// alert(tab)

	let tbldata = []
	let lab_data = []

	frappe.call({
		method: "his.dashboard_and_history.p_history.get_p_histy", //dotted path to server method
		args: { "patient": patient },
		callback: function (r) {
			let columns = r.message[0][tab]
			let data = r.message[1][tab]
			//    console.log(data)
			if (tab == "labs") {
				// alert()
				data.forEach(element => {
					frappe.db.get_doc("Lab Result", element.name).then(r => {
						if (r.template == "CBC") {
							lab_data.push({ "date": r.date, "practitioner": r.practitioner, "test": "CBC" })

						}

						r.normal_test_items.forEach(result => {

							lab_data.push({ "date": r.date, "practitioner": r.practitioner, "test": result.test, "lab_test_name": result.lab_test_name, "lab_test_event": result.lab_test_event, "result_value": result.result_value, "normal_range": result.normal_range })

						})
					})

				});
				setTimeout(() => {

					columns = [{ title: "Date", field: "date" }, { title: "Practitioner", field: "practitioner" }, { title: "Test", field: "test" }, { title: "Test Name", field: "lab_test_name" }, { title: "Event", field: "lab_test_event" }, { title: "Result", field: "result_value" }, { title: "Normal Range", field: "normal_range" }]
					// setup_datatable(columns , lab_data , "date" , tab)
				}, 500);
			}

			else {
				if (columns) {

					setup_datatable(columns, data, "date", tab)
				}
				else {

					setup_datatable([], [], "date", tab)

				}
			}
		}
	})



	// 	frappe.call({
	// 		method: "his.api.vitals.get_vital", //dotted path to server method
	// 		args :{ "patient": patient
	// 			},
	// 		callback: function(r) {

	// 			tbldata = r.message





	// 		 let me = this
	// 		//  let fields = frappe.get_meta("Sales Order").fields
	// 			let columns = [
	// 			// {title:"ID", field:"name"},
	// 			// {title:"Patient", field:"customer"},
	// 			{title:"Date / Time", field:"modified"},
	// 			{title:"Temperature", field:"temperature"},
	// 			{title:"Pulse", field:"pulse"},
	// 			{title:"BP", field:"bp"},
	// 			{title:"Respiration", field:"respiratory_rate"},
	// 			{title:"SpO2", field:"spo"},
	// 			{title:"Height", field:"height"},
	// 			{title:"Weight", field:"weight"},
	// 			{title:"BMI", field:"bmi"},
	// 			{title:"Nurse", field:"owner"},

	// 			// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},

	// 		 ]



	//
	// this.table = new Tabulator("#vitals", {
	// 			// layout:"fitDataFill",
	// 			layout:"fitDataStretch",
	// 			//  layout:"fitColumns",
	// 			// responsiveLayout:"collapse",
	// 			 rowHeight:30, 
	// 			//  selectable:true,
	// 			//  dataTree:true,
	// 			//  dataTreeStartExpanded:true,
	// 			 groupStartOpen:false,
	// 			 printAsHtml:true,
	// 			//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
	// 			//  printFooter:"<h2>Example Table Footer<h2>",
	// 			 // groupBy:"customer",
	// 			 groupHeader:function(value, count, data, group){
	// 				 //value - the value all members of this group share
	// 				 //count - the number of rows in this group
	// 				 //data - an array of all the row data objects in this group
	// 				 //group - the group component for the group

	// 				 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
	// 			 },
	// 			 groupToggleElement:"header",
	// 			//  groupBy:groupbyD.length >0 ? groupbyD : "",
	// 			 textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

	// 			 columns: columns,



	// 			 data: new_data
	// 		 });



}

function transfer_balance(from_c, amount) {
	// alert(patient , patient_name)
	let d = new frappe.ui.Dialog({
		title: 'Receipt details',
		fields: [
			{
				label: 'Posting Date',
				fieldname: 'posting_date',
				fieldtype: 'Date',
				// default: get_today(),
				default: frappe.datetime.get_today(),
				reqd: 1
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
				label: 'From',
				fieldname: 'from_c',
				fieldtype: 'Link',
				options: "Customer",
				default: from_c,
				read_only: 1,
				reqd: 1
			},
			{
				label: 'To',
				fieldname: 'to',
				fieldtype: 'Link',
				options: "Customer",
				reqd: 1
			},
			{
				label: 'Amount',
				fieldname: 'amount',
				fieldtype: 'Currency',
				default: amount,
				reqd: 1
			}

		],
		primary_action_label: 'Submit',
		primary_action(values) {


			frappe.call({
				method: "his.api.journal_entry.transfer_balance",
				args: {
					posting_date: values.posting_date,
					amount: values.amount,
					from_c: values.from_c,
					//   company: frappe.user_defaults.company,
					to: values.to,

				},
				callback: function (r) {

					frm.reload_doc();

					frappe.utils.play_sound("submit")

					frappe.show_alert({
						message: __('Reciepted Succesfully'),
						indicator: 'green',

					}, 5);
				}
			});
			d.hide();
		}
	});

	d.show();

}




function consoleerp_hi(patient, patient_name, is_curr = false) {
	if (is_curr) {
		get_history(patient, 'vitals_cur')
	}
	else {
		get_history(patient, 'visits')

	}

	let modal = ''
	let d = new frappe.ui.Dialog({
		title: `History of ${patient_name}`,
		fields: [
			{
				label: '',
				fieldname: 'model_html',
				fieldtype: 'HTML'
			},

		],
		primary_action_label: 'Close',
		primary_action(values) {
			// console.log(values);
			d.hide();
			window.location.reload()
		}
	});
	let html = `
	
	`
	if (!is_curr) {

		html = `
	<section class="customer">
	<div class="customer__head">
	  <span onclick = "get_history('${patient}' ,'visits')">Visits</span>
	  <span onclick = "get_history('${patient}' ,'vitals')">Vitals</span>
	  <span onclick =  "get_history('${patient}' ,'drug_pres')">Medical Prescription</span>
	  <span onclick =  "get_history('${patient}' ,'labs')">Lab Test  </span>
   
	  <span onclick =  "get_history('${patient}' ,'imaging')">Imaging</span>
	  <span onclick =  "get_history('${patient}' ,'comp')">History</span>
	 
	</div>
  </section>

	`



		// modal = `
		// <!-- Modal Fullscreen xl -->
		// <div class="modal modal-fullscreen-xl" id="modal-fullscreen-xl" tabindex="-1" role="dialog" aria-hidden="true">
		//   <div class="modal-dialog mdia" role="document">
		//     <div class="modal-content mdcont">
		//       <div class="modal-header">
		//         <h5 class="modal-title">Patient History of ${patient_name}</h5>
		//         <button type="button" class="close" data-dismiss="modal" aria-label="Close">
		//           <span aria-hidden="true">&times;</span>
		//         </button>
		//       </div>
		//       <div class="modal-body">

		// 	  	 <section class="customer">
		// 	 <div class="customer__head">
		// 	   <span onclick = "get_history('${patient}' ,'visits')">Visits</span>
		// 	   <span onclick = "get_history('${patient}' ,'vitals')">Vitals</span>
		// 	   <span onclick =  "get_history('${patient}' ,'med')">Medical Prescription</span>
		// 	   <span onclick =  "get_history('${patient}' ,'labs')">Lab Test  </span>

		// 	   <span onclick =  "get_history('${patient}' ,'imaging')">Imaging</span>
		// 	   <span onclick =  "get_history('${patient}' ,'comp')">Complaints</span>
		// 	   <span onclick =  "get_history('${patient}' ,'diag')">Diagnosis</span>
		// 	 </div>
		//    </section>
		//    <section class="viewCustomer">
		//    <div id="history" style = "min-width : 100%"></div>
		//  </section>

		//          </div>
		//       <div class="modal-footer">
		//         <button type="button" class="btn btn-danger" data-dismiss="modal">Close</button>

		//       </div>
		//     </div>
		//   </div>
		// </div>
		// `
	}
	else {
		html = `
	
	<section class="customer"> 
	<div class="customer__head">
	<span onclick =  "get_history('${patient}' ,'vitals_cur')">Vitals</span>
	  <span onclick = "get_history('${patient}' ,'labs_today')">Lab Test</span>
	  <span onclick = "get_history('${patient}' ,'images')">Imaging</span>
	 
	 
	</div>
  </section>

	`



		// modal =  `
		// <!-- Modal Fullscreen xl -->
		// <div class="modal modal-fullscreen-xl" id="modal-fullscreen-xl" tabindex="-1" role="dialog" aria-hidden="true">
		//   <div class="modal-dialog mdia" role="document">
		// 	<div class="modal-content mdcont">
		// 	  <div class="modal-header">
		// 		<h5 class="modal-title">Patient History of ${patient_name}</h5>
		// 		<button type="button" class="close" data-dismiss="modal" aria-label="Close">
		// 		  <span aria-hidden="true">&times;</span>
		// 		</button>
		// 	  </div>
		// 	  <div class="modal-body">

		// 		   <section class="customer"> 
		// 	 <div class="customer__head">
		// 	 <span onclick =  "get_history('${patient}' ,'vitals_cur')">Vitals</span>
		// 	   <span onclick = "get_history('${patient}' ,'labs_today')">Lab Test</span>
		// 	   <span onclick = "get_history('${patient}' ,'images')">Imaging</span>


		// 	 </div>
		//    </section>
		//    <section class="viewCustomer">
		//    <div id="history" style = "min-width : 100%"></div>
		//  </section>

		// 		 </div>
		// 	  <div class="modal-footer">
		// 		<button type="button" class="btn btn-danger" data-dismiss="modal">Close</button>

		// 	  </div>
		// 	</div>
		//   </div>
		// </div>
		// `
	}
	html += `

<section class="viewCustomer">
	<div id="history" style = "min-width : 100%"></div>
  </section>
`

	d.show();
	d.set_value("model_html", html)
	d.$wrapper.find(".modal-dialog").css("max-width", "100%", "width", "100%", "height", "700px");
	$("#modal-fullscreen-xl").remove();
	$('.page-wrapper').append(modal)
	$('#modal-fullscreen-xl').modal('hide');
	$('#modal-fullscreen-xl').modal('show');
	// alert(_from)
	// alert(to)
	// frappe.set_route('query-report', 'Purchase Items', { supplier: data , from_date : _from , to_date : to})
}




function sales_items(data, _from, to) {
	// alert(data)
	// alert(_from)
	// alert(to)
	frappe.set_route('query-report', 'Sales Items', { customer: data, from_date: _from, to_date: to })
}


function statement(party) {
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'From Date',
				fieldname: 'from_date',
				fieldtype: 'Date',
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				label: 'To Date',
				fieldname: 'to_date',
				fieldtype: 'Date',
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				fieldname: "cost_center",
				label: __("Source"),
				fieldtype: "Link",
				hidden: 0,
				options: "Cost Center"
			},

		],
		primary_action_label: 'Submit',
		primary_action(values) {
			frappe.call({
				method: "his.api.api.get_report_content",
				args: {

					company: frappe.defaults.get_default('Company'),
					customer_name: party,
					from_date: values.from_date,
					to_date: values.to_date,
					cost_center: values.cost_center
				},
				callback: function (r) {

					var x = window.open();
					x.document.open().write(r.message);
				}
			});
			d.hide();
		}
	});

	d.show();

	// alert(party)
	// frappe.new_doc("Customer Statements Sender"  ,{ customer: party } )
	// frappe.set_route('Form', 'Customer Setatements Sender',"Customer Statements Sender" ,{ customer: party })

}

function account_statement(account) {
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'From Date',
				fieldname: 'from_date',
				fieldtype: 'Date',
				reqd: 1,
				default: frappe.datetime.get_today()
			},
			{
				label: 'To Date',
				fieldname: 'to_date',
				fieldtype: 'Date',
				reqd: 1,
				default: frappe.datetime.get_today()
			},
		

		],
		primary_action_label: 'Submit',
		primary_action(values) {
			frappe.call({
				method: "his.api.api.account_statement",
				args: {

					company: frappe.defaults.get_default('Company'),
					account: account,
					from_date: values.from_date,
					to_date: values.to_date,
					cost_center: values.cost_center
				},
				callback: function (r) {

					var x = window.open();
					x.document.open().write(r.message);
				}
			});
			d.hide();
		}
	});

	d.show();

	// alert(party)
	// frappe.new_doc("Customer Statements Sender"  ,{ customer: party } )
	// frappe.set_route('Form', 'Customer Setatements Sender',"Customer Statements Sender" ,{ customer: party })

}

let buttons = document.querySelectorAll(".customer__head span");
// buttons.forEach((button) => {
//     button.addEventListener("click", handleClick);
//   });
//   buttons[0].addEventListener("click", handleDetail);
//   buttons[1].addEventListener("click", handleInvoices);
//   buttons[2].addEventListener("click", handleLogs);

//   buttons[0].classList.add("active");

function get_history(patient, tab) {
	// alert(tab)
	// let columns = [
	// 	{title:"ID", field:"name"},
	// 	// {title:"Patient", field:"customer"},
	// 	{title:"Patient Name", field:"patient_name"},
	// 	{title:"Date", field:"transaction_date"}
	// ]
	// let new_data = [
	// 	{"name" : "9999" ,"patient_name" : "Cali" , "transaction_date" : "2023-2-2" },

	// ]
	// alert("ok ok")
	let lab_data = []
	frappe.call({
		method: "his.dashboard_and_history.p_history.get_p_histy", //dotted path to server method
		args: { "patient": patient },
		callback: function (r) {
			let columns = r.message[0][tab]
			let data = r.message[1][tab]

			if (tab == "labs") {
				// alert()
				data.forEach(element => {
					frappe.db.get_doc("Lab Result", element.name).then(r => {
						if (r.template == "CBC") {
							lab_data.push({ "date": r.date, "practitioner": r.practitioner, "test": "CBC" })

						}
						// console.log(r)
						r.normal_test_items.forEach(result => {
							// console.log("this CBC normal "+  result.normal_range)
							lab_data.push({ "date": r.date, "practitioner": r.practitioner, "test": result.test, "lab_test_name": result.lab_test_name, "lab_test_event": result.lab_test_event, "result_value": result.result_value, "normal_range": result.normal_range })

						})
					})

				});
				setTimeout(() => {
					// console.log(lab_data)
					// console.log("this Others normal "+  result.normal_range)
					columns = [{ title: "Date", field: "date" }, { title: "Practitioner", field: "practitioner" }, { title: "Test", field: "test" }, { title: "Test Name", field: "lab_test_name" }, { title: "Event", field: "lab_test_event" }, { title: "Result", field: "result_value" }, , { title: "Normal Range", field: "normal_range" }]
					setup_datatable(columns, lab_data, "date")
					// this.table = new Tabulator("#labs", {
					// 	// layout:"fitDataFill",
					// 	layout:"fitDataFill",
					// 	//  layout:"fitColumns",
					// 	// responsiveLayout:"collapse",
					// 	 rowHeight:30, 
					// 	 placeholder:"No Data Available",
					// 	//  selectable:true,
					// 	//  dataTree:true,
					// 	//  dataTreeStartExpanded:true,
					// 	 groupStartOpen:false,
					// 	 printAsHtml:true,
					// 	//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
					// 	 printFooter:"<h2>Example Table Footer<h2>",
					// 	 groupBy:"date",
					// 	 groupHeader:function(value, count, data, group){
					// 		 //value - the value all members of this group share
					// 		 //count - the number of rows in this group
					// 		 //data - an array of all the row data objects in this group
					// 		 //group - the group component for the group
					// 	 // console.log(group)
					// 		 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
					// 	 },
					// 	 groupToggleElement:"header",
					// 	//  groupBy:groupbyD.length >0 ? groupbyD : "",
					// 	//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

					// 	 columns: columns,

					// 	 // [
					// 	 // 	{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"center", headerSort:false, cellClick:function(e, cell){
					// 	 // 		cell.getRow().toggleSelect();
					// 	 // 	  }},
					// 	 // 	{
					// 	 // 		title:"Name", field:"name", width:200,
					// 	 // 	},
					// 	 // 	{title:"Group", field:"item_group", width:200},
					// 	 // ],
					// 	 // [
					// 	 // {title:"Name", field:"name" , formatter:"link" , formatterParams:{
					// 	 // 	labelField:"name",
					// 	 // 	urlPrefix:`/app/${doct}/`,

					// 	 // }},
					// 	 // {title:"Customer", field:"customer" },
					// 	 // {title:"Total", field:"net_total" , bottomCalc:"sum",},

					// 	 // ],

					// 	 data: data
					//  });
				}, 1000);
			}
			else if (tab == "vitals") {
				this.table = new Tabulator("#vitals", {
					// layout:"fitDataFill",
					layout: "fitDataFill",
					//  layout:"fitColumns",
					// responsiveLayout:"collapse",
					rowHeight: 30,
					placeholder: "No Data Available",
					//  selectable:true,
					//  dataTree:true,
					//  dataTreeStartExpanded:true,
					groupStartOpen: false,
					printAsHtml: true,
					//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
					printFooter: "<h2>Example Table Footer<h2>",
					groupBy: "date",
					groupHeader: function (value, count, data, group) {
						//value - the value all members of this group share
						//count - the number of rows in this group
						//data - an array of all the row data objects in this group
						//group - the group component for the group
						// console.log(group)
						return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
					},
					groupToggleElement: "header",
					//  groupBy:groupbyD.length >0 ? groupbyD : "",
					//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

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

					data: data
				});
			}
			else {
				if (columns) {
					setup_datatable(columns, data)
				}
				else {
					setup_datatable([], [])

				}
			}
		}
	})


}


function setup_datatable(columns, data, group) {
	// alert()
	groupBy = []
	if (group) {
		groupBy.push(group)
	}

	this.table = new Tabulator("#labs", {
		// layout:"fitDataFill",
		layout: "fitDataFill",
		//  layout:"fitColumns",
		// responsiveLayout:"collapse",
		rowHeight: 30,
		placeholder: "No Data Available",
		//  selectable:true,
		//  dataTree:true,
		//  dataTreeStartExpanded:true,
		groupStartOpen: false,
		printAsHtml: true,
		//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
		printFooter: "<h2>Example Table Footer<h2>",
		groupBy: "date",
		groupHeader: function (value, count, data, group) {
			//value - the value all members of this group share
			//count - the number of rows in this group
			//data - an array of all the row data objects in this group
			//group - the group component for the group
			// console.log(group)
			return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
		},
		groupToggleElement: "header",
		//  groupBy:groupbyD.length >0 ? groupbyD : "",
		//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

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

		data: data
	});

	// 

	this.table = new Tabulator("#history", {
		// layout:"fitDataFill",
		layout: "fitDataFill",
		//  layout:"fitColumns",
		// responsiveLayout:"collapse",
		rowHeight: 30,
		placeholder: "No Data Available",
		//  selectable:true,
		//  dataTree:true,
		//  dataTreeStartExpanded:true,
		groupStartOpen: false,
		printAsHtml: true,
		//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
		printFooter: "<h2>Example Table Footer<h2>",
		groupBy: "date",
		groupHeader: function (value, count, data, group) {
			//value - the value all members of this group share
			//count - the number of rows in this group
			//data - an array of all the row data objects in this group
			//group - the group component for the group
			// console.log(group)
			return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
		},
		groupToggleElement: "header",
		//  groupBy:groupbyD.length >0 ? groupbyD : "",
		//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

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

		data: data
	});
}

function receipt(party, outstanding, vat) {

	// 	balance= 0
	// 	frappe.call({
	// 		method: "erpnext.accounts.utils.get_balance_on",
	// 		args: {date: get_today(), party_type: 'Customer', party: party},
	// 		callback: function(r) {
	// // 			doc.outstanding_balance = format_currency(r.message, erpnext.get_currency(doc.company));
	//            balance= r.message
	// // 			refresh_field('outstanding_balance', 'accounts');
	// 		}
	// 		})

	let d = new frappe.ui.Dialog({
		title: 'Receipt details',
		fields: [
			{
				label: 'Posting Date',
				fieldname: 'posting_date',
				fieldtype: 'Date',
				reqd: 1,
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
				label: 'Balance',
				fieldname: 'balance',
				fieldtype: 'Currency',
				default: outstanding,
				read_only: 1
			},

			{
				label: 'Balance With Vat',
				fieldname: 'vat',
				fieldtype: 'Currency',
				default: vat,
				read_only: 1,
				hidden: 1
			},
			{
				label: 'Paid Amount',
				fieldname: 'paid_amount',
				fieldtype: 'Currency',
				reqd: 1
				
			},
			{
				label: 'Discount',
				fieldname: 'discount',
				fieldtype: 'Currency',
				default: 0,
				read_only: 0,
				hidden: 0
			},
			{
				label: 'Remark',
				fieldname: 'remark',
				fieldtype: 'Data',
				reqd: 0
			},
		],
		primary_action_label: 'Submit',
		primary_action(values) {
			if ((values.discount + values.paid_amount) > outstanding) {

				frappe.throw(
					'Lacagta aad ka qabaneyso bukaankan waxa ay kabadan tahay lacagta lagu leeyahay lamana ogola overpayments.',
					// function () {
					// 	frappe.call({
					// 		method: "his.api.create_p_e.payment_re",
					// 		args: {


					// 			party: party,
					// 			posting_date: values.posting_date,
					// 			paid_amount: values.paid_amount,
					// 			discount: values.discount,
					// 			remark: values.remark,
					// 			company: frappe.user_defaults.company,
					// 			party_account: values.party_account,

					// 		},
					// 		callback: function (r) {
					// 		}
					// 	});
					// },
					function () {
						show_alert('Overpayments Not allowed!')
					}
				)
			}
			else {
				frappe.call({
					method: "his.api.create_p_e.payment_re",
					args: {


						party: party,
						posting_date: values.posting_date,
						paid_amount: values.paid_amount,
						discount: values.discount,
						remark: values.remark,
						company: frappe.user_defaults.company,
						party_account: values.party_account,

					},
					callback: function (r) {
					}
				});
			}



			d.hide();

		}
	});

	d.show();
}

function statementemployee(party) {
	

	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'From Date',
				fieldname: 'from_date',
				fieldtype: 'Date',
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				label: 'To Date',
				fieldname: 'to_date',
				fieldtype: 'Date',
				reqd: 1
			},

		],
		primary_action_label: 'Submit',
		primary_action(values) {
			frappe.call({
				method: "his.api.api.get_report_content_3",
				args: {

					company: frappe.defaults.get_default('Company'),
					employee_name: party,
					from_date: values.from_date,
					to_date: values.to_date,
					// account: account
				},
				callback: function (r) {

					var x = window.open();
					x.document.open().write(r.message);
				}
			});
			d.hide();
		}
	});

	d.show();
	// alert(party)
	// frappe.new_doc("Customer Statements Sender"  ,{ customer: party } )
	// frappe.set_route('Form', 'Customer Setatements Sender',"Customer Statements Sender" ,{ customer: party })

}

function statementsuppier(party) {
	let d = new frappe.ui.Dialog({
		title: 'Enter details',
		fields: [
			{
				label: 'From Date',
				fieldname: 'from_date',
				fieldtype: 'Date',
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				label: 'To Date',
				fieldname: 'to_date',
				fieldtype: 'Date',
				reqd: 1
			},

		],
		primary_action_label: 'Submit',
		primary_action(values) {
			frappe.call({
				method: "his.api.api.get_report_content_2",
				args: {

					company: frappe.defaults.get_default('Company'),
					supplier_name: party,
					from_date: values.from_date,
					to_date: values.to_date
				},
				callback: function (r) {

					var x = window.open();
					x.document.open().write(r.message);
				}
			});
			d.hide();
		}
	});

	d.show();
	// alert(party)
	// frappe.new_doc("Customer Statements Sender"  ,{ customer: party } )
	// frappe.set_route('Form', 'Customer Setatements Sender',"Customer Statements Sender" ,{ customer: party })

}

update_child_item = function (opts) {
	const frm = opts.frm;
	const cannot_add_row = (typeof opts.cannot_add_row === 'undefined') ? true : opts.cannot_add_row;
	const child_docname = (typeof opts.cannot_add_row === 'undefined') ? "items" : opts.child_docname;
	const child_meta = frappe.get_meta(`${frm.doc.doctype} Item`);
	const get_precision = (fieldname) => child_meta.fields.find(f => f.fieldname == fieldname).precision;

	this.data = frm.doc[opts.child_docname].map((d) => {
		return {
			"docname": d.name,
			"name": d.name,
			"item_code": d.item_code,
			"delivery_date": d.delivery_date,
			"schedule_date": d.schedule_date,
			"conversion_factor": d.conversion_factor,
			"qty": d.qty,
			"rate": d.rate,
			"uom": d.uom
		}
	});

	const fields = [{
		fieldtype: 'Data',
		fieldname: "docname",
		read_only: 1,
		hidden: 1,
	}, {
		fieldtype: 'Link',
		fieldname: "item_code",
		options: 'Item',
		in_list_view: 1,
		read_only: 0,
		disabled: 0,
		label: __('Item Code'),
		get_query: function () {
			let filters;
			if (frm.doc.doctype == 'Sales Order') {
				filters = { "is_sales_item": 1 };
			} else if (frm.doc.doctype == 'Purchase Order') {
				if (frm.doc.is_subcontracted) {
					if (frm.doc.is_old_subcontracting_flow) {
						filters = { "is_sub_contracted_item": 1 };
					} else {
						filters = { "is_stock_item": 0 };
					}
				} else {
					filters = { "is_purchase_item": 1 };
				}
			}
			return {
				query: "erpnext.controllers.queries.item_query",
				filters: filters
			};
		}
	}, {
		fieldtype: 'Link',
		fieldname: 'uom',
		options: 'UOM',
		read_only: 0,
		label: __('UOM'),
		reqd: 1,
		onchange: function () {
			frappe.call({
				method: "erpnext.stock.get_item_details.get_conversion_factor",
				args: { item_code: this.doc.item_code, uom: this.value },
				callback: r => {
					if (!r.exc) {
						if (this.doc.conversion_factor == r.message.conversion_factor) return;

						const docname = this.doc.docname;
						dialog.fields_dict.trans_items.df.data.some(doc => {
							if (doc.docname == docname) {
								doc.conversion_factor = r.message.conversion_factor;
								dialog.fields_dict.trans_items.grid.refresh();
								return true;
							}
						})
					}
				}
			});
		}
	}, {
		fieldtype: 'Float',
		fieldname: "qty",
		default: 0,
		read_only: 0,
		in_list_view: 1,
		label: __('Qty'),
		precision: get_precision("qty")
	}, {
		fieldtype: 'Currency',
		fieldname: "rate",
		options: "currency",
		default: 0,
		read_only: 0,
		in_list_view: 1,
		label: __('Rate'),
		precision: get_precision("rate")
	}];

	if (frm.doc.doctype == 'Sales Order' || frm.doc.doctype == 'Purchase Order') {
		fields.splice(2, 0, {
			fieldtype: 'Date',
			fieldname: frm.doc.doctype == 'Sales Order' ? "delivery_date" : "schedule_date",
			in_list_view: 1,
			label: frm.doc.doctype == 'Sales Order' ? __("Delivery Date") : __("Reqd by date"),
			reqd: 1
		})
		fields.splice(3, 0, {
			fieldtype: 'Float',
			fieldname: "conversion_factor",
			in_list_view: 1,
			label: __("Conversion Factor"),
			precision: get_precision('conversion_factor')
		})
	}

	new frappe.ui.Dialog({
		title: __("Update Items"),
		fields: [
			{
				fieldname: "trans_items",
				fieldtype: "Table",
				label: "Items",
				cannot_add_rows: cannot_add_row,
				in_place_edit: false,
				reqd: 1,
				data: this.data,
				get_data: () => {
					return this.data;
				},

				fields: fields
			},
			// {
			// 	label: 'Customer',
			// 	fieldname: 'customer',
			// 	fieldtype: 'Data',
			// 	cust: frm.doc.customer,
			// 	read_only: 1
			// },
			{
				label: 'Paid Amount',
				fieldname: 'total',
				fieldtype: 'Currency',
				reqd: 1


			},
			{
				label: 'Discount',
				fieldname: 'discount_amount',
				fieldtype: 'Currency',


			},
		],
		primary_action: function (values) {
			const trans_items = this.get_values()["trans_items"].filter((item) => !!item.item_code);
			frappe.call({
				// method: 'erpnext.controllers.accounts_controller.update_child_qty_rate',
				method: "his.api.create_inv.make_ipd_sales_invoice",
				freeze: true,
				// args: {
				// 	'parent_doctype': frm.doc.doctype,
				// 	'trans_items': trans_items,
				// 	'parent_doctype_name': frm.doc.name,
				// 	'child_docname': child_docname
				// },
				args: {
					dt: "IPD Order",
					doc_name: opts.doc_name,
					paid_amount: values.total,
					discount: values.discount_amount,
					trans_items: values.trans_items,
					// company: frappe.defaults.get_default('Company'),
					// party_account: values.party_account,
				},
				callback: function () {
					frm.reload_doc();
				}
			});
			this.hide();
			refresh_field("items");
		},
		primary_action_label: __('Update')
	}).show();
}

function renew(name) {
	alert("Renew")
	frappe.call({
		method: "his.api.Que_to_make_sales_invove.renew",
		args: {


			name: name,


		},
		callback: function (r) {
		}
	});
}
