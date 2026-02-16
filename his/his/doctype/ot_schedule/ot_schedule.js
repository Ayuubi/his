// Copyright (c) 2016, ESS LLP and contributors
// For license information, please see license.txt
frappe.provide('erpnext.queries');
frappe.ui.form.on('OT Schedule', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Vital Signs': 'Vital Signs',
			'Patient Encounter': 'Patient Encounter'
		};
	},

	onload: function(frm) {


		
			var filters = [["OT Schedule", "appointment_date", "=", frappe.datetime.get_today()]];
			listview.filter_area.add(filters);
		if (frm.is_new()) {
			frm.set_value('appointment_time', null);
			frm.disable_save();
		}
		get_history(frm.doc.patient , "vitals")
	},
	

	refresh: function(frm) {

		
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

	

		frm.set_query('patient', function() {
			return {
				filters: { 'status': 'Active' }
			};
		});
		if(frm.doc.status=="Scheduled"){
		frm.add_custom_button(__("Cancel"), function(){
			frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to to cancel <strong>${frm.doc.patient_name}</strong> ?`,
			() => {
			frappe.db.get_value("Patient",frm.doc.patient,"inpatient_status").then(
				res => {
					if(res.message.inpatient_status == "Admitted"){
						frappe.db.set_value("Inpatient Record",frm.doc.inpatient_record,"inpatient_status","Cancelled")
					}
					frm.set_value("status","Cancelled")
					frm.save();
				}
				
				)
			},)
		})
		// -------------------------------------------------------------------------------------------------
		 var btn_operation=frm.add_custom_button(__("Operation"), function(){

			if(frm.doc.clinical_procedure){
					// frappe.set_route("Consent Surgery Form" , )
					frappe.set_route('Form', 'Clinical Procedure', frm.doc.clinical_procedure);
				}
			else {
			frappe.new_doc("Clinical Procedure", 
				{
					"procedure_template": frm.doc.procedure_template, 
					"patient": frm.doc.patient, 
					"practitioner": frm.doc.practitioner, 
					"ot_schedule": frm.doc.name 
				}
			)
		}

		
		})
		btn_operation.addClass("btn-primary")
	}
		// if (!frm.is_new()) {
		// 	frm.add_custom_button(__('Print'), function(){
		// 		  frappe.call({
		// 			  method: "his.api.api.get_print_html",
		// 			  args:{
		// 				  patient:frm.doc.patient,
		// 				  clinical_procedure:frm.doc.procedure_template,
		// 			  },
		// 			  callback: function(r) {
		// 							var x = window.open();
		// 							  x.document.open().write(r.message);
		// 							  // console.log(x)
		// 			  }
		// 		  });
		// 	  });
		// 	}


		// var Aneasthesia_btn=  frm.add_custom_button(__("Aneasthesia"), function(){
		// 	frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Create Aneasthesia for <strong>${frm.doc.patient_name}</strong> ?`,
		// 	() => {
		// 		// action to perform if Yes is selected
		// 		frappe.call({
		// 			method: 'his.api.clinical_procedure.aneasthesia_sheet',
		// 			args: {
		// 				docname: frm.doc.name,
		// 				patient: frm.doc.patient,
		// 				procedure_template: frm.doc.procedure_template,
		// 				operative_doctor: frm.doc.practitioner
		// 			},
		// 			callback: function(r) {
		// 				//frappe.msgprint(r)
		// 				console.log(r)
		// 				frappe.utils.play_sound("submit")
		// 				frappe.show_alert({
		// 					message:__('Aneasthesia Created '),
		// 					indicator:'green',
		// 				}, 5);
		// 				// frm.set_value('aneasthesia', 1)
		// 				// frm.save("Update")
		// 				// frm.reload_doc()
		// 				// alert(frm.doc.aneasthesia)
		// 			}
		// 		});
		// 		},)
		// 	});
		// 	Aneasthesia_btn.addClass('btn-success');
		// frm.set_query('practitioner', function() {
		// 	if (frm.doc.department) {
		// 		return {
		// 			filters: {
		// 				'department': frm.doc.department
		// 			}
		// 		};
		// 	}
		// });

		frm.set_query('service_unit', function() {
			return {
				query: 'healthcare.controllers.queries.get_healthcare_service_units',
				filters: {
					company: frm.doc.company,
					inpatient_record: frm.doc.inpatient_record
				}
			};
		});

		frm.set_query('therapy_plan', function() {
			return {
				filters: {
					'patient': frm.doc.patient
				}
			};
		});

		frm.trigger('set_therapy_type_filter');

		// if (frm.is_new()) {
		// 	frm.page.set_primary_action(__('Check Availability'), function() {
		// 		if (!frm.doc.patient) {
		// 			frappe.msgprint({
		// 				title: __('Not Allowed'),
		// 				message: __('Please select Patient first'),
		// 				indicator: 'red'
		// 			});
		// 		} else {
		// 			frappe.call({
		// 				method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.check_payment_fields_reqd',
		// 				args: { 'patient': frm.doc.patient },
		// 				callback: function(data) {
		// 					if (data.message == true) {
		// 						if (frm.doc.mode_of_payment && frm.doc.paid_amount) {
		// 							check_and_set_availability(frm);
		// 						}
		// 						if (!frm.doc.mode_of_payment) {
		// 							frappe.msgprint({
		// 								title: __('Not Allowed'),
		// 								message: __('Please select a Mode of Payment first'),
		// 								indicator: 'red'
		// 							});
		// 						}
		// 						if (!frm.doc.paid_amount) {
		// 							frappe.msgprint({
		// 								title: __('Not Allowed'),
		// 								message: __('Please set the Paid Amount first'),
		// 								indicator: 'red'
		// 							});
		// 						}
		// 					} else {
		// 						check_and_set_availability(frm);
		// 					}
		// 				}
		// 			});
		// 		}
		// 	});
		// } else {
		// 	frm.page.set_primary_action(__('Save'), () => frm.save());
		// }

		// if (frm.doc.patient) {
		// 	frm.add_custom_button(__('Patient History'), function() {
		// 		frappe.route_options = { 'patient': frm.doc.patient };
		// 		frappe.set_route('patient_history');
		// 	}, __('View'));
		// }

		if (frm.doc.status == 'Not Scheduled') {
			frm.add_custom_button(__('Cancel'), function() {
				update_status(frm, 'Cancelled');
			});
			frm.add_custom_button(__('Schedule'), function() {
				check_and_set_availability(frm);
			});

			
			// else if (frm.doc.therapy_type) {
			// 	frm.add_custom_button(__('Therapy Session'), function() {
			// 		frappe.model.open_mapped_doc({
			// 			method: 'healthcare.healthcare.doctype.therapy_session.therapy_session.create_therapy_session',
			// 			frm: frm,
			// 		})
			// 	}, 'Create');
			// } else {
			// 	frm.add_custom_button(__('Patient Encounter'), function() {
			// 		frappe.model.open_mapped_doc({
			// 			method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.make_encounter',
			// 			frm: frm,
			// 		});
			// 	}, __('Create'));
			// }

			// frm.add_custom_button(__('Vital Signs'), function() {
			// 	create_vital_signs(frm);
			// }, __('Create'));
		}

		if (frm.doc.procedure_template) {
			// if (frm.doc.status == 'Scheduled'){
			// 	var Aneasthesia_btn=  frm.add_custom_button(__("Aneasthesia"), function(){
			// 		frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Create Aneasthesia for <strong>${frm.doc.patient_name}</strong> ?`,
			// 		() => {
			// 			// action to perform if Yes is selected
			// 			frappe.call({
			// 				method: 'his.api.clinical_procedure.aneasthesia_sheet',
			// 				args: {
			// 					docname: frm.doc.name,
			// 					patient: frm.doc.patient,
			// 					procedure_template: frm.doc.procedure_template,
			// 					operative_doctor: frm.doc.practitioner
			// 				},
			// 				callback: function(r) {
			// 					//frappe.msgprint(r)
			// 					console.log(r)
			// 					frappe.utils.play_sound("submit")
			// 					frappe.show_alert({
			// 						message:__('Aneasthesia Created '),
			// 						indicator:'green',
			// 					}, 5);
			// 					frm.set_value('status', 'In Progress')
			// 					frm.save()
			// 				}
			// 			});
			// 			},)
			// 		});
			// 		Aneasthesia_btn.addClass('btn-success');
			// }
			// frm.add_custom_button(__('Aneasthesia'), function() {
			// 	frappe.call({
			// 		method: "his.api.clinical_procedure.aneasthesia_sheet",
					// args: {
					// 	patient: frm.doc.patient,
					// 	procedure_template: frm.doc.procedure_template,
					// 	operative_doctor: frm.doc.practitioner
					// },
			// 	 callback: function(r) {
					 
			//  //frappe.msgprint(r)
			//  console.log(r)
			//  frappe.utils.play_sound("submit")

			//  frappe.show_alert({
			// 	 message:__('Aneasthesia Sheet Created Succesfully'),
			// 	 indicator:'green',
				 
			//  }, 5);}})
			// },);
		} 

		if (!frm.is_new()){
			var btn1 = frm.add_custom_button('Requests', () => {
				frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.consultant, "source_order": "IPD" })
		
			})
			frm.add_custom_button('Print Consent Form', () => {
				// let url= `${frappe.urllib.get_base_url()}/printview?doctype=Surgery%20Preparation&name=${frm.doc.name}&trigger_print=1&format=Surgery%20Preparation%20Consent&no_letterhead=0&letterhead=logo&settings=%7B%7D&_lang=en`;
				//      window.open(url, '_blank');
				if(frm.doc.consent_form){
					// frappe.set_route("Consent Surgery Form" , )
					frappe.set_route('Form', 'Consent Surgery Form', frm.doc.consent_form);
				}
				else{
					frappe.new_doc("Consent Surgery Form" , 
						{
							"patient" : frm.doc.patient , 
							"surgery_type" : frm.doc.procedure_template , 
							"surgery_preparation" : frm.doc.name, 
							"practitioner": frm.doc.practitioner,
							"reference_dt": frm.doc.doctype,
							"reference_name": frm.doc.name
						}
					)
		
				}
			
			})
		}
	},

	patient: function(frm) {
		if (frm.doc.patient) {
			frm.trigger('toggle_payment_fields');
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Patient',
					name: frm.doc.patient
				},
				callback: function(data) {
					let age = null;
					if (data.message.dob) {
						age = calculate_age(data.message.dob);
					}
					frappe.model.set_value(frm.doctype, frm.docname, 'patient_age', age);
				}
			});
		} else {
			frm.set_value('patient_name', '');
			frm.set_value('patient_sex', '');
			frm.set_value('patient_age', '');
			frm.set_value('inpatient_record', '');
		}
	},

	practitioner: function(frm) {
		if (frm.doc.practitioner) {
			frm.events.set_payment_details(frm);
		}
	},

	appointment_type: function(frm) {
		if (frm.doc.appointment_type) {
			frm.events.set_payment_details(frm);
		}
	},

	set_payment_details: function(frm) {
		frappe.db.get_single_value('Healthcare Settings', 'automate_appointment_invoicing').then(val => {
			if (val) {
				frappe.call({
					method: 'healthcare.healthcare.utils.get_service_item_and_practitioner_charge',
					args: {
						doc: frm.doc
					},
					callback: function(data) {
						if (data.message) {
							frappe.model.set_value(frm.doctype, frm.docname, 'paid_amount', data.message.practitioner_charge);
							frappe.model.set_value(frm.doctype, frm.docname, 'billing_item', data.message.service_item);
						}
					}
				});
			}
		});
	},

	therapy_plan: function(frm) {
		frm.trigger('set_therapy_type_filter');
	},

	set_therapy_type_filter: function(frm) {
		if (frm.doc.therapy_plan) {
			frm.call('get_therapy_types').then(r => {
				frm.set_query('therapy_type', function() {
					return {
						filters: {
							'name': ['in', r.message]
						}
					};
				});
			});
		}
	},

	therapy_type: function(frm) {
		if (frm.doc.therapy_type) {
			frappe.db.get_value('Therapy Type', frm.doc.therapy_type, 'default_duration', (r) => {
				if (r.default_duration) {
					frm.set_value('duration', r.default_duration)
				}
			});
		}
	},

	get_procedure_from_encounter: function(frm) {
		get_prescribed_procedure(frm);
	},

	toggle_payment_fields: function(frm) {
		frappe.call({
			method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.check_payment_fields_reqd',
			args: { 'patient': frm.doc.patient },
			callback: function(data) {
				if (data.message.fee_validity) {
					// if fee validity exists and automated appointment invoicing is enabled,
					// show payment fields as non-mandatory
					frm.toggle_display('mode_of_payment', 0);
					frm.toggle_display('paid_amount', 0);
					frm.toggle_display('billing_item', 0);
					frm.toggle_reqd('mode_of_payment', 0);
					frm.toggle_reqd('paid_amount', 0);
					frm.toggle_reqd('billing_item', 0);
				} else if (data.message) {
					frm.toggle_display('mode_of_payment', 0);
					frm.toggle_display('paid_amount', 1);
					frm.toggle_display('billing_item', 1);
					frm.toggle_reqd('mode_of_payment', 1);
					frm.toggle_reqd('paid_amount', 1);
					frm.toggle_reqd('billing_item', 1);
				} else {
					// if automated appointment invoicing is disabled, hide fields
					frm.toggle_display('mode_of_payment', data.message ? 0 : 0);
					frm.toggle_display('paid_amount', data.message ? 1 : 0);
					frm.toggle_display('billing_item', data.message ? 1 : 0);
					frm.toggle_reqd('mode_of_payment', data.message ? 1 : 0);
					frm.toggle_reqd('paid_amount', data.message ? 1 : 0);
					frm.toggle_reqd('billing_item', data.message ? 1 : 0);
				}
			}
		});
	},

	get_prescribed_therapies: function(frm) {
		if (frm.doc.patient) {
			frappe.call({
				method: "healthcare.healthcare.doctype.patient_appointment.patient_appointment.get_prescribed_therapies",
				args: { patient: frm.doc.patient },
				callback: function(r) {
					if (r.message) {
						show_therapy_types(frm, r.message);
					} else {
						frappe.msgprint({
							title: __('Not Therapies Prescribed'),
							message: __('There are no Therapies prescribed for Patient {0}', [frm.doc.patient.bold()]),
							indicator: 'blue'
						});
					}
				}
			});
		}
	}
});

