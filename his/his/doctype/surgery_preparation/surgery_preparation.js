// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Surgery Preparation', {
	view_as_chart:function(frm){
		$("#vitals").html(`<canvas id="vitalSignsChart"></canvas>`)
		// alert("Test")
		setup_chart()
		
	},
	refresh: function(frm) {


		frappe.call({
			method: "his.his.doctype.surgery_preparation.surgery_preparation.get_billed_items", //dotted path to server method
			args :{

				patient: frm.doc.patient
			},
			callback: function(r) {
				// code snippet
				// console.log(r.message)
				frm.set_query('procedure', () => {
					return {
						filters: {
							template: ['in', r.message]
						}
					}
				})
			}
		});
		

		if (!frm.is_new()){
			frm.add_custom_button('Print Consent Form', () => {
				// let url= `${frappe.urllib.get_base_url()}/printview?doctype=Surgery%20Preparation&name=${frm.doc.name}&trigger_print=1&format=Surgery%20Preparation%20Consent&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en`;
				//      window.open(url, '_blank');
				if(frm.doc.consent_form){
					// frappe.set_route("Consent Surgery Form" , )
					frappe.set_route('Form', 'Consent Surgery Form', frm.doc.consent_form);
				}
				else{
					frappe.new_doc("Consent Surgery Form" , {"patient" : frm.doc.patient , "surgery_type" : frm.doc.procedure , "surgery_preparation" : frm.doc.name})
		
				}
			
			})

			var readybtn=frm.add_custom_button('Ready', () => {
				let d = new frappe.ui.Dialog({
					title: 'Checking Requiements',
					fields: [
						{
							label: '',
							fieldname: 'q1',
							fieldtype: 'HTML',
							options: 'Bukankan ma loo sameyay baritanadii loo baahnaa',
							// reqd : 1,
							
						},
						{
							label: '',
							fieldname: 'clomn1',
							fieldtype: 'Column Break',
						},
						{
							label: '',
							fieldname: 'cq1',
							fieldtype: 'Check',
						},
						{
							label: '',
							fieldname: 's1',
							fieldtype: 'Section Break',
						},
						
						{
							label: '',
							fieldname: 'q2',
							fieldtype: 'HTML',
							options: 'Bukaan maloo sameeyay dhamaan imaging',
							// reqd : 1,
							
						},
						{
							label: '',
							fieldname: 'clomn2',
							fieldtype: 'Column Break',
						},
						{
							label: '',
							fieldname: 'cq2',
							fieldtype: 'Check',
						},
						{
							label: '',
							fieldname: 's2',
							fieldtype: 'Section Break',
						},
						{
							label: '',
							fieldname: 'q3',
							fieldtype: 'HTML',
							options: 'Bukankan ma saxiixay warqadda ogolaanshaha qalinka(Consent form)',
							// reqd : 1,
							
						},
						{
							label: '',
							fieldname: 'clomn3',
							fieldtype: 'Column Break',
						},
						{
							label: '',
							fieldname: 'cq3',
							fieldtype: 'Check',
						},
						
					 
					],
					primary_action_label: 'Submit',
					primary_action(values) {
						  let cq1 = d.get_value("cq1")
						  let cq2 = d.get_value("cq2")
						  let cq3 = d.get_value("cq3")
					if(!cq1){
						alert("Bukankan ma loo sameyaynin baritanadii loo baahnaa")
					
				// 			frappe.call({
				// 					method: "his.api.refer.refer", //dotted path to server method
				// 					args: {
				// 						"patient" : frm.doc.patient,
				// 						"practitioner" : practitioner,
				// 						"name": frm.doc.name,
				// 						"referring_practitioner": frm.doc.practitioner,
				// 					},
				// 					callback: function(r) {
				// 						// code snippet
				// 						// console.log(r)
				// 					// frm.set_value("status" , "Refered")
				// 					 frappe.utils.play_sound("submit")
				
				// 						frappe.show_alert({
				// 					message:__('You have Refered Patient Succesfully'),
				// 					indicator:'green',
									
				// 				}, 5);
				// 				// cur_frm.print_doc()
				// 					}
				// });

						d.hide();
					}
					if(!cq2){
						alert("Bukaan maloo sameeyay dhamaan imaging")

						d.hide();
					}
					if(!cq3){
						alert("Bukankan ma saxiixin warqadda ogolaanshaha qalinka(Consent form)")

						d.hide();
					}
					if(cq1 && cq2 && cq3){
					
							frappe.call({
									method: "his.his.doctype.surgery_preparation.surgery_preparation.make_ot_schedule", //dotted path to server method
									args: {
										"docname": frm.doc.name
									},
									callback: function(r) {
										
									 frappe.utils.play_sound("submit")
				
										frappe.show_alert({
									message:__('You have Succesfully Transfared OT '),
									indicator:'green',
									
								}, 5);
								// cur_frm.print_doc()
									}
				});

						d.hide();
					}
					}
					
				});
				
				d.show();
		
			})
			readybtn.addClass('btn-danger');
		}
	
		frm.set_df_property('view_as_chart', 'css_class', 'align-right');
		// $('.indicator-pill').hide()
		// $('.standard-actions').hide()
		// frm.disable_save();
		get_history(frm.doc.patient , "vitals")

		var tabs = $('.form-tabs');
		var parentElement = $('.parent');

// Get all child elements of the parent
		var childElements = tabs.children();

		// Loop through each child element and attach click event handler
		childElements.each(function() {
		var childElement = $(this);
		var tab = childElement[0].innerText.replace(/ /g, '_').toLowerCase()
		if(tab == "prescription"){
			tab = "med"
		}
		// Attach click event handler to the current child element
		childElement.click(function() {
			get_history(frm.doc.patient , tab)
			// Code to execute when the current child element is clicked
			// ...
		});
		});

		// $('#patient-history-vitals_tab-tab').on('click', function() {
        //     // Get the clicked tab name
        //     var tabName = $(this).attr('data-fieldname');
		// 	alert("")
            
        //     // Handle tab click event
      
        // });
	
		// var htmlContent = "<div id = 'vitals' >Test </div>";

        // Set the HTML content to a field in the form
        // frm.set_value('vitals', htmlContent);
		// setupdata_table("PID-00265")

	},
	onload:function(frm){
		get_history(frm.doc.patient , "vitals")

		// alert("")
	},
	
});

