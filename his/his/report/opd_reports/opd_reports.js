// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OPD Reports"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
			on_change: function(report) {
				reload_report_ui(report);
			}
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
			on_change: function(report) {
				reload_report_ui(report);
			}
		},
		{
			fieldname: "practitioner",
			label: __("Practitioner"),
			fieldtype: "Link",
			options: "Healthcare Practitioner",
			on_change: function(report) {
				reload_report_ui(report);
			}
		},
		{
			fieldname: "refresh_data",
			label: __("Refresh Data"),
			fieldtype: "Button",
		}
	],

	onload: function(report) {
		cleanup_report_dom(report);

		const btn = report.get_filter("refresh_data");
		if (btn && btn.$input) {
			btn.$input.off("click").on("click", function() {
				cleanup_report_dom(report);
				reload_report_ui(report);
				report.refresh();
			});
		}

		enhance_admin_summary_cards(report);
		render_all_extra_charts(report);
	},

	refresh: function(report) {
		cleanup_report_dom(report);
		enhance_admin_summary_cards(report);
		render_all_extra_charts(report);
	},

	after_datatable_render: function(report) {
		if (!is_correct_report(report, "OPD Report")) return;
		enhance_admin_summary_cards(report);
		render_all_extra_charts(report);
	}
};

function get_safe_wrapper(report) {
	if (report && report.page && report.page.wrapper && report.page.wrapper[0]) {
		return report.page.wrapper[0];
	}
	return null;
}

function is_correct_report(report, report_name) {
	return report && report.report_name === report_name;
}

function cleanup_report_dom(report) {
	const wrapper = get_safe_wrapper(report);
	if (!wrapper) return;

	wrapper.querySelector("#opd-extra-pie-section")?.remove();
	wrapper.querySelector("#ipd-extra-chart-section")?.remove();
}

function reload_report_ui(report) {
	if (!report) return;

	cleanup_report_dom(report);
	report.refresh();

	setTimeout(() => {
		if (!is_correct_report(report, "OPD Report")) return;
		enhance_admin_summary_cards(report);
		render_all_extra_charts(report);
	}, 500);
}

function enhance_admin_summary_cards(report) {
	if (!is_correct_report(report, "OPD Report")) return;

	add_admin_summary_css();

	const try_apply = () => {
		if (!is_correct_report(report, "OPD Report")) return;

		const wrapper = get_safe_wrapper(report);
		if (!wrapper) return;

		const containers = wrapper.querySelectorAll(`
			.report-summary,
			.summary-wrapper
		`);

		containers.forEach(container => {
			container.style.display = "flex";
			container.style.flexWrap = "wrap";
			container.style.gap = "16px";
			container.style.background = "transparent";
			container.style.padding = "12px 0";
			container.style.border = "none";
			container.style.boxShadow = "none";
		});

		const cards = wrapper.querySelectorAll(`
			.report-summary .summary-item,
			.report-summary .report-summary-item,
			.report-summary .card,
			.report-summary > div,
			.summary-wrapper .summary-item,
			.summary-wrapper .report-summary-item,
			.summary-wrapper .card,
			.summary-wrapper > div,
			.query-report .summary-item,
			.query-report .report-summary-item
		`);

		cards.forEach((card, index) => {
			const labelEl = card.querySelector(".summary-label, .label");
			const valueEl = card.querySelector(".summary-value, .value");

			if (!labelEl || !valueEl) return;

			const rawLabel = (labelEl.textContent || "").trim();
			const config = getCardConfig(rawLabel, index);

			card.style.background = config.background;
			card.style.border = "1px solid #dbe4ee";
			card.style.borderTop = `4px solid ${config.color}`;
			card.style.borderRadius = "16px";
			card.style.boxShadow = "0 6px 18px rgba(0,0,0,0.08)";
			card.style.padding = "18px 22px";
			card.style.minWidth = "180px";
			card.style.minHeight = "130px";
			card.style.flex = "1 1 180px";
			card.style.margin = "0";
			card.style.position = "relative";
			card.style.overflow = "hidden";
			card.style.cursor = "pointer";
			card.style.transition = "all 0.25s ease";

			labelEl.style.fontSize = "14px";
			labelEl.style.fontWeight = "600";
			labelEl.style.color = "#64748b";
			labelEl.style.marginBottom = "10px";
			labelEl.style.display = "flex";
			labelEl.style.alignItems = "center";
			labelEl.style.gap = "8px";

			valueEl.style.fontSize = "30px";
			valueEl.style.fontWeight = "700";
			valueEl.style.color = config.color;

			addIconToLabel(labelEl, config.icon);
			animateValue(valueEl);

			card.onmouseenter = () => {
				card.style.transform = "translateY(-4px)";
				card.style.boxShadow = "0 12px 24px rgba(0,0,0,0.12)";
			};

			card.onmouseleave = () => {
				if (!card.classList.contains("summary-card-active")) {
					card.style.transform = "translateY(0)";
					card.style.boxShadow = "0 6px 18px rgba(0,0,0,0.08)";
				}
			};

			card.onclick = () => {
				wrapper.querySelectorAll(".summary-card-active").forEach(el => {
					el.classList.remove("summary-card-active");
					el.style.transform = "translateY(0)";
					el.style.boxShadow = "0 6px 18px rgba(0,0,0,0.08)";
				});

				card.classList.add("summary-card-active");
				card.style.transform = "translateY(-4px)";
				card.style.boxShadow = `0 14px 30px ${hexToRgba(config.color, 0.25)}`;
			};
		});
	};

	setTimeout(try_apply, 300);
	setTimeout(try_apply, 800);
	setTimeout(try_apply, 1400);
}

