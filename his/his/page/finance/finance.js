frappe.pages['finance'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'None',
		single_column: true
	});
}


frappe.pages['finance'].on_page_load = function(wrapper) {
	new finance(wrapper)
	}
	
	
	finance= Class.extend({
		init: function(wrapper){
	
			this.xValues4 = []
			this.yValues4 = []
			this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Dashboard',
			single_column: true,
	
		});
			// $('.page-head').hide()
			this.make()
			
			
			
			// this.create_btns()
			frappe.call({
					
				method: 'his.dashboard_and_history.finance.get_data',
				args :{"from_date" :  get_today() , "to_date" : get_today()},
				
				callback: function(r) {
					// console.log(r)
					data  = r.message[0]

					// console.log(data)
					$('#new_que').html(`New : ${data.new}`)
					$('#fallowup').html(`Fallowup : ${data.fall}`)
					$('#revisit').html(`Revisit : ${data.rev}`)
					$('#paid').html(`Paid : $${data.paid}`)
					$('#unpaid').html(`Unpaid : $${data.unpaid}`)
					$('#free').html(`Free : $${data.free}`)
					let bils_html = ``
					bills = r.message[1]
					bills.forEach(bill => {
						bils_html += `
						
						<div class="sales">
						<div class="analytics__money">${bill.source_order} </div>
						<div class="analytics__money">Paid : ${bill.paid} </div>
						<div class="analytics__money">Unpaid : ${bill.unpaid}</div>
					
					</div>
						`
						
					});
					$('#bills').html(bils_html)
					let sales_gr_html = ``
					sales = r.message[2]
					for (let key in sales) {
						if (sales.hasOwnProperty(key)) {
							// console.log(key, sales[key]);
						 
						sales_gr_html += `
						<div class="analytics__todoItem" >
            

						<div class="analytics__todoItemList">
					
						  <span>${key.toUpperCase()}</span>
						</div>
		  
						<span class="analytics__todoDate ml-3"><strong>$${sales[key]}</strong></span>
		  
					   
					  </div>
						`
						
					}
				}
					$('#sales_group').html(sales_gr_html)

				}})
			frappe.call({
					method: 'his.dashboard_and_history.finance.account_balance',
					callback: function(r) {
						let account_html = ``
						r.message.forEach(account => {
							account_html += `
							
							<div class="accounts" style="margin-top: 3px;">
							<div class="analytics__money">${account.account} : ${account.balance}</div>
						
						</div>
							`
							
						});
						$('#accounts').html(account_html)
					
						
					}
				})				
			frappe.call({
					method: 'his.dashboard_and_history.finance.payables',
					callback: function(r) {
						let payables_html = ``
						r.message[1].forEach(payable => {
							payables_html += `
							
							<div class="analytics__mapProgWrap">
							<div class="analytics__countryProgressName" >
							  <span class="analytics__mapCountrName"style="margin-top: 5px;">${payable.party}</span>
							  <span class="analytics__mapCountrProgNum"style="margin-top: 5px;">$${payable.outstanding}</span>
							</div>
						  </div>
						  
							`
							
						});
						$('#payables').html(payables_html)
					
						
					}
				})				
	
		},
		
		make: function() {
			let me_f = this
					   
			$(frappe.render_template("finance", me_f)).appendTo(me_f.page.main)
	
			
			
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
	
	
		let m_f = this
			this.generateData("Math.sin(x)", 0, 10, 0.5);
			
			new Chart("myChart4", {
			type: "line",
			data: {
				labels: m_f.xValues4,
				datasets: [
				{
					fill: false,
					pointRadius: 2,
					borderColor: "rgba(0,0,255,0.5)",
					data: m_f.yValues4,
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
	
	
			let xValues = ["Website", "App", "Linux", "Window"];
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
							
					
					
					
				// Rest of your code...
			},
	generateData(value, i1, i2, step = 1) {
		let mys_f = this
				for (let x = i1; x <= i2; x += step) {
					mys_f.yValues4.push(eval(value));
					mys_f.xValues4.push(x);
				}
		},
	
		cards:function(){
			let me = this

			frappe.call({
					
				method: 'his.dashboard_and_history.finance.insurance',
				
				callback: function(data) {
					let insurance=''
					data.message.forEach(row=>{
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



					$("#insurance_table").html(insurance)

					
					
					
				}

			})
	
		}
	
		
	
	})
	