function setup_chart(){

// Sample vital signs data
const vitalSignsData = [
	{ datetime: '8:00:00', temperature: 98.6, heartRate: 80, bloodPressure: '120' },
	{ datetime: '12:00:00', temperature: 70.1, heartRate: 82, bloodPressure: '150' },
	{ datetime: '16:00:00', temperature: 97.9, heartRate: 78, bloodPressure: '160' },
	// Add more data entries as needed
  ];
  
  // Function to generate a random color
  function getRandomColor() {
	const letters = '0123456789ABCDEF';
	let color = '#';
	for (let i = 0; i < 6; i++) {
	  color += letters[Math.floor(Math.random() * 16)];
	}
	return color;
  }
  
  // Extract datetimes and vital signs data
  const datetimes = vitalSignsData.map((data) => new Date(data.datetime));
  const vitalSigns = Object.keys(vitalSignsData[0]).filter((key) => key !== 'datetime');
  
  // Create datasets for each vital sign
  const datasets = vitalSigns.map((sign) => ({
	label: sign,
	data: vitalSignsData.map((data) => data[sign]),
	borderColor: getRandomColor(),
	fill: false,
  }));
  
  // Create a new Chart instance
  const ctx = document.getElementById('vitalSignsChart').getContext('2d');
  const chart = new Chart(ctx, {
	type: 'line',
	data: {
	  labels: datetimes,
	  datasets: datasets,
	},
	options: {
	  responsive: true,
	  scales: {
		x: {
		  type: 'time',
		  time: {
			tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
			unit: 'minute',
			displayFormats: {
			  minute: 'YYYY-MM-DD HH:mm',
			},
		  },
		  title: {
			display: true,
			text: 'Date and Time',
		  },
		},
	  },
	},
  });
  
  
  
  
}


function getRandomColor() {
	const letters = '0123456789ABCDEF';
	let color = '#';
	for (let i = 0; i < 6; i++) {
	  color += letters[Math.floor(Math.random() * 16)];
	}
	return color;
  }