function render_all_extra_charts(report) {
	if (!is_correct_report(report, "OPD Report")) return;

	if (report._opd_extra_timer_1) clearTimeout(report._opd_extra_timer_1);
	if (report._opd_extra_timer_2) clearTimeout(report._opd_extra_timer_2);

	report._opd_extra_timer_1 = setTimeout(() => {
		if (!is_correct_report(report, "OPD Report")) return;
		create_or_update_extra_charts(report);
	}, 500);

	report._opd_extra_timer_2 = setTimeout(() => {
		if (!is_correct_report(report, "OPD Report")) return;
		create_or_update_extra_charts(report);
	}, 1000);
}

function create_or_update_extra_charts(report) {
	if (!is_correct_report(report, "OPD Report")) return;

	const wrapper = get_safe_wrapper(report);
	if (!wrapper) return;

	const data = get_report_rows(report);

	if (!data || !data.length) {
		wrapper.querySelector("#opd-extra-pie-section")?.remove();
		return;
	}

	let section = wrapper.querySelector("#opd-extra-pie-section");

	if (!section) {
		section = document.createElement("div");
		section.id = "opd-extra-pie-section";
		section.innerHTML = `
			<div class="opd-extra-chart-card opd-extra-chart-card-full">
				<div class="opd-extra-chart-title">New / Follow Up / Refer by Doctor</div>
				<div id="opd-pie-by-doctor-grid" class="opd-pie-by-doctor-grid"></div>
			</div>

			<div class="opd-extra-chart-card opd-extra-chart-card-full">
				<div class="opd-extra-chart-title"></div>
				<div id="opd-gender-funnel-wrap" class="opd-gender-funnel-wrap">
					<div id="opd-gender-funnel"></div>
					<div id="opd-gender-funnel-note" class="opd-gender-funnel-note"></div>
				</div>
			</div>
		`;

		const chartHost =
			wrapper.querySelector(".chart-wrapper")?.closest(".section-body") ||
			wrapper.querySelector(".chart-wrapper")?.parentElement ||
			wrapper.querySelector(".frappe-chart")?.closest(".section-body") ||
			wrapper.querySelector(".frappe-chart")?.parentElement ||
			wrapper.querySelector(".report-chart")?.closest(".section-body") ||
			wrapper.querySelector(".report-chart")?.parentElement;

		if (chartHost) {
			chartHost.insertAdjacentElement("afterend", section);
		} else {
			wrapper.appendChild(section);
		}
	}

	render_pie_types_by_doctor(data);
	// render_gender_funnel(report);
}

function get_report_rows(report) {
	let rows = [];

	if (Array.isArray(report?.raw_data)) {
		rows = report.raw_data;
	} else if (Array.isArray(report?.data)) {
		rows = report.data;
	} else {
		rows = [];
	}

	return rows
		.filter(row => row && typeof row === "object" && !Array.isArray(row))
		.map(row => ({
			practitioner: (row.practitioner || "").toString().trim(),
			new_patient: cint(row.new_patient),
			follow_up: cint(row.follow_up),
			refer: cint(row.refer),
			total_cases: cint(row.total_cases)
		}))
		.filter(row =>
			row.practitioner &&
			row.practitioner.toLowerCase() !== "total" &&
			row.total_cases > 0
		);
}

