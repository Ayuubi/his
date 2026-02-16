frappe.pages['dashboards'].on_page_load = function(wrapper) {
new dashboards(wrapper)
}
dashboards= Class.extend({
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

	},
	
	make: function() {
		let me = this
				   
		$(frappe.render_template("dashboards", me)).appendTo(me.page.main)

		
		
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
		this.generateData("Math.sin(x)", 0, 10, 0.5);
		
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
	let mys = this
			for (let x = i1; x <= i2; x += step) {
			  mys.yValues4.push(eval(value));
			  mys.xValues4.push(x);
			}
	},



	

})