function get_history(patient ,tab) {
	// alert(tab)
	
	let tbldata = []
	let lab_data = []
	
	frappe.call({
        method: "his.dashboard_and_history.p_history.get_p_histy", //dotted path to server method
        args : {"patient" : patient},
        callback: function(r) {
           let columns =  r.message[0][tab]
		   let data = r.message[1][tab]
		 
		   if(tab == "labs"){
			// alert()
			data.forEach(element => {
				frappe.db.get_doc("Lab Result" , element.name).then( r => {
					if(r.template == "CBC"){
						lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": "CBC"})
 
					}
					
					r.normal_test_items.forEach(result => {

						lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": result.test ,"lab_test_name":result.lab_test_name , "lab_test_event" : result.lab_test_event , "result_value" : result.result_value})
 
					})
				})
				
			});
			setTimeout(() => {
			
				columns = [{title : "Date" , field : "date"},{title : "Practitioner" , field : "practitioner"},{title : "Test" , field : "test"} , {title : "Test Name" , field : "lab_test_name"} ,  {title : "Event" , field : "lab_test_event"} , {title : "Result" , field : "result_value"}  ]
				setup_datatable(columns , lab_data , "date" , tab)
			   }, 200);
		   }
		
			else{
			if(columns){
			
				setup_datatable(columns , data , false , tab)
			}
			else{
				
				setup_datatable([] , [] , false , tab)

			}
		}
        }})



// 	frappe.call({
// 		method: "his.api.vitals.get_vital", //dotted path to server method
// 		args :{ "patient": patient
// 			},
// 		callback: function(r) {
			
// 			tbldata = r.message
	
   

			
		
// 		 let me = this
// 		//  let fields = frappe.get_meta("Sales Order").fields
// 			let columns = [
// 			// {title:"ID", field:"name"},
// 			// {title:"Patient", field:"customer"},
// 			{title:"Date / Time", field:"modified"},
// 			{title:"Temperature", field:"temperature"},
// 			{title:"Pulse", field:"pulse"},
// 			{title:"BP", field:"bp"},
// 			{title:"Respiration", field:"respiratory_rate"},
// 			{title:"SpO2", field:"spo"},
// 			{title:"Height", field:"height"},
// 			{title:"Weight", field:"weight"},
// 			{title:"BMI", field:"bmi"},
// 			{title:"Nurse", field:"owner"},
			
// 			// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
			
// 		 ]
	


//
// this.table = new Tabulator("#vitals", {
// 			// layout:"fitDataFill",
// 			layout:"fitDataStretch",
// 			//  layout:"fitColumns",
// 			// responsiveLayout:"collapse",
// 			 rowHeight:30, 
// 			//  selectable:true,
// 			//  dataTree:true,
// 			//  dataTreeStartExpanded:true,
// 			 groupStartOpen:false,
// 			 printAsHtml:true,
// 			//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
// 			//  printFooter:"<h2>Example Table Footer<h2>",
// 			 // groupBy:"customer",
// 			 groupHeader:function(value, count, data, group){
// 				 //value - the value all members of this group share
// 				 //count - the number of rows in this group
// 				 //data - an array of all the row data objects in this group
// 				 //group - the group component for the group
// 			
// 				 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
// 			 },
// 			 groupToggleElement:"header",
// 			//  groupBy:groupbyD.length >0 ? groupbyD : "",
// 			 textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
	 
// 			 columns: columns,
			 
		
			 
// 			 data: new_data
// 		 });
		 

// 		}
	
// });
}

function setup_datatable(columns , data , group , tabid){
	// console.log(data)

	// alert(tabid)
	let groupBy = []
	if(group){
		groupBy.push(group)
	}

	this.table = new Tabulator(`#${tabid}`, {
		// layout:"fitDataFill",
		layout:"fitDataFill",
		//  layout:"fitColumns",
		// responsiveLayout:"collapse",
		 rowHeight:30, 
		 placeholder:"No Data Available",
		//  selectable:true,
		//  dataTree:true,
		//  dataTreeStartExpanded:true,
		 groupStartOpen:false,
		 printAsHtml:true,
		//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
		 printFooter:"<h2>Example Table Footer<h2>",
		 groupBy:groupBy,
		 groupHeader:function(value, count, data, group){
			 //value - the value all members of this group share
			 //count - the number of rows in this group
			 //data - an array of all the row data objects in this group
			 //group - the group component for the group
		
			 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
		 },
		 groupToggleElement:"header",
		//  groupBy:groupbyD.length >0 ? groupbyD : "",
		//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
 
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
		 
		 data: data
	 });
}