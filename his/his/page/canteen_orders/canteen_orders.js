frappe.pages['canteen-orders'].on_page_load = function(wrapper) {
	new OpdOrder(wrapper)
}

OpdOrder = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "OPD Order",
				single_column : true
			});
			this.groupbyD = []
			this.currDate =  frappe.datetime.get_today()
			this.make()
			this.setupdata_table()
			this.make_grouping_btn()
			let myf = this
			frappe.realtime.on('new_msg', (data) => {
				// alert("in realtime")
				myf.setupdata_table()
					})
			// this.grouping_cols()
		},
		make:function(){

		
			let me = this
			let date = this.page.add_field({
				fieldtype: 'Date',
			
				fieldname: 'date',
				label : "Date",
				default: frappe.datetime.get_today(),
				
				
				change: () => {
					// alert()
					this.currDate = date.get_value()
					me.setupdata_table()
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});
   		
   		
			$(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main)




		
		},

		setupdata_table : function(gr_ref){
			let currdate = this.currDate
		let tbldata = []
		frappe.call({
        method: "his.api.get_orders.get_canteen_orders", //dotted path to server method
        // args : {"_from" : "2022-11-5" , "to" : "2022-11-10"},
         args : {"currdate" : currdate},
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
			{title:"Customer Name", field:"customer_name" ,  headerFilter:"input"},
			{title:"Date", field:"transaction_date" ,  headerFilter:"input"},
			
			{title:"Total", field:"total" ,  headerFilter:"input",},
			{title:"Status", field:"status" ,  headerFilter:"input",},
			{title:"Time", field: "modified" ,  headerFilter:"input", formatter:formatter},

			{title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
			
		 ]
		//  fields.forEach(field => {
		// 	if(field.in_list_view){
		// 		columns.push(
		// 			{title:field.label, field:field.fieldname}
		// 		)
		// 	}
		//  })
		if(!gr_ref){
			columns.unshift(
				// {formatter:"responsiveCollapse", width:30, minWidth:30, hozAlign:"center", resizable:false, headerSort:false},
    
				{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"left", headerSort:false, checked:function(e, cell){
					// cell.getRow().toggleSelect();
					// alert("ok 2")
					me.toggle_actions_menu_button(true);
				  }}
			)
			
			
			

		}
		// console.log("this is ",doctype)
		let list_btns = frappe.listview_settings[`Sales Invoice`]
		// tbldata = tbldata[0]['action'] = "Button"
		let new_data = []
		// if(list_btns)
		// console.log(tbldata)
		tbldata.forEach(row => {
			// console.log(row.status)
			if(row.status === "To Deliver and Bill"){
				row.status = "To Bill"

			}
			// console.log("this is ",row.per_billed)
			let btnhml = ''
			// if (frappe.user_roles.includes('Pharmacy')) {
			// 	btnhml += `
			// 	<button class='btn btn-success ml-2' onclick = 'frappe.utils.print("Sales Order","${row.name}","drug","logo")'> Print</button>
				
			// `	
			
			// }
			if(row.status !== "Draft" && row.status !== "Cancelled" && row.status!= "Completed" ){
			
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
this.table = new Tabulator("#opdorder", {
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
let opdbody = `

<div class="container">
<div class="row">

<div id="opdorder" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : opdbody
}

cash_sales = function(source_name){
	frappe.model.open_mapped_doc({
		method: "his.api.make_invoice.make_sales_invoice",
		source_name: source_name
	})

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
				frappe.throw(__('Customer-kaan  looma ogala dayn'))
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