let check_and_set_availability = function(frm) {
	let selected_slot = null;
	let service_unit = null;
	let duration = null;
	let add_video_conferencing = null;
	let overlap_appointments = null;

	show_availability();

	function show_empty_state(practitioner, appointment_date) {
		frappe.msgprint({
			title: __('Not Available'),
			message: __('Healthcare Practitioner {0} not available on {1}', [practitioner.bold(), appointment_date.bold()]),
			indicator: 'red'
		});
	}

	function show_availability() {
		let selected_practitioner = '';
		let d = new frappe.ui.Dialog({
			title: __('Available slots'),
			fields: [
				{ fieldtype: 'Link', options: 'Medical Department', reqd: 1, fieldname: 'department', label: 'Medical Department' },
				{ fieldtype: 'Column Break' },
				{ fieldtype: 'Link', options: 'Healthcare Practitioner', reqd: 1, fieldname: 'practitioner', label: 'Healthcare Practitioner' },
				{ fieldtype: 'Column Break' },
				{ fieldtype: 'Date', reqd: 1, fieldname: 'appointment_date', label: 'Date', min_date: new Date(frappe.datetime.get_today()) },
				{ fieldtype: 'Section Break' },
				{ fieldtype: 'HTML', fieldname: 'available_slots' }

			],
			primary_action_label: __('Book'),
			primary_action: function() {
				frm.set_value('appointment_time', selected_slot);
				add_video_conferencing = add_video_conferencing && !d.$wrapper.find(".opt-out-check").is(":checked")
					&& !overlap_appointments

				// frm.set_value('add_video_conferencing', add_video_conferencing);

				if (!frm.doc.duration) {
					frm.set_value('duration', duration);
				}

				frm.set_value('practitioner', d.get_value('practitioner'));
				frm.set_value('department', d.get_value('department'));
				frm.set_value('appointment_date', d.get_value('appointment_date'));

				if (service_unit) {
					frm.set_value('service_unit', service_unit);
				}

				d.hide();
				frm.enable_save();
				frm.save();
				d.get_primary_btn().attr('disabled', true);
				frm.set_value("status" , "Scheduled")
			}
		});

		d.set_values({
			'department': frm.doc.department,
			'practitioner': frm.doc.practitioner,
			'appointment_date': frm.doc.appointment_date
		});

		let selected_department = frm.doc.department;

		d.fields_dict['department'].df.onchange = () => {
			if (selected_department != d.get_value('department')) {
				d.set_values({
					'practitioner': ''
				});
				selected_department = d.get_value('department');
			}
			if (d.get_value('department')) {
				d.fields_dict.practitioner.get_query = function() {
					return {
						filters: {
							'department': selected_department
						}
					};
				};
			}
		};

		// disable dialog action initially
		d.get_primary_btn().attr('disabled', true);

		// Field Change Handler

		let fd = d.fields_dict;

		d.fields_dict['appointment_date'].df.onchange = () => {
			show_slots(d, fd);
		};
		d.fields_dict['practitioner'].df.onchange = () => {
			if (d.get_value('practitioner') && d.get_value('practitioner') != selected_practitioner) {
				selected_practitioner = d.get_value('practitioner');
				show_slots(d, fd);
			}
		};

		d.show();
	}

	function show_slots(d, fd) {
		if (d.get_value('appointment_date') && d.get_value('practitioner')) {
			fd.available_slots.html('');
			frappe.call({
				method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.get_availability_data',
				args: {
					practitioner: d.get_value('practitioner'),
					date: d.get_value('appointment_date')
				},
				callback: (r) => {
					let data = r.message;
					if (data.slot_details.length > 0) {
						let $wrapper = d.fields_dict.available_slots.$wrapper;

						// make buttons for each slot
						let slot_html = get_slots(data.slot_details, d.get_value('appointment_date'));

						$wrapper
							.css('margin-bottom', 0)
							.addClass('text-center')
							.html(slot_html);

						// highlight button when clicked
						$wrapper.on('click', 'button', function() {
							let $btn = $(this);
							$wrapper.find('button').removeClass('btn-outline-primary');
							$btn.addClass('btn-outline-primary');
							selected_slot = $btn.attr('data-name');
							service_unit = $btn.attr('data-service-unit');
							duration = $btn.attr('data-duration');
							add_video_conferencing = parseInt($btn.attr('data-tele-conf'));
							overlap_appointments = parseInt($btn.attr('data-overlap-appointments'));
							// show option to opt out of tele conferencing
							if ($btn.attr('data-tele-conf') == 1) {
								if (d.$wrapper.find(".opt-out-conf-div").length) {
									d.$wrapper.find(".opt-out-conf-div").show();
								} else {
									overlap_appointments ?
										d.footer.prepend(
											`<div class="opt-out-conf-div ellipsis text-muted" style="vertical-align:text-bottom;">
												<label>
													<span class="label-area">
													${__("Video Conferencing disabled for group consultations")}
													</span>
												</label>
											</div>`
										)
									:
										d.footer.prepend(
											`<div class="opt-out-conf-div ellipsis" style="vertical-align:text-bottom;">
											<label>
												<input type="checkbox" class="opt-out-check"/>
												<span class="label-area">
												${__("Do not add Video Conferencing")}
												</span>
											</label>
										</div>`
										);
								}
							} else {
								d.$wrapper.find(".opt-out-conf-div").hide();
							}

							// enable primary action 'Book'
							d.get_primary_btn().attr('disabled', null);
						});

					} else {
						//	fd.available_slots.html('Please select a valid date.'.bold())
						show_empty_state(d.get_value('practitioner'), d.get_value('appointment_date'));
					}
				},
				freeze: true,
				freeze_message: __('Fetching Schedule...')
			});
		} else {
			fd.available_slots.html(__('Appointment date and Healthcare Practitioner are Mandatory').bold());
		}
	}

	function get_slots(slot_details, appointment_date) {
		let slot_html = '';
		let appointment_count = 0;
		let disabled = false;
		let start_str, slot_start_time, slot_end_time, interval, count, count_class, tool_tip, available_slots;

		slot_details.forEach((slot_info) => {
			slot_html += `<div class="slot-info">
				<span><b>
				${__('Practitioner Schedule: ')} </b> ${slot_info.slot_name}
					${slot_info.tele_conf && !slot_info.allow_overlap ? '<i class="fa fa-video-camera fa-1x" aria-hidden="true"></i>' : ''}
				</span><br>
				<span><b> ${__('Service Unit: ')} </b> ${slot_info.service_unit}</span>`;

			if (slot_info.service_unit_capacity) {
				slot_html += `<br><span> <b> ${__('Maximum Capacity:')} </b> ${slot_info.service_unit_capacity} </span>`;
			}

			slot_html += '</div><br>';

			slot_html += slot_info.avail_slot.map(slot => {
				appointment_count = 0;
				disabled = false;
				count_class = tool_tip = '';
				start_str = slot.from_time;
				slot_start_time = moment(slot.from_time, 'HH:mm:ss');
				slot_end_time = moment(slot.to_time, 'HH:mm:ss');
				interval = (slot_end_time - slot_start_time) / 60000 | 0;

				// restrict past slots based on the current time.
				let now = moment();
				if((now.format("YYYY-MM-DD") == appointment_date) && slot_start_time.isBefore(now)){
					disabled = true;
				} else {
					// iterate in all booked appointments, update the start time and duration
					slot_info.appointments.forEach((booked) => {
						let booked_moment = moment(booked.appointment_time, 'HH:mm:ss');
						let end_time = booked_moment.clone().add(booked.duration, 'minutes');

						// Deal with 0 duration appointments
						if (booked_moment.isSame(slot_start_time) || booked_moment.isBetween(slot_start_time, slot_end_time)) {
							if (booked.duration == 0) {
								disabled = true;
								return false;
							}
						}

						// Check for overlaps considering appointment duration
						if (slot_info.allow_overlap != 1) {
							if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
								// There is an overlap
								disabled = true;
								return false;
							}
						} else {
							if (slot_start_time.isBefore(end_time) && slot_end_time.isAfter(booked_moment)) {
								appointment_count++;
							}
							if (appointment_count >= slot_info.service_unit_capacity) {
								// There is an overlap
								disabled = true;
								return false;
							}
						}
					});
				}

				if (slot_info.allow_overlap == 1 && slot_info.service_unit_capacity > 1) {
					available_slots = slot_info.service_unit_capacity - appointment_count;
					count = `${(available_slots > 0 ? available_slots : __('Full'))}`;
					count_class = `${(available_slots > 0 ? 'badge-success' : 'badge-danger')}`;
					tool_tip =`${available_slots} ${__('slots available for booking')}`;
				}

				return `
					<button class="btn btn-secondary" data-name=${start_str}
						data-duration=${interval}
						data-service-unit="${slot_info.service_unit || ''}"
						data-tele-conf="${slot_info.tele_conf || 0}"
						data-overlap-appointments="${slot_info.service_unit_capacity || 0}"
						style="margin: 0 10px 10px 0; width: auto;" ${disabled ? 'disabled="disabled"' : ""}
						data-toggle="tooltip" title="${tool_tip || ''}">
						${start_str.substring(0, start_str.length - 3)}
						${slot_info.service_unit_capacity ? `<br><span class='badge ${count_class}'> ${count} </span>` : ''}
					</button>`;

			}).join("");

			if (slot_info.service_unit_capacity) {
				slot_html += `<br/><small>${__('Each slot indicates the capacity currently available for booking')}</small>`;
			}
			slot_html += `<br/><br/>`;
		});

		return slot_html;
	}
};