function render_pie_types_by_doctor(data) {
	const container = document.getElementById("opd-pie-by-doctor-grid");
	if (!container) return;

	container.innerHTML = "";

	const doctorRows = data
		.filter(row =>
			row &&
			row.practitioner &&
			String(row.practitioner).trim() &&
			String(row.practitioner).trim().toLowerCase() !== "total" &&
			cint(row.total_cases) > 0
		)
		.sort((a, b) => cint(b.total_cases) - cint(a.total_cases))
		.slice(0, 16);

	doctorRows.forEach((row, index) => {
		const name = String(row.practitioner).trim();
		const chartId = `opd-doctor-type-pie-${index}`;

		const card = document.createElement("div");
		card.className = "opd-doctor-pie-card";
		card.innerHTML = `
			<div class="opd-doctor-pie-title">${frappe.utils.escape_html(name)}</div>
			<div class="opd-doctor-pie-chart-wrap">
				<div id="${chartId}" class="opd-doctor-chart-holder"></div>
			</div>
		`;

		container.appendChild(card);

		const chartEl = document.getElementById(chartId);
		if (!chartEl) return;

		chartEl.innerHTML = "";

		new frappe.Chart(chartEl, {
			data: {
				labels: ["New", "Follow Up", "Refer"],
				datasets: [
					{
						values: [
							cint(row.new_patient),
							cint(row.follow_up),
							cint(row.refer)
						]
					}
				]
			},
			type: "donut",
			height: 220,
			colors: ["#3b82f6", "#ec4899", "#22c55e"]
		});
	});
}

function render_gender_funnel(report) {
	const container = document.getElementById("opd-gender-funnel");
	const note = document.getElementById("opd-gender-funnel-note");
	if (!container || !note) return;

	container.innerHTML = "";
	note.innerHTML = "";

	const gender = (report && report.message && report.message.gender_data) || {};
	const male = cint(gender.male);
	const female = cint(gender.female);
	const total = male + female;

	if (!total) {
		note.textContent = "No gender data found";
		return;
	}

	const malePct = ((male / total) * 100).toFixed(1);
	const femalePct = ((female / total) * 100).toFixed(1);

	try {
		new frappe.Chart(container, {
			data: {
				labels: ["Male", "Female"],
				datasets: [
					{
						values: [male, female]
					}
				]
			},
			type: "funnel",
			height: 260,
			colors: ["#3b82f6", "#ec4899"]
		});
	} catch (e) {
		new frappe.Chart(container, {
			data: {
				labels: ["Male", "Female"],
				datasets: [
					{
						values: [male, female]
					}
				]
			},
			type: "donut",
			height: 260,
			colors: ["#3b82f6", "#ec4899"]
		});
	}

	note.innerHTML = `
		<div class="opd-gender-stat"><span>Male</span><strong>${male} (${malePct}%)</strong></div>
		<div class="opd-gender-stat"><span>Female</span><strong>${female} (${femalePct}%)</strong></div>
	`;
}

function getCardConfig(label, index) {
	const text = (label || "").toLowerCase();

	if (text.includes("new")) {
		return {
			icon: "🆕",
			color: "#2563eb",
			background: "linear-gradient(180deg, #ffffff 0%, #eff6ff 100%)"
		};
	}

	if (text.includes("follow")) {
		return {
			icon: "🔁",
			color: "#d97706",
			background: "linear-gradient(180deg, #ffffff 0%, #fff7ed 100%)"
		};
	}

	if (text.includes("refer")) {
		return {
			icon: "📤",
			color: "#7c3aed",
			background: "linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%)"
		};
	}

	if (text.includes("open")) {
		return {
			icon: "🟠",
			color: "#dc2626",
			background: "linear-gradient(180deg, #ffffff 0%, #fef2f2 100%)"
		};
	}

	if (text.includes("closed")) {
		return {
			icon: "✅",
			color: "#16a34a",
			background: "linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%)"
		};
	}

	if (text.includes("total")) {
		return {
			icon: "📊",
			color: "#0f766e",
			background: "linear-gradient(180deg, #ffffff 0%, #f0fdfa 100%)"
		};
	}

	const fallback = [
		{ icon: "📈", color: "#2563eb", background: "linear-gradient(180deg, #ffffff 0%, #eff6ff 100%)" },
		{ icon: "📋", color: "#d97706", background: "linear-gradient(180deg, #ffffff 0%, #fff7ed 100%)" },
		{ icon: "📌", color: "#7c3aed", background: "linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%)" }
	];

	return fallback[index % fallback.length];
}

function addIconToLabel(labelEl, icon) {
	if (!labelEl || labelEl.querySelector(".summary-card-icon")) return;

	const iconSpan = document.createElement("span");
	iconSpan.className = "summary-card-icon";
	iconSpan.textContent = icon;
	iconSpan.style.fontSize = "16px";
	iconSpan.style.display = "inline-flex";
	iconSpan.style.alignItems = "center";
	iconSpan.style.justifyContent = "center";

	labelEl.prepend(iconSpan);
}

