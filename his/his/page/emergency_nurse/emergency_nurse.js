frappe.pages["emergency-nurse"].on_page_load = function (wrapper) {
	new EmergencyNurse(wrapper);
};

class EmergencyNurse {
	constructor(wrapper) {
		this.wrapper = wrapper;

		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Emergency"),
			single_column: true,
		});

		/*
		 * Emergency DocType fieldnames.
		 */
		this.triage_field = "triage_level";
		this.status_field = "status";

		this.triage_options = [
			"Not Triaged",
			"Red",
			"Yellow",
			"Green",
		];

		this.current_date = frappe.datetime.get_today();
		this.table = null;
		this.realtime_handler = null;
		this.is_loading = false;

		this.make();
		this.bind_realtime();
	}

	make() {
		this.make_filters();
		this.make_body();
		this.setup_data_table();
	}

	make_filters() {
		const me = this;

		this.date_field = this.page.add_field({
			fieldtype: "Date",
			fieldname: "date",
			label: __("Date"),
			default: frappe.datetime.get_today(),

			change() {
				me.current_date =
					me.date_field.get_value() ||
					frappe.datetime.get_today();

				me.setup_data_table();
			},
		});

		this.page.add_button(__("Refresh"), function () {
			me.setup_data_table();
		});
	}

	make_body() {
		this.page.main.html(`
			<div class="emergency-page-wrapper">
				<div
					id="opdorder"
					class="emergency-table"
					style="width: 100%;"
				></div>
			</div>
		`);

		this.add_styles();
	}

	add_styles() {
		if ($("#emergency-nurse-page-style").length) {
			return;
		}

		$("head").append(`
			<style id="emergency-nurse-page-style">
				.emergency-page-wrapper {
					width: 100%;
					padding-top: 10px;
				}

				.emergency-table {
					width: 100%;
					min-height: 300px;
					background: var(--card-bg);
					border: 1px solid var(--border-color);
					border-radius: 8px;
					overflow: hidden;
				}

				.emergency-action-buttons {
					display: flex;
					align-items: center;
					justify-content: center;
					gap: 6px;
					flex-wrap: nowrap;
				}

				.emergency-action-buttons .btn {
					padding: 3px 10px;
					font-size: 11px;
					line-height: 1.4;
					white-space: nowrap;
				}

				.emergency-status-badge {
					display: inline-flex;
					align-items: center;
					justify-content: center;
					min-width: 78px;
					padding: 3px 8px;
					border-radius: 12px;
					font-size: 11px;
					font-weight: 600;
					white-space: nowrap;
				}

				.emergency-status-admitted {
					background: #e5dbff;
					color: #6741d9;
				}

				.emergency-status-discharged {
					background: #d3f9d8;
					color: #2b8a3e;
				}

				.emergency-status-default {
					background: var(--control-bg);
					color: var(--text-muted);
				}

				.emergency-triage-cell {
					display: flex;
					align-items: center;
					justify-content: center;
					width: 100%;
					height: 100%;
					min-height: 28px;
					padding: 3px 8px;
					border-radius: 12px;
					font-size: 11px;
					font-weight: 600;
					cursor: pointer;
					white-space: nowrap;
				}

				.emergency-triage-red {
					background: #ffe3e3;
					color: #c92a2a;
				}

				.emergency-triage-yellow {
					background: #fff3bf;
					color: #8f6b00;
				}

				.emergency-triage-green {
					background: #d3f9d8;
					color: #2b8a3e;
				}

				.emergency-triage-default {
					background: var(--control-bg);
					color: var(--text-muted);
				}

				.tabulator {
					border: none !important;
					background-color: var(--card-bg) !important;
				}

				.tabulator .tabulator-header {
					background-color: var(--subtle-fg) !important;
					border-bottom: 1px solid var(--border-color) !important;
				}

				.tabulator .tabulator-row {
					background-color: var(--card-bg) !important;
					border-bottom: 1px solid var(--border-color) !important;
					border-left: 5px solid transparent !important;
					box-sizing: border-box !important;
				}

				.tabulator .tabulator-row:hover {
					background-color: var(--control-bg) !important;
				}

				.tabulator .tabulator-row.emergency-critical-row {
					border-left: 5px solid #e03131 !important;
				}

				.tabulator .tabulator-row.emergency-yellow-row {
					border-left: 5px solid #f08c00 !important;
				}

				.tabulator .tabulator-row.emergency-green-row {
					border-left: 5px solid #2f9e44 !important;
				}

				.tabulator
				.tabulator-cell
				.tabulator-editing {
					padding: 0 !important;
				}

				@media (max-width: 768px) {
					.emergency-action-buttons {
						flex-direction: column;
					}

					.emergency-action-buttons .btn {
						width: 100%;
					}
				}
			</style>
		`);
	}

	async setup_data_table() {
		if (this.is_loading) {
			return;
		}

		this.is_loading = true;
		this.set_loading(true);

		try {
			const response = await frappe.call({
				method: "his.api.get_orders.get_que_em",
				args: {
					currdate: this.current_date,
				},
				freeze: false,
			});

			const records = Array.isArray(response.message)
				? response.message
				: [];

			const table_data =
				await this.prepare_records(records);

			this.render_table(table_data);
		} catch (error) {
			console.error(
				"Failed to load Emergency queue:",
				error
			);

			this.destroy_table();

			frappe.msgprint({
				title: __("Emergency"),
				message: __(
					"Unable to load the Emergency patient list."
				),
				indicator: "red",
			});
		} finally {
			this.is_loading = false;
			this.set_loading(false);
		}
	}

	async prepare_records(records) {
		const prepared_records = await Promise.all(
			records.map(async (record) => {
				const row = { ...record };

				row.emergency_name =
					row.emergency_name ||
					row.emergency ||
					row.name ||
					"";

				if (!row.patient_age && row.patient) {
					row.patient_age =
						await this.get_patient_age(
							row.patient
						);
				}

				if (
					!row.emergency_name ||
					row.emergency_name === row.patient
				) {
					row.emergency_name =
						await this.find_emergency_name(
							row
						);
				}

				/*
				 * Triage empty ah waxaa loo qaadanayaa
				 * Not Triaged.
				 */
				row.triage_value =
					row[this.triage_field] ||
					row.triage_level ||
					"Not Triaged";

				/*
				* Determine Emergency status.
				* Transfer To IP wuxuu isticmaalaa emergency_status.
				*/
				if (row.emergency_status) {
					row.status_value = row.emergency_status;
				} else if (row[this.status_field]) {
					row.status_value = row[this.status_field];
				} else {
					row.status_value = "Admitted";
				}

				return row;
			})
		);

		/*
		 * Discharged patients kama muuqanayaan active page-ka.
		 * Backend-ku haddii uu soo celiyoba JS-ku wuu sifeynayaa.
		 */
		return prepared_records.filter((row) => {
			const status = this.normalize_value(
				row.status_value
	);
			return (
				status !== "discharged" &&
				status !== "transferred"
			);
		});
	}

	async get_patient_age(patient) {
		if (!patient) {
			return "";
		}

		try {
			const result =
				await frappe.db.get_value(
					"Patient",
					patient,
					"dob"
				);

			const dob =
				result &&
				result.message &&
				result.message.dob
					? result.message.dob
					: null;

			return calculate_age(dob);
		} catch (error) {
			console.error(
				`Could not calculate age for patient ${patient}:`,
				error
			);

			return "";
		}
	}

	async find_emergency_name(row) {
		if (!row.patient) {
			return "";
		}

		const filters = {
			patient: row.patient,
		};

		if (row.encounter_date) {
			filters.encounter_date =
				row.encounter_date;
		}

		try {
			const emergency_records =
				await frappe.db.get_list(
					"Emergency",
					{
						filters,
						fields: [
							"name",
							"modified",
						],
						order_by:
							"modified desc",
						limit: 1,
					}
				);

			if (
				emergency_records &&
				emergency_records.length
			) {
				return emergency_records[0].name;
			}

			return "";
		} catch (error) {
			console.error(
				"Could not find Emergency record:",
				error
			);

			return "";
		}
	}

	render_table(data) {
		const me = this;

		this.destroy_table();

		const columns = [
			{
				title: __("No"),
				formatter: "rownum",
				width: 60,
				hozAlign: "center",
				headerSort: false,
			},
			{
				title: __("PID"),
				field: "patient",
				minWidth: 130,
				headerFilter: "input",
			},
			{
				title: __("Patient Name"),
				field: "patient_name",
				minWidth: 180,
				headerFilter: "input",
			},
			{
				title: __("Sex"),
				field: "patient_sex",
				minWidth: 90,
				hozAlign: "center",
				headerFilter: "input",
			},
			{
				title: __("Age"),
				field: "patient_age",
				width: 70,
				maxWidth: 70,
				hozAlign: "center",
				headerFilter: "input",
			},
			{
				title: __("Diagnosis"),
				field: "diagnosis",
				width: 220,
				maxWidth: 220,
				minWidth: 150,
				headerFilter: "input",
				formatter: function(cell){
					const value = cell.getValue() || "";
					const formatted = value.split(',').map(v => v.trim()).join('<br>');
					return `<div style="white-space:normal; word-wrap:break-word; overflow-wrap:break-word; line-height:1.4; padding:4px 0;">${formatted}</div>`;
				}
			},
			{
				title: __("Date"),
				field: "encounter_date",
				minWidth: 110,
				headerFilter: "input",

				formatter(cell) {
					return me.format_date(
						cell.getValue()
					);
				},
			},
			
			{
				title: __("Triage"),
				field: "triage_value",
				minWidth: 130,
				hozAlign: "center",
				headerFilter: "input",

				editor: "list",

				editorParams: {
					values: this.triage_options,
					autocomplete: false,
					allowEmpty: false,
					listOnEmpty: true,
				},

				formatter(cell) {
					return me.format_triage(
						cell.getValue()
					);
				},

				cellEdited(cell) {
					me.update_triage(cell);
				},
			},
			{
				title: __("Status"),
				field: "status_value",
				minWidth: 110,
				hozAlign: "center",
				headerFilter: "input",

				formatter(cell) {
					return me.format_status(
						cell.getValue()
					);
				},
			},
			{
				title: __("Action"),
				field: "action",
				minWidth: 175,
				hozAlign: "center",
				headerSort: false,

				formatter() {
					return `
						<div class="emergency-action-buttons">
							<button
								type="button"
								class="btn btn-xs btn-default emergency-open-btn"
							>
								${__("Open")}
							</button>

							<button
								type="button"
								class="btn btn-xs btn-danger emergency-discharge-btn"
							>
								${__("Discharge")}
							</button>
						</div>
					`;
				},

				cellClick(event, cell) {
					event.preventDefault();
					event.stopPropagation();

					const row_data =
						cell.getRow().getData();

					if (
						$(event.target).closest(
							".emergency-open-btn"
						).length
					) {
						me.open_emergency(
							row_data
						);

						return;
					}

					if (
						$(event.target).closest(
							".emergency-discharge-btn"
						).length
					) {
						me.discharge_patient(
							row_data,
							cell.getRow()
						);
					}
				},
			},
			{
				title: __("Balance"),
				field: "balance",
				minWidth: 100,
				hozAlign: "right",
				formatter: function(cell){
					const value = cell.getValue() || 0;
					const color = value === 0 ? "#e03131" : "#2f9e44";
					return `<div style="color:${color}; font-weight:600;text-align:center;">${value.toLocaleString()}</div>`;
				}
			}
		];

		

		this.table = new Tabulator("#opdorder", {
			data,
			columns,
			layout: "fitDataStretch",
			movableColumns: true,
			movablerow: true,
			placeholder: __(
				"No active Emergency patients found."
			),

			textDirection:
				frappe.utils.is_rtl()
					? "rtl"
					: "ltr",

			index: "emergency_name",

			initialSort: [
				{
					column: "triage_value",
					dir: "asc",
				},
				{
					column: "encounter_date",
					dir: "desc",
				},
			],

			rowFormatter(row) {
				me.apply_triage_row_style(row);
			},
		});

		this.table.on(
			"rowClick",
			function (event, row) {
				if (
					$(event.target).closest(
						"button, input, select, a, .tabulator-editable"
					).length
				) {
					return;
				}

				me.open_emergency(row.getData());
			}
		);
	}

	async update_triage(cell) {
		const row = cell.getRow();
		const row_data = row.getData();

		const new_triage =
			cell.getValue() || "Not Triaged";

		const old_triage =
			cell.getOldValue() || "Not Triaged";

		if (
			this.normalize_value(new_triage) ===
			this.normalize_value(old_triage)
		) {
			return;
		}

		if (
			!this.triage_options.includes(
				new_triage
			)
		) {
			cell.setValue(old_triage, true);

			frappe.show_alert({
				message: __(
					"Invalid triage level."
				),
				indicator: "red",
			});

			return;
		}

		let emergency_name =
			row_data.emergency_name;

		if (!emergency_name) {
			emergency_name =
				await this.find_emergency_name(
					row_data
				);
		}

		if (!emergency_name) {
			cell.setValue(old_triage, true);

			frappe.msgprint({
				title: __("Emergency"),
				message: __(
					"No Emergency record was found for this patient."
				),
				indicator: "orange",
			});

			return;
		}

		cell.getElement().style.opacity = "0.55";

		try {
			await frappe.db.set_value(
				"Emergency",
				emergency_name,
				this.triage_field,
				new_triage
			);

			row.update({
				emergency_name,
				triage_value: new_triage,
				[this.triage_field]:
					new_triage,
			});

			this.apply_triage_row_style(row);

			frappe.show_alert({
				message: __(
					`Triage updated to ${new_triage}.`
				),
				indicator:
					this.get_triage_indicator(
						new_triage
					),
			});
		} catch (error) {
			console.error(
				"Could not update triage level:",
				error
			);

			cell.setValue(old_triage, true);

			row.update({
				triage_value: old_triage,
				[this.triage_field]:
					old_triage,
			});

			this.apply_triage_row_style(row);

			frappe.msgprint({
				title: __("Triage"),
				message: __(
					"Could not update the triage level. Check the triage fieldname and user permissions."
				),
				indicator: "red",
			});
		} finally {
			cell.getElement().style.opacity = "1";
		}
	}

	async open_emergency(row_data) {
		let emergency_name =
			row_data.emergency_name;

		if (!emergency_name) {
			emergency_name =
				await this.find_emergency_name(
					row_data
				);
		}

		if (!emergency_name) {
			frappe.msgprint({
				title: __("Emergency"),
				message: __(
					"No Emergency record was found for this patient."
				),
				indicator: "orange",
			});

			return;
		}

		frappe.set_route(
			"Form",
			"Emergency",
			emergency_name
		);
	}

	async discharge_patient(row_data) {

	let emergency_name =
		row_data.emergency_name;

	if (!emergency_name) {
		emergency_name =
			await this.find_emergency_name(
				row_data
			);
	}

	if (!emergency_name) {
		frappe.msgprint({
			title: __("Emergency"),
			message: __(
				"No Emergency record was found for this patient."
			),
			indicator: "orange",
		});

		return;
	}

	frappe.new_doc("Discharge Summery", {
		patient: row_data.patient,
		patient_name: row_data.patient_name,
		emergency: emergency_name,
		discharge_date: frappe.datetime.now_date(),
	});

}

	confirm_discharge(row_data) {
		return new Promise((resolve) => {
			const patient_name =
				row_data.patient_name ||
				row_data.patient ||
				__("Patient");

			frappe.confirm(
				__(
					`Do you want to discharge ${patient_name} from Emergency?`
				),
				function () {
					resolve(true);
				},
				function () {
					resolve(false);
				}
			);
		});
	}

	format_triage(value) {
		const label =
			value || "Not Triaged";

		const normalized =
			this.normalize_value(label);

		let css_class =
			"emergency-triage-default";

		if (normalized === "red") {
			css_class =
				"emergency-triage-red";
		} else if (normalized === "yellow") {
			css_class =
				"emergency-triage-yellow";
		} else if (normalized === "green") {
			css_class =
				"emergency-triage-green";
		}

		return `
			<div class="emergency-triage-cell ${css_class}">
				${frappe.utils.escape_html(
					String(label)
				)}
			</div>
		`;
	}

	format_status(value) {
		const label =
			value || "Admitted";

		const normalized =
			this.normalize_value(label);

		let css_class =
			"emergency-status-default";

		if (normalized === "admitted") {
			css_class =
				"emergency-status-admitted";
		} else if (
			normalized === "discharged"
		) {
			css_class =
				"emergency-status-discharged";
		}

		return `
			<span class="emergency-status-badge ${css_class}">
				${frappe.utils.escape_html(
					String(label)
				)}
			</span>
		`;
	}

	apply_triage_row_style(row) {
		const row_data = row.getData();

		const normalized =
			this.normalize_value(
				row_data.triage_value
			);

		const row_element = row.getElement();

		row_element.classList.remove(
			"emergency-critical-row",
			"emergency-yellow-row",
			"emergency-green-row"
		);

		if (normalized === "red") {
			row_element.classList.add(
				"emergency-critical-row"
			);
		} else if (normalized === "yellow") {
			row_element.classList.add(
				"emergency-yellow-row"
			);
		} else if (normalized === "green") {
			row_element.classList.add(
				"emergency-green-row"
			);
		}
	}

	get_triage_indicator(value) {
		const normalized =
			this.normalize_value(value);

		if (normalized === "red") {
			return "red";
		}

		if (normalized === "yellow") {
			return "orange";
		}

		if (normalized === "green") {
			return "green";
		}

		return "blue";
	}

	format_date(value) {
		if (!value) {
			return "";
		}

		try {
			return frappe.datetime.str_to_user(
				value
			);
		} catch (error) {
			return value;
		}
	}

	normalize_value(value) {
		return String(value || "")
			.trim()
			.toLowerCase();
	}

	set_loading(is_loading) {
		if (is_loading) {
			this.page.set_indicator(
				__("Loading"),
				"orange"
			);

			return;
		}

		this.page.clear_indicator();
	}

	destroy_table() {
		if (this.table) {
			try {
				this.table.destroy();
			} catch (error) {
				console.warn(
					"Could not destroy previous table:",
					error
				);
			}

			this.table = null;
		}

		const table_container =
			document.querySelector(
				"#opdorder"
			);

		if (table_container) {
			table_container.innerHTML = "";
		}
	}

	bind_realtime() {
		const me = this;

		this.realtime_handler = function () {
			me.setup_data_table();
		};

		frappe.realtime.on(
			"new_msg",
			this.realtime_handler
		);
	}
}

/*
 * Calculate patient age from DOB.
 *
 * Example:
 * 25 Year(s) 3 Month(s) 10 Day(s)
 */
function calculate_age(birth) {
	if (!birth) {
		return "";
	}

	const birth_date = new Date(birth);
	const today = new Date();

	if (
		Number.isNaN(birth_date.getTime()) ||
		birth_date > today
	) {
		return "";
	}

	let years =
		today.getFullYear() -
		birth_date.getFullYear();

	let months =
		today.getMonth() -
		birth_date.getMonth();

	let days =
		today.getDate() -
		birth_date.getDate();

	if (days < 0) {
		months--;

		const days_in_previous_month =
			new Date(
				today.getFullYear(),
				today.getMonth(),
				0
			).getDate();

		days += days_in_previous_month;
	}

	if (months < 0) {
		years--;
		months += 12;
	}

	if (years < 0) {
		return "";
	}

	return (
		`${years} Year(s) ` +
		`${months} Month(s) ` +
		`${days} Day(s)`
	);
}