let get_prescribed_procedure = function(frm) {
	if (frm.doc.patient) {
		frappe.call({
			method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.get_procedure_prescribed',
			args: { patient: frm.doc.patient },
			callback: function(r) {
				if (r.message && r.message.length) {
					show_procedure_templates(frm, r.message);
				} else {
					frappe.msgprint({
						title: __('Not Found'),
						message: __('No Prescribed Procedures found for the selected Patient')
					});
				}
			}
		});
	} else {
		frappe.msgprint({
			title: __('Not Allowed'),
			message: __('Please select a Patient first')
		});
	}
};

let show_procedure_templates = function(frm, result) {
	let d = new frappe.ui.Dialog({
		title: __('Prescribed Procedures'),
		fields: [
			{
				fieldtype: 'HTML', fieldname: 'procedure_template'
			}
		]
	});
	let html_field = d.fields_dict.procedure_template.$wrapper;
	html_field.empty();
	$.each(result, function(x, y) {
		let row = $(repl('<div class="col-xs-12" style="padding-top:12px; text-align:center;" >\
		<div class="col-xs-5"> %(encounter)s <br> %(consulting_practitioner)s <br> %(encounter_date)s </div>\
		<div class="col-xs-5"> %(procedure_template)s <br>%(practitioner)s  <br> %(date)s</div>\
		<div class="col-xs-2">\
		<a data-name="%(name)s" data-procedure-template="%(procedure_template)s"\
		data-encounter="%(encounter)s" data-practitioner="%(practitioner)s"\
		data-date="%(date)s"  data-department="%(department)s">\
		<button class="btn btn-default btn-xs">Add\
		</button></a></div></div><div class="col-xs-12"><hr/><div/>', {
			name: y[0], procedure_template: y[1],
			encounter: y[2], consulting_practitioner: y[3], encounter_date: y[4],
			practitioner: y[5] ? y[5] : '', date: y[6] ? y[6] : '', department: y[7] ? y[7] : ''
		})).appendTo(html_field);
		row.find("a").click(function() {
			frm.doc.procedure_template = $(this).attr('data-procedure-template');
			frm.doc.procedure_prescription = $(this).attr('data-name');
			frm.doc.practitioner = $(this).attr('data-practitioner');
			frm.doc.appointment_date = $(this).attr('data-date');
			frm.doc.department = $(this).attr('data-department');
			refresh_field('procedure_template');
			refresh_field('procedure_prescription');
			refresh_field('appointment_date');
			refresh_field('practitioner');
			refresh_field('department');
			d.hide();
			return false;
		});
	});
	if (!result) {
		let msg = __('There are no procedure prescribed for ') + frm.doc.patient;
		$(repl('<div class="col-xs-12" style="padding-top:20px;" >%(msg)s</div></div>', { msg: msg })).appendTo(html_field);
	}
	d.show();
};

