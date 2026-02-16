frappe.pages['maternity'].on_page_load = function(wrapper) {
	new IPD(wrapper)
}

IPD = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Maternity",
				single_column : true
			});
			this.groupbyD = []
			this.currDate =  frappe.datetime.get_today()
			this.make()
			this.setupdata_table()
			this.make_grouping_btn()
			let myf = this
			frappe.realtime.on('inp_update', (data) => {
				// alert("in realtime")
				myf.setupdata_table()
					})
			// this.grouping_cols()
		},
		make:function(){

		
			let me = this
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
   		
   		
			$(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main)




		
		},

		setupdata_table : function(gr_ref){
			let currdate = this.currDate
		let tbldata = []
		frappe.db.get_list('Inpatient Record', {
			fields: ['patient','patient_name', 'age', 'dob', 'type','room' , 'bed' , 'admitted_datetime' , 'medical_department', 'admission_practitioner' , 'diagnose'],
			filters: {
				"status": 'Admitted',
				"type": "Maternity"
			},
			limit : 1000
		}).then(r => {
			// console.log(r)
			// calculate age for each patient
			r.forEach(row => {
				if (row.dob) {
					row.age = calculate_age(row.dob);
				} else {
					row.age = "Unknown";
				}
			});
            // code snippet
            // $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			tbldata = r
        // console.log(r)
   

			// let doct ='Sales Order'.replace(' ' , '-').toLowerCase()
		
		 let me = this
		//  let fields = frappe.get_meta("Sales Order").fields
		 	columns = [
			// {title:"ID", field:"name"},
			// {title:"Patient", field:"customer"},
			{title:"No", field:"id", formatter:"rownum"},
			{title:"PID", field:"patient" ,  headerFilter:"input"},
			{title:"Patient Name", field:"patient_name" ,  headerFilter:"input"},
			{title:"Age", field:"age" ,  headerFilter:"input"},
			{title:"Type", field:"type" ,  headerFilter:"input"},
			{title:"Date", field:"admitted_datetime" ,  headerFilter:"input"},
			{title:"Duration", field:"duration" ,  headerFilter:"input" , formatter:durationformatter},
			{title:"Doctor Name", field:"admission_practitioner" ,  headerFilter:"input",},
			{title:"Medical Department", field:"medical_department" ,  headerFilter:"input",},
			{title:"Room", field:"room" ,  headerFilter:"input",},
			
			{title:"Bed", field:"bed" ,  headerFilter:"input",},
			// {title:"Status", field:"inpatient_status" ,  headerFilter:"input",},
			{title:"Diagnosis", field:"diagnose" ,  headerFilter:"input",},
			

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
		// console.log(tbldata)
		tbldata.forEach(row => {
			// console.log(row.status)
			// if(row.status === "To Deliver and Bill"){
			// 	row.status = "To Bill"

			// }
			// console.log("this is ",row.per_billed)
			let btnhml = ''
			// if(row.status !== "Draft" && row.status !== "Cancelled" && row.status!= "Completed" ){
			
			// btnhml += `
			// <button class='btn btn-primary ml-2' onclick = "get_history('${row.patient }' , '${row.patient_name}')"> History</button>
		
			// <button class='btn btn-danger ml-2' onclick = "credit_sales('${row.name}')"> Ready To Surgery</button>
			
			// `
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
			row['duration']  = row.admitted_datetime
			new_data.push(row)
		})
		// console.log(columns)
this.table = new Tabulator("#met", {
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
		//  let row = this
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
		let row = this
		this.table.on("rowClick", function(e ,rows){
		   let target = e.target.nodeName
		   //  let selectedRows = row.table.getSelectedRows(); 
			// console.log(rows._row.data)
		   //  console.log(row.table.getSelectedData())
		   //  row.toggle_actions_menu_button(row.table.getSelectedData().length > 0);
		  
		frappe.new_doc("Patient History" , {
			patient: rows._row.data.patient , 
			type: rows._row.data.type , 
			consultant: rows._row.data.admission_practitioner,
			floor: rows._row.data.floor , 
			room: rows._row.data.room , 
			bed: rows._row.data.bed
		 })
		
			// document.getElementById("select-stats").innerHTML = data.length;
		  });
		
	
});
		},


		make_grouping_btn:function(){
			let listitmes = ''
			
			let me = this
			let columns = [
				{title:"ID", field:"name"},
				{title:"Customer", field:"customer"},
				{title:"Customer Name", field:"customer"},
			
		 ]
				columns.forEach(field => {
					// console.log(field)
					// if(field.docfield.fieldtype !== "Currency"){
						listitmes += `
 
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
				
					
			// 		${listitmes}
			// 	</ul>
			// </button>
				$(`<div class="mt-2 sort-selector">
				
	
	
	
				<button type="button" class="btn btn-default btn-sm"<a href="#" data-toggle="dropdown" class="dropdown-toggle">Group<b class="caret"></b></a>
				</button>
				<ul class="dropdown-menu">
				${listitmes}
			</ul>
				</div>`).appendTo('.page-head')
			
			// this.group_by_control = new frappe.ui.GroupBy(this);
		
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
let met = `

<div class="container">
<div class="row">

<div id="met" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : met
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


durationformatter = function(cell, formatterParams, onRendered){
	return frappe.datetime.prettyDate(cell.getValue() , 1)
}
// let calculate_age = function(birth) {
//     let ageMS = Date.parse(Date()) - Date.parse(birth);
//     let age = new Date();
//     age.setTime(ageMS);
//     let years = age.getFullYear() - 1970;
//     return `${years} Years(s) ${age.getMonth()} Month(s) ${age.getDate()} Day(s)`;
// };

let calculate_age = function(birth) {
    let birthDate = new Date(birth);
    let today = new Date();

    let years = today.getFullYear() - birthDate.getFullYear();
    let months = today.getMonth() - birthDate.getMonth();
    let days = today.getDate() - birthDate.getDate();

    // Adjust for negative days
    if (days < 0) {
        months--;
        // Get total days in previous month
        let prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        days += prevMonth.getDate();
    }

    // Adjust for negative months
    if (months < 0) {
        years--;
        months += 12;
    }

    return `${years} Year(s) ${months} Month(s) ${days} Day(s)`;
};
