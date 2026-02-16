frappe.pages['view-vital-signs'].on_page_load = function(wrapper) {
	new EmOrder(wrapper)
}

EmOrder = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "VITAL SIGNS",
				single_column : true
			});
			this.groupbyD = []
			this.make()
			this.setupdata_table()
			// this.create_btns()
			let myf = this
		
			// this.make_grouping_btn()
			// this.grouping_cols()
		},
		make:function(){
			let me = this
   		
			$(frappe.render_template(frappe.ipd_page.body, me)).appendTo(me.page.main)
			let myself = this
			// let tbldata = []
			let emp = this.page.add_field({
				label: 'Patient',
				fieldtype: 'Link',
				fieldname: 'patient',
				options: "Patient",
			
				change() {
				
					let empl = emp.get_value()
					myself.setupdata_table(empl)
			
				}
			});
			let patient_name = this.page.add_field({
				label: 'Patient Name',
				fieldtype: 'Data',
				fieldname: 'patient_name',
				read_only : 1
			
			});
			alert()
			emp.set_value(frappe.route_options.patient)
			patient_name.set_value(frappe.route_options.patient_name)

		
		},
		// create_btns:function(){
		

			// let emp = this.page.add_field({
			// 	label: 'Patient',
			// 	fieldtype: 'Link',
			// 	fieldname: 'patient',
			// 	options: "Patient",
			
			// 	change() {
				
			// 		let empl = emp.get_value()
			// 		ready(empl)
			// 		// console.log(empl)
			// 		// create_clander(empl)
			// 	}
			// });
		// },
	
		setupdata_table : function(patient){
			// patient = frappe.route_options.patient
			// let tbldata = []
			this.get_vitals(patient)

		},


		get_vitals(patient){
			frappe.call({
				method: "his.api.vitals.get_vital", //dotted path to server method
				args :{ "patient": patient
					},
				callback: function(r) {
					// code snippet
					// $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
					tbldata = r.message
				// console.log(r)
		   
		
					let doct ='Sales Order'.replace(' ' , '-').toLowerCase()
				
				 let me = this
				//  let fields = frappe.get_meta("Sales Order").fields
					 columns = [
					// {title:"ID", field:"name"},
					// {title:"Patient", field:"customer"},
					{title:"Date / Time", field:"modified"},
					{title:"Temperature", field:"temperature"},
					{title:"Pulse", field:"pulse"},
					{title:"BP", field:"bp"},
					{title:"Respiration", field:"respiratory_rate"},
					{title:"SpO2", field:"spo"},
					{title:"Height", field:"height"},
					{title:"Weight", field:"weight"},
					{title:"BMI", field:"bmi"},
					{title:"Nurse", field:"owner"},
					
					// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
					
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
				let list_btns = frappe.listview_settings[`Sales Invoice`]
				// tbldata = tbldata[0]['action'] = "Button"
				let new_data = []
				// if(list_btns)
		
				tbldata.forEach(row => {
					// console.log(row.status)
					if(row.status === "To Deliver and Bill"){
						row.status = "To Bill"
		
					}
					let btnhml = ''
					if(row.status !== "Draft" && row.status !== "Cancelled" && row.status !== "Completed"){
					
					btnhml += `
					<button class='btn btn-primary ml-2' onclick = "cash_sales('${row.name}')"> Cash</button>
					<button class='btn btn-danger ml-2' onclick = "credit_sales('${row.name}')"> Credit</button>
					
					`
					}
					else{
						btnhml += `
						<div style="height: 100px; background-color: rgba(255,255,250);"> </div>
				
					
					`
		
					}
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
					new_data.push(row)
				})
				// console.log(columns)
		this.table = new Tabulator("#emorder", {
					// layout:"fitDataFill",
					layout:"fitDataStretch",
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
					 
					 data: new_data
				 });
				 
				 //  table.getSelectedData(); 
				 let row = this
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
				}
			
		});
		},
		grouping_cols:function(){
		
			let me = this
			$('.groupcheck').change(function() {
				// alert ("The element with id " + this.value + " changed.");
				let value = this.value
				if(this.checked) {
				groupbyD.push(this.value)
				}
				else{
					groupbyD = groupbyD.filter(function(e) { return e !== value })
				}
				me.setupdata_table(true);
				// setup_datatable()
				
			});
	
		   
		},

 make_sales_invoice : function(source_name) {
	// alert("ok ok")
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
let emrbody = `

<div class="container">
<div class="row">

<div id="emorder"  style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.ipd_page = {
	body : emrbody
}
formatter = function(cell, formatterParams, onRendered){
			return frappe.datetime.prettyDate(cell.getValue() , 1)
		}