let show_therapy_types = function(frm, result) {
	var d = new frappe.ui.Dialog({
		title: __('Prescribed Therapies'),
		fields: [
			{
				fieldtype: 'HTML', fieldname: 'therapy_type'
			}
		]
	});
	var html_field = d.fields_dict.therapy_type.$wrapper;
	$.each(result, function(x, y) {
		var row = $(repl('<div class="col-xs-12" style="padding-top:12px; text-align:center;" >\
		<div class="col-xs-5"> %(encounter)s <br> %(practitioner)s <br> %(date)s </div>\
		<div class="col-xs-5"> %(therapy)s </div>\
		<div class="col-xs-2">\
		<a data-therapy="%(therapy)s" data-therapy-plan="%(therapy_plan)s" data-name="%(name)s"\
		data-encounter="%(encounter)s" data-practitioner="%(practitioner)s"\
		data-date="%(date)s"  data-department="%(department)s">\
		<button class="btn btn-default btn-xs">Add\
		</button></a></div></div><div class="col-xs-12"><hr/><div/>', {
			therapy: y[0],
			name: y[1], encounter: y[2], practitioner: y[3], date: y[4],
			department: y[6] ? y[6] : '', therapy_plan: y[5]
		})).appendTo(html_field);

		row.find("a").click(function() {
			frm.doc.therapy_type = $(this).attr("data-therapy");
			frm.doc.practitioner = $(this).attr("data-practitioner");
			frm.doc.department = $(this).attr("data-department");
			frm.doc.therapy_plan = $(this).attr("data-therapy-plan");
			frm.refresh_field("therapy_type");
			frm.refresh_field("practitioner");
			frm.refresh_field("department");
			frm.refresh_field("therapy-plan");
			frappe.db.get_value('Therapy Type', frm.doc.therapy_type, 'default_duration', (r) => {
				if (r.default_duration) {
					frm.set_value('duration', r.default_duration)
				}
			});
			d.hide();
			return false;
		});
	});
	d.show();
};

let create_vital_signs = function(frm) {
	if (!frm.doc.patient) {
		frappe.throw(__('Please select patient'));
	}
	frappe.route_options = {
		'patient': frm.doc.patient,
		'appointment': frm.doc.name,
		'company': frm.doc.company
	};
	frappe.new_doc('Vital Signs');
};

let update_status = function(frm, status) {
	let doc = frm.doc;
	frappe.confirm(__('Are you sure you want to cancel this appointment?'),
		function() {
			frappe.call({
				method: 'healthcare.healthcare.doctype.patient_appointment.patient_appointment.update_status',
				args: { appointment_id: doc.name, status: status },
				callback: function(data) {
					if (!data.exc) {
						frm.reload_doc();
					}
				}
			});
		}
	);
};

let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};

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
