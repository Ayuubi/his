
frappe.pages['opd-dashboard'].on_page_load = function(wrapper) {
	new Opd_dashboard(wrapper)
	}
	Opd_dashboard= Class.extend({
		init: function(wrapper){
	
			this.xValues4 = []
			this.yValues4 = []
			this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'OPD DASHBOARD',
			single_column: true,
	
		});
			// $('.page-head').hide()
			this.make()
			this.cards()
			$(".analytics__item2").hide()
			// let to=this
		
			// this.create_btns()
		// $("#doctor").html(`   )
		frappe.call({
					
				method: 'his.api.dashboard.doctorwise',
				
				callback: function(data) {
					let doctorwise=''
					data.message.forEach(row=>{
						
						doctorwise+=`
							<tr>
     
     				 <td>${row.Practitioner}</td>
     				 <td>${row.Qty}</td>
    				  <td>$${row.Amount}</td>
    				</tr>`
						
					})

					$("#doctor").html(doctorwise)
				}
			})
// -------------------------------------------------------------------------------------------

		frappe.call({
					
				method: 'his.api.dashboard.doctor_wise_income',
				
				callback: function(data) {
					let doctorwise=''
					
					data.message.forEach(row=>{
				
						total_orders=''
						totl_bills=''
						if(!row.totl_bills){
							totl_bills="0"

						}
						else{
							totl_bills=row.totl_bills
						}
						if(!row.total_orders){
							total_orders="0"

						}
						else{
							total_orders=row.total_orders
						}
						doctorwise+=`
							<tr>
     
     				 <td>${row.ref_practitioner || ""}</td>
     				 <td>${row.item_group}</td>
    				  <td>$${total_orders}</td>
    				  <td>$${totl_bills}</td>
    				</tr>`
						
					})

					$("#doctor_income_wise").html(doctorwise)
				}
			})
// -------------------------------------------------------------------------------------------

		frappe.call({
					
				method: 'his.api.dashboard.patient_wise_income',
				
				callback: function(data) {
					// console.log(data.message)
					let doctorwise=''
					data.message.forEach(row=>{
					
						total_orders=''
						totl_bills=''
						if(!row.totl_bills){
							totl_bills="0"

						}
						else{
							totl_bills=row.totl_bills
						}
						if(!row.total_orders){
							total_orders="0"

						}
						else{
							total_orders=row.total_orders
						}
						doctorwise+=`
							<tr>
     
     				 <td>${row.patient}</td>
     				 <td>${row.item_group}</td>
    				  <td>$${total_orders}</td>
    				  <td>$${totl_bills}</td>
    				</tr>`
						
					})

					$("#patient_income_wise").html(doctorwise)
				}
			})
// -------------------------------------------------------------------------------------------
		frappe.call({
					
				method: 'his.api.dashboard.departmentwise',
				
				callback: function(data) {
					let departmentwise=''
					data.message.forEach(row=>{
						
						departmentwise+=`
							<tr>
     
     				 <td>${row.department}</td>
     				 <td>${row.Qty}</td>
    				  <td>$${row.Amount}</td>
    				</tr>`
						
					})

					$("#department").html(departmentwise)
				}
			})
		// -----------------------------------------------------------------------------------------
				frappe.call({
					
				method: 'his.api.dashboard.open_que',
				
				callback: function(data) {
					let que=''
					data.message.forEach(row=>{
					
						que+=`
							<tr>
     
     				 <td>${row.patient_name}</td>
     				 <td>${row.practitioner}</td>
    				  <td>${row.status}</td>
    				</tr>`
						
					})

					$("#openque").html(que)
				}
			})	
				// -----------------------------------------------------------------------------------------
				frappe.call({
					
				method: 'his.api.dashboard.doctor_wise_que',
				
				callback: function(data) {
					let doctor_wise_que=''
					data.message.forEach(row=>{
			
						doctor_wise_que+=`
							<tr>
     				<td>${row.practitioner}</td>
     				 <td>${row.New}</td>
     				 
    				  <td>${row.FollowUp}</td>
    				  <td>${row.Refer}</td>
    				  <td>${row.Revisit}</td>
    				  <td>${row.Total}</td>
    				  <td>${row.Open}</td>
    				  <td>${row.Closed}</td>
    				</tr>`
						
					})

					$("#doctorque").html(doctor_wise_que)
				}
			})
// -----------------------------------------------------------------------------------------
				frappe.call({
					
				method: 'his.api.dashboard.department_wise_que',
				
				callback: function(data) {
					let departmentque=''
					data.message.forEach(row=>{
			
						departmentque+=`
							<tr>
     				<td>${row.department}</td>
     				 <td>${row.New}</td>
     				 
    				  <td>${row.FollowUp}</td>
    				  <td>${row.Refer}</td>
    				  <td>${row.Revisit}</td>
    				  <td>${row.Total}</td>
    				  <td>${row.Open}</td>
    				  <td>${row.Closed}</td>
    				</tr>`
						
					})

					$("#departmentque").html(departmentque)
				}
			})

		}

			// ------------------------------------------------------------------

		,

		
		make: function() {
			let me = this
					   
			$(frappe.render_template("opd_dashboard", me)).appendTo(me.page.main)
	
			
			
			let xValues2 = ["Italy", "France", "Spain", "USA", "Argentina"];
			let yValues2 = [55, 49, 44, 24, 15];
			let barColors2 = ["#b91d47", "#00aba9", "#2b5797", "#e8c3b9", "#1e7145"];
			// frappe.require(["https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js"  ], () => {
						
			
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
					text: "World Wide Wine Production 2018",
				},
				},
			});
		// })

	
		let m = this
	
		frappe.call({
					
				method: 'his.api.dashboard.today',
				
				callback: function(data) {
					today=data.message[0].num
				m.generateData("Math.sin(x)", 0, today, 0.5);
			
		// this.generateData("Math.sin(x)", 0, 0, 0.5);
			new Chart("myChart4", {
			type: "line",
			data: {
				labels: m.xValues4,
				datasets: [
				{
					fill: false,
					pointRadius: 2,
					borderColor: "rgba(0,0,255,0.5)",
					data: m.yValues4,
				},
				],
			},
			options: {
				legend: { display: false },
				title: {
				display: true,
				text: "y = sin(x)",
				fontSize: 16,
				},
			},
			});
				frappe.call({
				method: 'his.api.dashboard.account_balance',
				callback: function(data) {

			let xValues = [];
			let yValues = [];
			data.message.forEach(row=>{
				xValues.push(row.account)
				yValues.push(row.balance)
			})
			let barColors = ["red", "green", "blue", "orange", "brown"];
	
			new Chart("myChart", {
			type: "bar",
			data: {
				labels: xValues,
				datasets: [
				{
					backgroundColor: barColors,
					data: yValues,
				},
				],
			},
			options: {
				legend: { display: false },
				title: {
				display: true,
				// text: "World Wine Production 2018",
				},
			},
			});
			}
			})				
					
		}
	})

		// ---------------------------------------------------------------last week-----------------------------------------------
		$("#week").click(function(){
			frappe.call({
						
					method: 'his.api.dashboard.week',
					
					callback: function(data) {
						res=data.message[0].num
					m.generateData("Math.sin(x)", 0, res, 0.5);
				
			// this.generateData("Math.sin(x)", 0, 0, 0.5);
				new Chart("myChart4", {
				type: "line",
				data: {
					labels: m.xValues4,
					datasets: [
					{
						fill: false,
						pointRadius: 2,
						borderColor: "rgba(0,0,255,0.5)",
						data: m.yValues4,
					},
					],
				},
				options: {
					legend: { display: false },
					title: {
					display: true,
					text: "y = sin(x)",
					fontSize: 16,
					},
				},
				});
		
		
		frappe.call({
				method: 'his.api.dashboard.account_balance',
				callback: function(data) {
				
			let xValues = [];
			let yValues = [];
			data.message.forEach(row=>{
				xValues.push(row.account)
				yValues.push(row.balance)
			})
				let barColors = ["red", "green", "blue", "orange", "brown"];
		
				new Chart("myChart", {
				type: "bar",
				data: {
					labels: xValues,
					datasets: [
					{
						backgroundColor: barColors,
						data: yValues,
					},
					],
				},
				options: {
					legend: { display: false },
					title: {
					display: true,
					// text: "World Wine Production 2018",
					},
				},
				});

			}
		})
								
						
			}
		})
	})	
	// -------------------------------last Month----------------------------------------------------------------------------------
	$("#month").click(function(){
		frappe.call({
					
				method: 'his.api.dashboard.month',
				
				callback: function(data) {
					res=data.message[0].num
				m.generateData("Math.sin(x)", 0, res, 0.5);
			
		// this.generateData("Math.sin(x)", 0, 0, 0.5);
			new Chart("myChart4", {
			type: "line",
			data: {
				labels: m.xValues4,
				datasets: [
				{
					fill: false,
					pointRadius: 2,
					borderColor: "rgba(0,0,255,0.5)",
					data: m.yValues4,
				},
				],
			},
			options: {
				legend: { display: false },
				title: {
				display: true,
				text: "y = sin(x)",
				fontSize: 16,
				},
			},
			});
	
			frappe.call({
				method: 'his.api.dashboard.account_balance',
				callback: function(data) {

			let xValues = [];
			let yValues = [];
			data.message.forEach(row=>{
				xValues.push(row.account)
				yValues.push(row.balance)
			})
			let barColors = ["red", "green", "blue", "orange", "brown"];
	
			new Chart("myChart", {
			type: "bar",
			data: {
				labels: xValues,
				datasets: [
				{
					backgroundColor: barColors,
					data: yValues,
				},
				],
			},
			options: {
				legend: { display: false },
				title: {
				display: true,
				// text: "World Wine Production 2018",
				},
			},
			});
			}
			})				
					
		}
	})
})	
// ---------------------------------------------------last year-----------------------------------------------------------------------
$("#year").click(function(){
	frappe.call({
				
			method: 'his.api.dashboard.year',
			
			callback: function(data) {
				res=data.message[0].num
			m.generateData("Math.sin(x)", 0, res, 0.5);
		
	// this.generateData("Math.sin(x)", 0, 0, 0.5);
		new Chart("myChart4", {
		type: "line",
		data: {
			labels: m.xValues4,
			datasets: [
			{
				fill: false,
				pointRadius: 2,
				borderColor: "rgba(0,0,255,0.5)",
				data: m.yValues4,
			},
			],
		},
		options: {
			legend: { display: false },
			title: {
			display: true,
			text: "y = sin(x)",
			fontSize: 16,
			},
		},
		});

		frappe.call({
			method: 'his.api.dashboard.account_balance',
				callback: function(data) {
		let xValues = ["Cashier", "Pharmacy"];
		let yValues = [55, 49, 44, 24, 15];
		let barColors = ["red", "green", "blue", "orange", "brown"];

		new Chart("myChart", {
		type: "bar",
		data: {
			labels: xValues,
			datasets: [
			{
				backgroundColor: barColors,
				data: yValues,
			},
			],
		},
		options: {
			legend: { display: false },
			title: {
			display: true,
			// text: "World Wine Production 2018",
			},
		},
		});
						
		}
		});		
	}
})
})	
// --------------------------------------------------------------------all---------------------------------------------------------------------
$("#all").click(function(){
	frappe.call({
				
			method: 'his.api.dashboard.all',
			
			callback: function(data) {
				res=data.message[0].num
			m.generateData("Math.sin(x)", 0, res, 0.5);
		
	// this.generateData("Math.sin(x)", 0, 0, 0.5);
		new Chart("myChart4", {
		type: "line",
		data: {
			labels: m.xValues4,
			datasets: [
			{
				fill: false,
				pointRadius: 2,
				borderColor: "rgba(0,0,255,0.5)",
				data: m.yValues4,
			},
			],
		},
		options: {
			legend: { display: false },
			title: {
			display: true,
			text: "y = sin(x)",
			fontSize: 16,
			},
		},
		});
		frappe.call({
				method: 'his.api.dashboard.account_balance',
				callback: function(data) {

			let xValues = [];
			let yValues = [];
			data.message.forEach(row=>{
				xValues.push(row.account)
				yValues.push(row.balance)
			})
				let barColors = ["red", "green", "blue", "orange", "brown"];

						new Chart("myChart", {
					type: "bar",
					data: {
						labels: xValues,
						datasets: [
						{
							backgroundColor: barColors,
							data: yValues,
						},
						],
					},
					options: {
						legend: { display: false },
						title: {
						display: true,
						// text: "World Wine Production 2018",
						},
					},
					});
				}
			})

						
				
	}
})
})	
					
				// Rest of your code...
			},
	generateData(value, i1, i2, step = 1) {
		let mys = this
				for (let x = i1; x <= i2; x += step) {
				  mys.yValues4.push(eval(value));
				  mys.xValues4.push(x);
				}
		}
		,

	
		cards:function(){
			let me = this

			frappe.call({
					
				method: 'his.api.dashboard.cards',
				
				callback: function(data) {
					let insurance=''
					let unbilled=''
					let ot=''
					let num=0
					data.message[12].forEach(row=>{
						num=num+1
						ot+=`
						    <div class="analytics__footerGrid">
				                <div class="analytics__footerItem">
				                  <div class="analytics__footerLeft">
				                    <span class="analytics__footerLeftNum">${num}</span> <br />
				                    
				                  </div>

				                  <div class="analytics__footerCenter">
				                    <span class="analytics__footerCenterTitle"
				                      >${row.patient_name}</span
				                    >
				                    <br />
				                    <span class="analytics__footerCenterSubtitle"
				                      >${row.practitioner}</span
				                    >
				                  </div>

				                  <div class="analytics__footerRight">${row.appointment_time}</div>
				                </div>
				              </div>
						`
					})
					data.message[11].forEach(row=>{
						unbilled +=`
									<div class="analytics__ATContentItem">
						            <div class="analytics__ATContentProjectName">${row.patient} </div>
                
					                <div class="analytics__ATContentProjectName">${row.patient_name}  </div>
					              
					                <div class="analytics__ATContentProgress">
					                
					                  <span class="analytics__ATContentProgNum">${row.ref_practitioner}</span>
					                </div>
					          <div class="analytics__ATContentAssignee">
					            <span class="analytics__ATContentStatusPrimay"
					            >${row.transaction_date}</span>
					                </div> 

					       

					                <div class="analytics__ATContentDueDate">
					                  <span>$${row.grand_total} </span>
					                </div>
					                 </div>

						`

					})

					data.message[10].forEach(row=>{
							insurance +=`
									<div class="analytics__ATContentItem">
						            <div class="analytics__ATContentProjectName">${row.patient} </div>
                
					                <div class="analytics__ATContentProjectName">${row.patient_name}  </div>
					              
					                <div class="analytics__ATContentProgress">
					                
					                  <span class="analytics__ATContentProgNum">${row.mobile} </span>
					                </div>
					          <div class="analytics__ATContentAssignee">
					            <span class="analytics__ATContentStatusPrimay"
					            >${row.insurance}</span>
					                </div> 

					                <div class="analytics__ATContentStatus">
					                  <span class="analytics__ATContentStatusPrimay"
					                    >${row.posting_date}</span
					                  >
					                </div>

					                <div class="analytics__ATContentDueDate">
					                  <span>$${row.total} </span>
					                </div>
					                 </div>

						`

					})


					let htmldata=''
					data.message[9].forEach(row => {
						htmldata +=`
									<div class="analytics__ATContentItem">
						            <div class="analytics__ATContentProjectName">${row.patient} </div>
                
					                <div class="analytics__ATContentProjectName">${row.patient_name}  </div>
					              
					                <div class="analytics__ATContentProgress">
					                
					                  <span class="analytics__ATContentProgNum">${row.mobile}</span>
					                </div>
					          <div class="analytics__ATContentAssignee">
					            <span class="analytics__ATContentStatusPrimay"
					            >${row.source_order}</span>
					                </div> 

					                <div class="analytics__ATContentStatus">
					                  <span class="analytics__ATContentStatusPrimay"
					                    >${row.posting_date}</span
					                  >
					                </div>

					                <div class="analytics__ATContentDueDate">
					                  <span>$${row.outstanding_amount} </span>
					                </div>
					                 </div>

						`
						
					})
					// alert(htmldata)

					$("#ot").html(ot)
					$("#unbilled_table").html(unbilled)

					$("#insurance_table").html(insurance)
					$("#upaid_table").html(htmldata)
					que=data.message[0][0].que
					invoices=data.message[2][0].num
					lab=data.message[3][0].num
					radiology=data.message[4][0].num
					draft_lab=data.message[5][0].num
					draft_radiology=data.message[6][0].num
					open_que=data.message[7][0].que
					unpaid=data.message[8][0].num
					
					setInterval(function () {
						$("#total_que").html(que)
						$("#invoices").html(invoices)
						$("#lab").html(lab)
						$("#radiology").html(radiology)
						$("#draft_radiology").html('Draft: '+draft_radiology)
						$("#draft_lab").html('Draft: '+draft_lab)
						$("#open_que").html('Open: '+open_que)
						$("#unpaid").html('Unpaid: '+unpaid)
						
					}, 100);
					
					
				}

			})
	
		}
		
	
	})


	


	
	