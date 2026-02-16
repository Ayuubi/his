

frappe.pages['discharged'].on_page_load = function(wrapper) {
	new Disch(wrapper)
}

Disch = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Discharged",
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
			let me = this;

			// Add Start Date field
			let start_date_field = this.page.add_field({
				fieldtype: 'Date',
				fieldname: 'start_date',
				label: 'Start Date',
				default: frappe.datetime.get_today(),
				change: () => {
					// Update the selected start date value
					this.startDate = start_date_field.get_value();
					if (this.isTableReady) {
						me.setupdata_table();  // Refresh the table with the updated date range
					}
				}
			});

			// Add End Date field
			let end_date_field = this.page.add_field({
				fieldtype: 'Date',
				fieldname: 'end_date',
				label: 'End Date',
				default: frappe.datetime.get_today(),
				change: () => {
					// Update the selected end date value
					this.endDate = end_date_field.get_value();
					if (this.isTableReady) {
						me.setupdata_table();  // Refresh the table with the updated date range
					}
				}
			});

			// Initialize the table after the fields are added
			let dischargedHtml = `
				<div class="container">
					<div class="row">
						<div id="discharged" style="min-width: 100%;"></div>
					</div>
				</div>
			`;
			$(dischargedHtml).appendTo(me.page.main);  // Append the table container

			// Set the flag to true once the table is ready
			this.isTableReady = true;
			me.setupdata_table();  // Initial data load
		},

		setupdata_table: function(gr_ref){
			let currdate = this.currDate;
			let startDate = this.startDate || frappe.datetime.get_today();  // Get selected start date
			let endDate = this.endDate || frappe.datetime.get_today();  // Get selected end date
			let tbldata = [];

			// Fetch inpatient records with the date filter
			frappe.db.get_list('Inpatient Record', {
				fields: ['name', 'patient', 'patient_name', 'room', 'bed', 'admitted_datetime', 'discharge_datetime', 'admission_practitioner', 'diagnose'],
				filters: {
					status: 'Discharged',
					discharge_datetime: ['between', [startDate, endDate]] // Filter by date range
				},
				limit: 1000
			}).then(r => {
				tbldata = r;

				let me = this;
				
				// Fetch discharged_type for each inpatient record
				let new_data = [];
				let promises = tbldata.map(row => {
					return frappe.db.get_value('Discharge Summery', { 'patient': row.patient }, 'discharged_type').then(res => {
						row['discharged_type'] = res.message.discharged_type; // Set the discharged_type in the row
						new_data.push(row); // Push the row with discharged_type to new_data
					});
				});

				// Wait for all promises to resolve
				Promise.all(promises).then(() => {
					// Define columns, using discharged_type instead of inpatient_status
					let columns = [
						{title: "No", field: "id", formatter: "rownum"},
						{title: "PID", field: "patient", headerFilter: "input"},
						{title: "Patient Name", field: "patient_name", headerFilter: "input"},
						{title: "Admitted Date", field: "admitted_datetime", headerFilter: "input"},
						{title: "Discharge Date", field: "discharge_datetime", headerFilter: "input"},
						{title: "Doctor Name", field: "admission_practitioner", headerFilter: "input"},
						{title: "Room", field: "room", headerFilter: "input"},
						{title: "Bed", field: "bed", headerFilter: "input"},
						{title: "Discharged Type", field: "discharged_type", headerFilter: "input"}, // Use discharged_type here
						{title: "Diagnosis", field: "diagnose", headerFilter: "input"}
					];

					// Initialize Tabulator with the updated columns
					this.table = new Tabulator("#discharged", {
						layout: "fitDataStretch",
						rowHeight: 30, 
						groupStartOpen: false,
						printAsHtml: true,
						groupHeader: function(value, count, data, group) {
							return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
						},
						groupToggleElement: "header",
						textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
						pagination: "remote",  
						paginationSize: 50,    
						paginationDataSent: {
							page: "page",      
							size: "limit"      
						},
						paginationDataReceived: function(data) {
							return {
								rows: data.result, 
								total: data.total   
							};
						},
						columns: columns,
						data: new_data // Use new_data which contains discharged_type
					});

					// Row click event handler
					this.table.on("rowClick", function(e, rows) {
						frappe.new_doc("Patient History", { patient: rows._row.data.patient })
					});
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
let discharged = `

<div class="container">
<div class="row">

<div id="discharged" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : discharged
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
