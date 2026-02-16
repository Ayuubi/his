frappe.pages['ipd-dasboard'].on_page_load = function(wrapper) {
	new Ipd_dashboard(wrapper)
}
Ipd_dashboard= Class.extend({
	init: function(wrapper){

		this.xValues4 = []
		this.yValues4 = []
		this.page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'IPD DASHBOARD',
		single_column: true,

	});
		// $('.page-head').hide()
		this.make()

		
			
	
		// this.cards()
		// $(".analytics__item2").hide()
		// let to=this
	
		// this.create_btns()
	// $("#doctor").html(`   )
	
// // -------------------------------------------------------------------------------------------

	// frappe.call({
				
	// 		method: 'his.api.dashboard.doctor_wise_income',
			
	// 		callback: function(data) {
	// 			let doctorwise=''
	// 			data.message.forEach(row=>{
	// 				// console.log(row)
	// 				total_orders=''
	// 				totl_bills=''
	// 				if(!row.totl_bills){
	// 					totl_bills="0"

	// 				}
	// 				else{
	// 					totl_bills=row.totl_bills
	// 				}
	// 				if(!row.total_orders){
	// 					total_orders="0"

	// 				}
	// 				else{
	// 					total_orders=row.total_orders
	// 				}
	// 				doctorwise+=`
	// 					<tr>
 
	// 			  <td>${row.ref_practitioner}</td>
	// 			  <td>${row.item_group}</td>
	// 			  <td>$${total_orders}</td>
	// 			  <td>$${totl_bills}</td>
	// 			</tr>`
					
	// 			})

	// 			$("#doctor_income_wise").html(doctorwise)
	// 		}
	// 	})
// -------------------------------------------------------------------------------------------

	// frappe.call({
				
	// 		method: 'his.api.dashboard.patient_wise_income',
			
	// 		callback: function(data) {
	// 			let doctorwise=''
	// 			data.message.forEach(row=>{
	// 				// console.log(row)
	// 				total_orders=''
	// 				totl_bills=''
	// 				if(!row.totl_bills){
	// 					totl_bills="0"

	// 				}
	// 				else{
	// 					totl_bills=row.totl_bills
	// 				}
	// 				if(!row.total_orders){
	// 					total_orders="0"

	// 				}
	// 				else{
	// 					total_orders=row.total_orders
	// 				}
	// 				doctorwise+=`
	// 					<tr>
 
	// 			  <td>${row.patient}</td>
	// 			  <td>${row.item_group}</td>
	// 			  <td>$${total_orders}</td>
	// 			  <td>$${totl_bills}</td>
	// 			</tr>`
					
	// 			})

	// 			$("#patient_income_wise").html(doctorwise)
	// 		}
	// 	})
// -------------------------------------------------------------------------------------------
	// frappe.call({
				
	// 		method: 'his.api.dashboard.departmentwise',
			
	// 		callback: function(data) {
	// 			let departmentwise=''
	// 			data.message.forEach(row=>{
	// 				console.log(row)
	// 				departmentwise+=`
	// 					<tr>
 
	// 			  <td>${row.department}</td>
	// 			  <td>${row.Qty}</td>
	// 			  <td>$${row.Amount}</td>
	// 			</tr>`
					
	// 			})

	// 			$("#department").html(departmentwise)
	// 		}
	// 	})
	// -----------------------------------------------------------------------------------------
		// 	frappe.call({
				
		// 	method: 'his.api.dashboard.open_que',
			
		// 	callback: function(data) {
		// 		let que=''
		// 		data.message.forEach(row=>{
		// 			console.log(row)
		// 			que+=`
		// 				<tr>
 
		// 		  <td>${row.patient_name}</td>
		// 		  <td>${row.practitioner}</td>
		// 		  <td>${row.status}</td>
		// 		</tr>`
					
		// 		})

		// 		$("#openque").html(que)
		// 	}
		// })	
			// -----------------------------------------------------------------------------------------
// 			frappe.call({
				
// 			method: 'his.api.dashboard.doctor_wise_que',
			
// 			callback: function(data) {
// 				let doctor_wise_que=''
// 				data.message.forEach(row=>{
// 					// console.log(row)
// 					doctor_wise_que+=`
// 						<tr>
// 				 <td>${row.practitioner}</td>
// 				  <td>${row.New}</td>
				  
// 				  <td>${row.FollowUp}</td>
// 				  <td>${row.Refer}</td>
// 				  <td>${row.Revisit}</td>
// 				  <td>${row.Total}</td>
// 				  <td>${row.Open}</td>
// 				  <td>${row.Closed}</td>
// 				</tr>`
					
// 				})

// 				$("#doctorque").html(doctor_wise_que)
// 			}
// 		})
// // -----------------------------------------------------------------------------------------
		// 	frappe.call({
				
		// 	method: 'his.api.dashboard.department_wise_que',
			
		// 	callback: function(data) {
		// 		let departmentque=''
		// 		data.message.forEach(row=>{
		// 			// console.log(row)
		// 			departmentque+=`
		// 				<tr>
		// 		 <td>${row.department}</td>
		// 		  <td>${row.New}</td>
				  
		// 		  <td>${row.FollowUp}</td>
		// 		  <td>${row.Refer}</td>
		// 		  <td>${row.Revisit}</td>
		// 		  <td>${row.Total}</td>
		// 		  <td>${row.Open}</td>
		// 		  <td>${row.Closed}</td>
		// 		</tr>`
					
		// 		})

		// 		$("#departmentque").html(departmentque)
		// 	}
		// })

	},
	make: function() {
		let me = this
				   
		$(frappe.render_template("ipd_dasboard", me)).appendTo(me.page.main)

		frappe.call({
				
			method: 'his.api.ipd_dashboard.admit_dashboard',
			
			callback: function(data) {
				
				let admited=''
				data.message.forEach(row=>{
					// console.log(data)
					admited+=`
						<tr>
 
				  <td>${row.patient_name}</td>
				  <td>${row.room || ""}</td>
				  <td>${row.bed || ""}</td>
				  <td>${row.type || "" }</td>
				  <td>$${row.balance || 0}</td>
				  <td>$${row.allowed_credit || 0 }</td>
				  
				</tr>`
					
				})
				
				

				$("#add").html(admited)
		

			}
		})
		frappe.call({
				
			method: 'his.api.ipd_dashboard.discharge_p_da',
			
			callback: function(data) {
				
				let dischraged=''
				data.message.forEach(row=>{
					// console.log(data)
					dischraged+=`
						<tr>
 
				  <td>${row.patient_name}</td>
				  <td>${row.room || ""}</td>
				  <td>${row.bed || ""}</td>
				  <td>${row.type || "" }</td>
				  <td>$${row.balance || 0}</td>
				  <td>${row.allowed_credit || 0 }</td>
				  <td>${row.clearance_status || "" }</td>
				  
				</tr>`
					
				})
				
				
				
				$("#dischraged").html(dischraged)
		

			}
		})
		frappe.call({
				
			method: 'his.api.ipd_dashboard.admission_ordered',
			
			callback: function(data) {
				
				let admission=''
				data.message.forEach(row=>{
					// console.log(data)
					admission+=`
						<tr>
 
				  <td>${row.patient_name}</td>
				  <td>${row.room || ""}</td>
				  <td>${row.bed || ""}</td>
				  <td>${row.type || "" }</td>
				  <td>$${row.balance || 0}</td>
				  <td>${row.allowed_credit || 0 }</td>
				  <td>${row.status || "" }</td>
				  
				</tr>`
					
				})
				
				
				
				$("#admission").html(admission)
		

			}
		})
		frappe.call({
				
			method: 'his.api.ipd_dashboard.doctor_plan',
			
			callback: function(data) {
				
				let doctor=''
				data.message.forEach(row=>{
					// console.log(data)
					doctor+=`
						<tr>
 
				  <td>${row.patient_name}</td>
				  <td>${row.ref_practitioner || ""}</td>
				  <td>${row.drug_code || ""}</td>
				  <td>${row.quantity || "" }</td>
				  <td>${row.ordered_qty || 0 }</td>
				  <td>$${row.used_qty || 0}</td>
				
			
				  
				</tr>`
					
				})
				
				
				
				$("#doctorp").html(doctor)
		

			}
		})
		frappe.call({
				
			method: 'his.api.ipd_dashboard.bed_status',
			
			callback: function(data) {
				
					let xValues2 = ["Occupied", "In Cleaning", "Discharge Ordered", "Vacant"];
					let yValues2 = [];
					let barColors2 = ["#b91d47", "#ffff00", "#2b5797", "#1e7145"];
				data.message.forEach(row=>{
					// xValues.push(row.account)
					yValues2.push(row.Occupied,row.InCleaning,row.Discharge,row.Vacant)
					console.log(data)

					new Chart("myChart2", {
						type: "doughnut",
						data: {
						  labels: xValues2,
						  datasets: [
							{
							  backgroundColor: barColors2,
							  data: yValues2,
							},
						  ],
						},
						options: {
						  title: {
							display: true,
							text: "Bed Status",
						  },
						},
					  });
				// 	doctor+=`
				// 		<tr>
 
				//   <td>${row.patient_name}</td>
				//   <td>${row.ref_practitioner || ""}</td>
				//   <td>${row.drug_code || ""}</td>
				//   <td>${row.quantity || "" }</td>
				//   <td>${row.ordered_qty || 0 }</td>
				//   <td>$${row.used_qty || 0}</td>
				
			
				  
				// </tr>`
					
				})
				
				
				
				// $("#doctorp").html(doctor)
		

			}
		})
			// Rest of your code...
		},
})