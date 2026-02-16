
frappe.pages['bed-matrix'].on_page_load = function(wrapper) {
	new BedMatrix(wrapper)
}

BedMatrix = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Bed Matix",
				single_column : true
			});
			$('.page-head').hide()
			this.make()
			
			// this.make_grouping_btn()
			// this.grouping_cols()
		},
		make:function(){
			let me = this
   		
			$(frappe.render_template("bed_matrix", me)).appendTo(me.page.main)
			let room_list = ``
			let ul_nav = $('#nav_ul').empty()
			let room_sel =''
			let room = ''
			frappe.db.get_list('Healthcare Service Unit Type',
			 {
				fields: ['name'],
				filters: {
					type: "IPD"
				}
			}).then(records => {
				records.forEach( (element  , index)=> {
					if(index == 0){
						room = element.name
					}
					room_list +=  `
					<li>
					<span class="bed_icon__"><i class="fa fa-bed"></i></span>
					<a   class = "room_selec" id = "${element.name}">${element.name}</a>
				  </li>
					`
				})
				$(room_list).appendTo(nav_ul)
				get_beds(room)
				room_sel = $(".room_selec")
				room_sel.click( e => {
					let room_name = e.target.id
					get_beds(room_name)
					// alert()
					// console.log("this is ",e.target.id)
	
				
				
	
					
				})

			})
			
			
			




		
		}
	})


	function get_beds(room_name){
		// alert(room_name)
		frappe.db.get_list('Healthcare Service Unit', {
			fields: ['name', 'occupancy_status'],
			filters: {
				service_unit_type: room_name
			}
		}).then(records => {
			// console.log(records);
			let bed = ``
			let sts_bg_class= "card_one_occupied"
			records.forEach(element => {
				if(element.occupancy_status === "Occupied"){
					sts_bg_class = "card_one_occupied"
				}
				else if(element.occupancy_status === "Vacant"){
					sts_bg_class = "card_one_vocant"
				}
				else{
					sts_bg_class = "card_one_cleaning"
				}
				bed += `
				<div class="${sts_bg_class}">
				<div class="bed_icon">
				  <span><i class="fa fa-bed"></i></span>
				</div>
				<span class="bed_tex">${element.name}</span>
				<span class="bed_tex">${element.occupancy_status}</span>
			  </div>
				`
			});
			// console.log(bed)
			let beds = `
			
			<div class="room1 mobile">
			<h1>${room_name}</h1>
			<div class="my_main_cards">
			
	  
			 
			${bed}
			
	  
			</div>
		  </div>
			`
			// console.log(bed)
			// Append beds to rooms section
			$('#room').empty()
			
			$(beds).appendTo('#room')
			console.log(beds)
		})
	}