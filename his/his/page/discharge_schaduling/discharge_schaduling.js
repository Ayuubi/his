frappe.pages['discharge-schaduling'].on_page_load = function(wrapper) {
	new IPD(wrapper)
}

IPD = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Discharge Schaduling",
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
			fields: ['name','patient','patient_name', 'room' , 'bed' , 'scheduled_date' , 'primary_practitioner' , 'clearance_status', 'status'],
			filters: {
				status: 'Discharge Scheduled'
			},
			limit : 1000
		}).then(r => {
			// console.log(r)
			
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
			{title:"PID", field:"patient" ,  headerFilter:"input"},
			{title:"Patient Name", field:"patient_name" ,  headerFilter:"input"},
			{title:"Admission Date", field:"scheduled_date" ,  headerFilter:"input"},
			{title:"Doctor Name", field:"primary_practitioner" ,  headerFilter:"input",},
			{title:"Room", field:"room" ,  headerFilter:"input",},
			
			{title:"Bed", field:"bed" ,  headerFilter:"input",},
			{title:"Status", field:"status" ,  headerFilter:"input",},
			
			

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

					
			if(row.clearance_status == "Cleared"){
				btnhml = `
				<button class='btn btn-danger ml-2' onclick = "discharge('${row.name}')"> Discharge</button>
				`

			}
			else if(row.clearance_status == "Uncleared"){
				btnhml = `
			<p class='btn btn-primary ml-2' >Uncleared</p>
		
		
			
			`

			}

			
			row['action'] = btnhml
			new_data.push(row)
		})
		// console.log(columns)
this.table = new Tabulator("#dis_sch", {
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
let dischargeSched = `

<div class="container">
<div class="row">

<div id="dis_sch" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : dischargeSched
}


formatter = function(cell, formatterParams, onRendered){
			return frappe.datetime.prettyDate(cell.getValue() , 1)
		}

function discharge(name){

// alert(name)
	frappe.confirm('Are you sure you want to proceed?',
    () => {
        // action to perform if Yes is selected

		frappe.call({
			method: "his.api.inpatient_record.check_out_inpatient", //dotted path to server method
			args: {
				'inpatient_record' : name
			},
			callback: function(r) {
				// code snippet
				// console.log(r)
			// frm.set_value("status" , "Refered")
			const baseUrl = `${window.location.protocol}//${window.location.host}`;
			let url = baseUrl + "/printview?doctype=Inpatient%20Record&name="+name+"&trigger_print=1&format=Exit%Gate&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en-US"
			window.open(url, '_blank');
			// frappe.utils.print("Inpatient Record",name,"Exit Gate","logo")
			frappe.utils.play_sound("submit")
			window.location.reload();
			frappe.show_alert({
			message:__('You have Discharged Patient Succesfully'),
			indicator:'green',
			
		}, 5);
			}
		});
    }, () => {
        // action to perform if No is selected
    })


}