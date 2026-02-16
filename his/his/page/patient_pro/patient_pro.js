frappe.pages['patient-pro'].on_page_load = function(wrapper) {
	new Patient_pro(wrapper);

}
Patient_pro= Class.extend({
	init: function(wrapper){
		this.page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Patient Progress',
		single_column: true
	});
		// $('.page-head').hide()
		this.make()
		this.create_btns()

	},


	//grapp the class
make: function() {
let me = this
   		
			$(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main)
			// createYear = generate_year_range(1970, 2050);


			
			
			




		
		
    // Rest of your code...
},
	create_btns:function(){
		

			let emp = this.page.add_field({
				label: 'Patient',
				fieldtype: 'Link',
				fieldname: 'patient',
				options: "Patient",
			
				change() {
				
					let empl = emp.get_value()
					ready(empl)
					// console.log(empl)
					// create_clander(empl)
				}
			});
		}


})
function ready(empl){
		           frappe.call({
                    method: "his.api.patient_pro.get_patient_pro", //dotted path to server method
                    args: {
                        "empl":empl
                    },
                    callback: function(r) {
                    	// console.log(r)
			           if(r.message[0].que > 0){

						var que=$("#que").removeClass('hide')
						

						
				
				

				}
				else{
					var que=$("#que").addClass('hide')
				}
			  if(r.message[1].doctor > 0){

				var doctor=$("#doctor").removeClass('hide')
						

						
				
				

				}
				else{
					var doctor=$("#doctor").addClass('hide')
				}
				 if(r.message[2].cashier > 0){

				var cashier=$("#order").removeClass('hide')
						

						
				
				

				}
				else{
					var cashier=$("#order").addClass('hide')
				}
				if(r.message[3].invoice > 0){

				var invoice=$("#bill").removeClass('hide')
						

						
				
				

				}
				else{
					var invoice=$("#bill").addClass('hide')
				}
				if(r.message[4].pharmacy > 0){

				var pharmacy=$("#pharmacy").removeClass('hide')
						

						
				
				

				}
				else{
					var pharmacy=$("#pharmacy").addClass('hide')
				}
				if(r.message[5].imaging > 0){

				var imaging=$("#imaging").removeClass('hide')
						

						
				
				

				}
				else{
					var imaging=$("#imaging").addClass('hide')
				}
				if(r.message[6].lab > 0){

				var lab=$("#lab").removeClass('hide')
						

						
				
				

				}
				else{
					var lab=$("#lab").addClass('hide')
				}
                  
                    	// console.log(r)


                        
                    }
        });
	}
let patient_progress=`<head>
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"/>
</head>
<div class="progress" style="margin-top: 40px;">
  <div id="que" class="progress-bar progress-bar-success hide" role="progressbar" style="width:15% " >
    Que
  </div>
  <div id="doctor" class="progress-bar progress-bar-warning hide" role="progressbar" style="width:15% " >
    Doctor
  </div>
  <div id="order" class="progress-bar progress-bar-danger hide" role="progressbar" style="width:15% " >
    Order
  </div>
    <div id="bill" class="progress-bar progress-bar-primary hide" role="progressbar" style="width:15%" > 
    Bill
  </div>
    <div id="lab" class="progress-bar progress-bar-info hide" role="progressbar" style="width:15% " >
    Lab
  </div>
    <div id="imaging" class="progress-bar progress-bar-danger hide" role="progressbar" style="width:15% " >
    Imaging
  </div>
    <div id="pharmacy" class="progress-bar progress-bar-link hide" role="progressbar" style="width:15% " >
    Pharmacy
  </div>
</div>
`
frappe.dashbard_page = {
	body : patient_progress
}

	


