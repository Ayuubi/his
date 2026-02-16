// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('History', {
	refresh: function(frm) {
		
		var htmlContent = "<div id = 'vitals' ></div>";

        // Set the HTML content to a field in the form
        frm.set_value('vitals', htmlContent);
		setupdata_table("PID-00265")

	}
});

let setupdata_table = function(patient){
	alert(patient)
	// patient = frappe.route_options.patient
	// let tbldata = []

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
this.table = new Tabulator("#vitals", {
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
}
