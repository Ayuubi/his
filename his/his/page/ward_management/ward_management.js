console.log("is this working?")

// .......


frappe.pages['ward-management'].on_page_load = function (wrapper) {
    new WardManagement(wrapper)
}


WardManagement = Class.extend(
    
    
    {
        init: function (wrapper) {
            // .....intan ayan kusoo dary
            this.xValues4 = []
            this.yValues4 = []
            // ... dhamaad inta aan kusoo dary
            this.page = frappe.ui.make_app_page({
              
                parent: wrapper,
                title: "Ward Management",
                single_column: true
            });
            $('.page-head').hide()
            this.make()

            // this.make_grouping_btn()
            // this.grouping_cols()
        },
        make: function () {
            let me = this
            frappe.call({
				
                method: 'his.api.ipd_dashboard.bed_status',
                
                callback: function(data) {
                    
                        let xValues2 = ["Occupied", "In Cleaning", "Discharge Ordered", "Vacant"];
                        let yValues2 = [];
                        let barColors2 = ["#b91d47", "#ffff00", "#ffa500", "#1e7145"];
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


            $(frappe.render_template("ward_management", me)).appendTo(me.page.main)
            let room_list = ``
            let ul_nav = $('#nav_ul').empty()
            let room_sel = ''
            let room = ''
            frappe.db.get_list('Healthcare Service Unit Type',
                {
                    fields: ['name', 'patient'],
                    filters: {
                        type: "IPD"
                    },
                    limit: 1000
                }).then(records => {
                    records.forEach((element, index) => {
                        if (index == 0) {
                            room = element.name
                        }
                //         room_list += `
				// 	<li>
				// 	<span class="bed_icon__"><i class="fa fa-bed"></i></span>
				// 	<a  style = 'color: black;' class = "room_selec" id = "${element.name}">${element.name}</a>
				//   </li>
				// 	`
                    })
                    $(room_list).appendTo(nav_ul)
                    get_beds(room)

                    room_sel = $(".room_selec")
                    room_sel.click(e => {
                        let room_name = e.target.id
                        get_beds(room_name)
                        // get_patient(room_name)
                        // 
                        // alert()
                        // console.log("this is ",e.target.id)





                    })

                })


    





        },

        

  
    })
    


// function get_patient(room_name){
// 	frappe.db.get_list('Inpatient Record', {
// 		fields: ['patient_name', 'bed'],
// 		filters: {
// 			room: room_name,

// 		}
// 	}).then(records => {
// 		// console.log(records);
// 		let bed = ``
// 		let sts_bg_class= "card_one_occupied"
// 		btn=``
// 		records.forEach(element => {
// 			if(element.occupancy_status === "Occupied"){
// 				sts_bg_class = "card_one_occupied"
// 				btn = ''
// 			}
// 			else if(element.occupancy_status === "Vacant"){
// 				sts_bg_class = "card_one_vocant"
// 				btn =''
// 			}

// 			else{
// 				sts_bg_class = "card_one_cleaning"
// 			}
// 			if(element.occupancy_status === "In Cleaning"){
// 				// alert(element.name)
// 					// sts_bg_class = "card_one_vocant_single"
// 					btn = `<button class="btn btn-warning mb-3" style="color:white" onclick = "ready('${element.name}')"> Ready </button>`
// 				}
// 			bed += `
// 			<div class="${sts_bg_class}">
// 			<div class="bed_icon">
// 			  <span><i class="fa fa-bed"></i></span>
// 			</div>
// 			<span class="bed_tex">${element.occupancy_status}</span>
// 			<span class="bed_tex">${element.patient_name}</span>
// 			<span class="bed_tex">${element.bed}</span>


// 			${btn}
// 		  </div>
// 			`

// 		});
// 		// console.log(bed)
// 		let beds = `

// 		<div class="room1 mobile">
// 		<h1>${room_name}</h1>
// 		<div class="my_main_cards">



// 		${bed}


// 		</div>
// 	  </div>
// 		`

// 		// Append beds to rooms section
// 		$('#room').empty()
// 		$(beds).appendTo('#room')

// 	})

// }

// .... midka aan xiray maanta 20-11-2024

// function get_beds(room_name) {
//     frappe.db.get_list('Healthcare Service Unit', {
//         fields: ['name', 'occupancy_status', 'patient'],
//         filters: {
//             service_unit_type: room_name
//         },
//         limit: 1000
//     }).then(records => {
//         // console.log(records);
//         let bed = ``
//         let sts_bg_class = "card_one_occupied"
//         btn = ``


//         records.forEach(element => {
//             if (element.occupancy_status === "Occupied") {




//                 sts_bg_class = "card_one_occupied"
//                 btn = ''




//                 // get_patient(room_name)


//             }
//             else if (element.occupancy_status === "Vacant") {
//                 sts_bg_class = "card_one_vocant"
//                 btn = ''
//             }

//             else {
//                 sts_bg_class = "card_one_cleaning"
//             }
//             if (element.occupancy_status === "In Cleaning") {
//                 // alert(element.name)
//                 // sts_bg_class = "card_one_vocant_single"
//                 btn = `<button class="btn btn-warning mb-3" style="color:white" onclick = "ready('${element.name}')"> Ready </button>`
//             }

//             bed += `
// 				<div class="${sts_bg_class}">
// 				<div class="bed_icon">
// 				  <span><i class="fa fa-bed"></i></span>
// 				</div>
				
// 				<span class="bed_tex">${element.name}</span>
// 				<span class="bed_tex">${element.occupancy_status}</span>
// 				<span class="bed_tex">${element.patient || ""}</span>
// 				${btn}
// 			  </div>
// 				`
//         });
//         // console.log(bed)
//         let beds = `
			
// 			<div class="room1 mobile">
// 			<h1>${room_name}</h1>
// 			<div class="my_main_cards">
			
	  
			 
// 			${bed}
			
	  
// 			</div>
// 		  </div>
// 			`

//         // Append beds to rooms section
//         $('#room').empty()
//         $(beds).appendTo('#room')

//     })

// }

//  ........ kan waa mid practice saxan

function get_beds() {
    frappe.db.get_list('Healthcare Service Unit Type', {
        fields: ['name'],
        filters: { type: "IPD" },
        limit: 1000
    }).then(rooms => {
        let roomsHTML = ``; // To store all room and bed HTML

        let roomPromises = rooms.map(room => {
            return frappe.db.get_list('Healthcare Service Unit', {
                fields: ['name', 'occupancy_status', 'patient'],
                filters: { service_unit_type: room.name },
                limit: 1000
            }).then(beds => {
                // Generate bed HTML for each room
                let bedHTML = ``;
                let patientName;
               

                beds.forEach(bed => {
                    let sts_bg_class = "card_one_occupied";
                    frappe.db.get_value("Patient", bed.patient, "patient_name")
                    .then(response => {
                     patientName = response.message ? response.message.patient_name : "jj";
                        // document.getElementById(`patient-name-${bed.name}`).innerText = patientName;
                        console.log(patientName)
                    })

                    let btn = ``;
                    // console.log(`Bed Name: ${bed.name}, Status: ${bed.occupancy_status}`);
                    
                    if (bed.occupancy_status === "Occupied") {
                        sts_bg_class = "card_one_occupied";
                    } else if (bed.occupancy_status === "Vacant") {
                        sts_bg_class = "card_one_vocant";
                    } else if (bed.occupancy_status === "In Cleaning") {
                        console.log('value of status', bed.occupancy_status)
                       
                        btn = `<button class="btn btn-warning mb-3" style="color:white" onclick="ready('${bed.name}')">Ready</button>`;
                    }else if(bed.occupancy_status == 'Discharge Ordered'){
                        sts_bg_class = "card_discharge"

                    }
                        
                   
                        bedHTML += `
                            <div class="${sts_bg_class}">
                                <div class="bed_icon">
                                    <span><i class="fa fa-bed"></i></span>
                                </div>
                                <span class="bed_tex">${bed.name}</span>
                                <span class="bed_tex">${bed.occupancy_status}</span>
                                <span class="bed_tex">${bed.patient || ""}</span>
                                <span class="bed_tex" id = "patientNamePlaceholder"></span> 
                                ${btn}
                            </div>
                        `;

                        setTimeout(() => {
                            document.getElementById('patientNamePlaceholder').textContent = patientName || "";
                        }, 1000);
                   // This will wait for 1 second before executing the code inside
                    
                    
                });

                // Append the room and its beds to the main HTML
                roomsHTML += `
                    <div class="room_block">
                        <h2 style="color: black; margin-bottom: 10px;">${room.name}</h2>
                        <div class="my_main_cards">
                            ${bedHTML}
                        </div>
                    </div>
                `;
            });
            
        });

        // Wait for all room data to be processed
        Promise.all(roomPromises).then(() => {
            $('#room').empty(); // Clear existing content
            $(roomsHTML).appendTo('#room'); // Add new content
        });
    });
}

// Call the function to automatically display all rooms and beds
get_beds();





function ready(bed) {
    frappe.call({
        method: "his.api.ward_management.ready", //dotted path to server method
        args: {
            "bed": bed
        },
        callback: function (r) {
            // frappe.msgprint(r)
            frappe.utils.play_sound("submit")
            frappe.show_alert({
                message: __('Bed: ' + bed + " Vacanted Successfully!!"),
                indicator: 'green',

            }, 5);
            location.reload();

        }
    });
}