function animateValue(valueEl) {
	if (!valueEl || valueEl.dataset.animated === "1") return;

	const rawText = (valueEl.textContent || "").replace(/,/g, "").trim();
	const finalValue = parseInt(rawText, 10);

	if (isNaN(finalValue)) return;

	valueEl.dataset.animated = "1";
	let current = 0;
	const duration = 700;
	const stepTime = 20;
	const increment = Math.max(1, Math.ceil(finalValue / (duration / stepTime)));

	const timer = setInterval(() => {
		current += increment;

		if (current >= finalValue) {
			current = finalValue;
			clearInterval(timer);
		}

		valueEl.textContent = current.toLocaleString();
	}, stepTime);
}

function hexToRgba(hex, alpha) {
	const sanitized = hex.replace("#", "");
	const bigint = parseInt(sanitized, 16);
	const r = (bigint >> 16) & 255;
	const g = (bigint >> 8) & 255;
	const b = bigint & 255;
	return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function cint(value) {
	return parseInt(value || 0, 10) || 0;
}

function add_admin_summary_css() {
	if (document.getElementById("admin-summary-cards-css")) return;

	const style = document.createElement("style");
	style.id = "admin-summary-cards-css";
	style.innerHTML = `
		.report-summary,
		.summary-wrapper {
			background: transparent !important;
			border: none !important;
			box-shadow: none !important;
		}

		.report-summary .summary-item,
		.report-summary .report-summary-item,
		.report-summary .card,
		.report-summary > div,
		.summary-wrapper .summary-item,
		.summary-wrapper .report-summary-item,
		.summary-wrapper .card,
		.summary-wrapper > div,
		.query-report .summary-item,
		.query-report .report-summary-item {
			border-radius: 16px !important;
			min-height: 130px !important;
			padding: 18px 22px !important;
			transition: all 0.25s ease !important;
		}

		.report-summary .summary-label,
		.report-summary .label,
		.summary-wrapper .summary-label,
		.summary-wrapper .label {
			font-size: 14px !important;
			font-weight: 600 !important;
			line-height: 1.4 !important;
		}

		.report-summary .summary-value,
		.report-summary .value,
		.summary-wrapper .summary-value,
		.summary-wrapper .value {
			font-size: 30px !important;
			font-weight: 700 !important;
			line-height: 1.1 !important;
		}

		.summary-card-active {
			outline: 2px solid rgba(37, 99, 235, 0.12);
		}

		#opd-extra-pie-section {
			margin-top: 18px;
		}

		.opd-extra-chart-card {
			background: #ffffff;
			border: 1px solid #dbe4ee;
			border-radius: 16px;
			box-shadow: 0 6px 18px rgba(0,0,0,0.08);
			padding: 18px;
		}

		.opd-extra-chart-card-full {
			margin-top: 6px;
		}

		.opd-extra-chart-title {
			font-size: 16px;
			font-weight: 700;
			color: #1f2937;
			margin-bottom: 12px;
		}

		.opd-pie-by-doctor-grid {
			display: grid;
			grid-template-columns: repeat(4, 1fr);
			gap: 16px;
			margin-bottom: 18px;
		}

		.opd-doctor-pie-card {
			background: #f8fafc;
			border: 1px solid #e5e7eb;
			border-radius: 14px;
			padding: 14px;
		}

		.opd-doctor-pie-title {
			font-size: 14px;
			font-weight: 600;
			color: #374151;
			margin-bottom: 10px;
			text-align: center;
		}

		.opd-doctor-pie-chart-wrap {
			display: flex;
			justify-content: center;
			align-items: center;
			width: 100%;
			min-height: 220px;
			overflow: hidden;
		}

		.opd-doctor-chart-holder {
			width: 100%;
			display: flex;
			justify-content: center;
			align-items: center;
		}

		.opd-doctor-chart-holder .frappe-chart,
		.opd-doctor-chart-holder svg {
			margin: 0 auto !important;
			display: block !important;
		}

		.opd-gender-funnel-wrap {
			padding: 8px 0 4px 0;
		}

		.opd-gender-funnel-note {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
			gap: 12px;
			margin-top: 10px;
		}

		.opd-gender-stat {
			background: #f8fafc;
			border: 1px solid #e5e7eb;
			border-radius: 12px;
			padding: 12px 14px;
			display: flex;
			justify-content: space-between;
			align-items: center;
			font-size: 14px;
		}

		.opd-gender-stat span {
			color: #64748b;
			font-weight: 600;
		}

		.opd-gender-stat strong {
			color: #111827;
			font-weight: 700;
		}

		@media (max-width: 1200px) {
			.opd-pie-by-doctor-grid {
				grid-template-columns: repeat(3, 1fr);
			}
		}

		@media (max-width: 900px) {
			.opd-pie-by-doctor-grid {
				grid-template-columns: repeat(2, 1fr);
			}
		}

		@media (max-width: 600px) {
			.opd-pie-by-doctor-grid {
				grid-template-columns: 1fr;
			}
		}
	`;
	document.head.appendChild(style);
}