# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff, get_datetime, flt
from datetime import datetime, time, timedelta


# =========================================================
# CUSTOM LEAVE DOCTYPE
# =========================================================

LEAVE_DOCTYPE = "Leaves Assigment"

LEAVE_EMPLOYEE_FIELD = "employee"
LEAVE_FROM_DATE_FIELD = "from_date"
LEAVE_TO_DATE_FIELD = "to_date"
LEAVE_TYPE_FIELD = "leave_type"
LEAVE_REASON_FIELD = "reason"
LEAVE_STATUS_FIELD = "status"

IGNORE_LEAVE_STATUSES = ["Cancelled", "Canceled", "Rejected"]


# =========================================================
# CUSTOM EMPLOYEE SCHEDULLING DOCTYPE
# =========================================================

SCHEDULE_DOCTYPE = "Employee Schedulling"

SCHEDULE_EMPLOYEE_FIELD = "employee"
SCHEDULE_SHIFT_FIELD = "shift"
SCHEDULE_FROM_DATE_FIELD = "from_date"
SCHEDULE_TO_DATE_FIELD = "to_date"
SCHEDULE_LABEL_FIELD = "label"
SCHEDULE_DEPARTMENT_FIELD = "department"


# FREE macnaheedu waa fasax / day off.
# Qofka shift-kiisu FREE yahay Absent ma noqonayo.
OFF_LABELS = [
	"OFF",
	"FREE",
	"FREE DAY",
	"DAY OFF",
	"OFF DAY",
	"REST",
	"REST DAY",
	"WEEKLY OFF",
	"FASAX",
	"FASAX DAY",
]


# =========================================================
# MAIN
# =========================================================

def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	view_type = filters.get("view_type") or "Detail"

	employees = get_employees(filters)

	if not employees:
		return get_columns(view_type), [], None, None, []

	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)
	dates = get_dates(from_date, to_date)

	employee_names = [employee.name for employee in employees]

	schedules = get_employee_schedules(employee_names, from_date, to_date)
	raw_checkins = get_raw_checkins(employee_names, from_date, to_date)
	leaves = get_leaves(employee_names, from_date, to_date)
	holidays = get_holidays(employees, from_date, to_date)
	shift_map = get_shift_map(employees, schedules, raw_checkins)

	checkins = build_checkins(
		employees=employees,
		dates=dates,
		raw_checkins=raw_checkins,
		schedules=schedules,
		shift_map=shift_map
	)

	if view_type == "Summary":
		data = build_summary_data(
			employees=employees,
			dates=dates,
			checkins=checkins,
			leaves=leaves,
			holidays=holidays,
			shift_map=shift_map,
			schedules=schedules,
			filters=filters
		)
	else:
		data = build_detail_data(
			employees=employees,
			dates=dates,
			checkins=checkins,
			leaves=leaves,
			holidays=holidays,
			shift_map=shift_map,
			schedules=schedules,
			filters=filters
		)

	report_summary = get_report_summary(data, view_type)
	data = add_total_row(data, view_type)

	return get_columns(view_type), data, None, None, report_summary


# =========================================================
# VALIDATION
# =========================================================

def validate_filters(filters):
	if not filters.get("from_date"):
		frappe.throw(_("From Date is required"))

	if not filters.get("to_date"):
		frappe.throw(_("To Date is required"))

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def get_dates(from_date, to_date):
	total_days = date_diff(to_date, from_date) + 1
	return [getdate(add_days(from_date, i)) for i in range(total_days)]


# =========================================================
# COLUMNS
# =========================================================

def get_columns(view_type):
	if view_type == "Summary":
		return [
			{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 190},
			{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
			{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 150},
			{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},

			{"label": _("Total Days"), "fieldname": "total_days", "fieldtype": "Int", "width": 100},
			{"label": _("Working Days"), "fieldname": "working_days", "fieldtype": "Int", "width": 115},
			{"label": _("Present"), "fieldname": "present_days", "fieldtype": "Float", "precision": 1, "width": 90},
			{"label": _("Absent"), "fieldname": "absent_days", "fieldtype": "Float", "precision": 1, "width": 90},
			{"label": _("Half Day"), "fieldname": "half_days", "fieldtype": "Float", "precision": 1, "width": 95},
			{"label": _("On Leave"), "fieldname": "leave_days", "fieldtype": "Float", "precision": 1, "width": 95},
			{"label": _("Holiday"), "fieldname": "holiday_days", "fieldtype": "Float", "precision": 1, "width": 95},
			{"label": _("Off Day"), "fieldname": "off_days", "fieldtype": "Float", "precision": 1, "width": 90},
			{"label": _("No Schedule"), "fieldname": "no_schedule_days", "fieldtype": "Float", "precision": 1, "width": 115},

			{"label": _("W Hours"), "fieldname": "total_working_hours", "fieldtype": "Float", "precision": 2, "width": 100},
			{"label": _("Early In"), "fieldname": "total_early_in", "fieldtype": "Data", "width": 110},
			{"label": _("Late In"), "fieldname": "total_late_in", "fieldtype": "Data", "width": 110},
			{"label": _("Early Out"), "fieldname": "total_early_out", "fieldtype": "Data", "width": 110},
			{"label": _("Late Out"), "fieldname": "total_late_out", "fieldtype": "Data", "width": 110},

			{"label": _("Missing Checkout"), "fieldname": "missing_checkout_days", "fieldtype": "Int", "width": 135},
			{"label": _("Attendance %"), "fieldname": "attendance_percentage", "fieldtype": "Percent", "precision": 2, "width": 120},
		]

	return [
		{"label": _("Date"), "fieldname": "attendance_date", "fieldtype": "Date", "width": 110},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 190},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 150},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},

		{"label": _("Status"), "fieldname": "attendance_status", "fieldtype": "Data", "width": 135},
		{"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 130},
		{"label": _("Time In"), "fieldname": "time_in", "fieldtype": "Data", "width": 110},
		{"label": _("Time Out"), "fieldname": "time_out", "fieldtype": "Data", "width": 110},
		{"label": _("W Hours"), "fieldname": "working_hours", "fieldtype": "Float", "precision": 2, "width": 95},

		{"label": _("Early In"), "fieldname": "early_in", "fieldtype": "Data", "width": 110},
		{"label": _("Late In"), "fieldname": "late_in", "fieldtype": "Data", "width": 110},
		{"label": _("Early Out"), "fieldname": "early_out", "fieldtype": "Data", "width": 110},
		{"label": _("Late Out"), "fieldname": "late_out", "fieldtype": "Data", "width": 110},

		{"label": _("Schedule Label"), "fieldname": "schedule_label", "fieldtype": "Data", "width": 130},
		{"label": _("Leave Type"), "fieldname": "leave_type", "fieldtype": "Data", "width": 130},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 260},
	]


# =========================================================
# META HELPERS
# =========================================================

def doctype_exists(doctype):
	return frappe.db.exists("DocType", doctype)


def has_field(doctype, fieldname):
	if not doctype_exists(doctype):
		return False

	return frappe.get_meta(doctype).has_field(fieldname)


# =========================================================
# FORMAT HELPERS
# =========================================================

def format_time(dt):
	if not dt:
		return ""

	return get_datetime(dt).strftime("%H:%M:%S")


def format_duration(seconds):
	seconds = int(seconds or 0)

	if seconds <= 0:
		return ""

	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	secs = seconds % 60

	parts = []

	if hours:
		parts.append(f"{hours}h")

	if minutes:
		parts.append(f"{minutes}m")

	if secs or not parts:
		parts.append(f"{secs}s")

	return " ".join(parts)


def normalize_text(value):
	return str(value or "").strip().upper()


def is_off_value(value):
	return normalize_text(value) in OFF_LABELS


# =========================================================
# EMPLOYEES
# =========================================================

def get_employees(filters):
	fields = ["name", "employee_name", "department", "designation", "status"]

	if has_field("Employee", "branch"):
		fields.append("branch")

	if has_field("Employee", "holiday_list"):
		fields.append("holiday_list")

	if has_field("Employee", "default_shift"):
		fields.append("default_shift")

	conditions = {"status": "Active"}

	if filters.get("employee"):
		conditions["name"] = filters.employee

	if filters.get("department"):
		conditions["department"] = filters.department

	if filters.get("designation"):
		conditions["designation"] = filters.designation

	if filters.get("branch") and has_field("Employee", "branch"):
		conditions["branch"] = filters.branch

	employees = frappe.get_all(
		"Employee",
		fields=fields,
		filters=conditions,
		order_by="employee_name asc"
	)

	for employee in employees:
		employee.setdefault("branch", "")
		employee.setdefault("holiday_list", "")
		employee.setdefault("default_shift", "")

	return employees


# =========================================================
# EMPLOYEE SCHEDULLING
# =========================================================

def get_employee_schedules(employee_names, from_date, to_date):
	schedules = {}

	if not employee_names:
		return schedules

	if not doctype_exists(SCHEDULE_DOCTYPE):
		return schedules

	meta = frappe.get_meta(SCHEDULE_DOCTYPE)

	required_fields = [
		SCHEDULE_EMPLOYEE_FIELD,
		SCHEDULE_SHIFT_FIELD,
		SCHEDULE_FROM_DATE_FIELD,
		SCHEDULE_TO_DATE_FIELD,
	]

	for field in required_fields:
		if not meta.has_field(field):
			return schedules

	fields = [
		"name",
		SCHEDULE_EMPLOYEE_FIELD,
		SCHEDULE_SHIFT_FIELD,
		SCHEDULE_FROM_DATE_FIELD,
		SCHEDULE_TO_DATE_FIELD,
	]

	for field in [SCHEDULE_LABEL_FIELD, SCHEDULE_DEPARTMENT_FIELD]:
		if meta.has_field(field):
			fields.append(field)

	records = frappe.get_all(
		SCHEDULE_DOCTYPE,
		fields=fields,
		filters={
			SCHEDULE_EMPLOYEE_FIELD: ["in", employee_names],
			SCHEDULE_FROM_DATE_FIELD: ["<=", to_date],
			SCHEDULE_TO_DATE_FIELD: [">=", from_date],
		},
		order_by=f"{SCHEDULE_EMPLOYEE_FIELD} asc, {SCHEDULE_FROM_DATE_FIELD} asc"
	)

	for record in records:
		employee = record.get(SCHEDULE_EMPLOYEE_FIELD)
		start = getdate(record.get(SCHEDULE_FROM_DATE_FIELD))
		end = getdate(record.get(SCHEDULE_TO_DATE_FIELD))

		shift = record.get(SCHEDULE_SHIFT_FIELD) or ""
		label = record.get(SCHEDULE_LABEL_FIELD) if meta.has_field(SCHEDULE_LABEL_FIELD) else ""
		department = record.get(SCHEDULE_DEPARTMENT_FIELD) if meta.has_field(SCHEDULE_DEPARTMENT_FIELD) else ""

		current = max(start, from_date)
		last = min(end, to_date)

		while current <= last:
			schedules[(employee, current)] = frappe._dict({
				"name": record.name,
				"employee": employee,
				"shift": shift,
				"label": label or "",
				"department": department or ""
			})
			current = getdate(add_days(current, 1))

	return schedules


def is_off_schedule(schedule_data):
	if not schedule_data:
		return False

	shift = schedule_data.get("shift")
	label = schedule_data.get("label")

	return is_off_value(shift) or is_off_value(label)


def get_effective_shift(employee, schedule_data):
	if schedule_data:
		if is_off_schedule(schedule_data):
			return ""

		if schedule_data.get("shift"):
			return schedule_data.get("shift")

	default_shift = employee.get("default_shift") or ""

	if is_off_value(default_shift):
		return ""

	return default_shift


def get_display_shift(employee, schedule_data):
	if schedule_data:
		if schedule_data.get("shift"):
			return schedule_data.get("shift")

		if schedule_data.get("label"):
			return schedule_data.get("label")

	default_shift = employee.get("default_shift") or ""

	if default_shift:
		return default_shift

	return ""


def get_schedule_label(schedule_data):
	if not schedule_data:
		return ""

	return schedule_data.get("label") or ""


# =========================================================
# RAW CHECKINS
# =========================================================

def get_raw_checkins(employee_names, from_date, to_date):
	if not employee_names:
		return {}

	if not doctype_exists("Employee Checkin"):
		return {}

	start_dt = get_datetime(f"{from_date} 00:00:00")
	extended_to_date = getdate(add_days(to_date, 1))
	end_dt = get_datetime(f"{extended_to_date} 23:59:59")

	fields = ["employee", "time"]

	if has_field("Employee Checkin", "log_type"):
		fields.append("log_type")

	if has_field("Employee Checkin", "shift"):
		fields.append("shift")

	raw_rows = frappe.get_all(
		"Employee Checkin",
		fields=fields,
		filters={
			"employee": ["in", employee_names],
			"time": ["between", [start_dt, end_dt]]
		},
		order_by="employee asc, time asc"
	)

	checkins_by_employee = {}

	for index, row in enumerate(raw_rows):
		employee = row.employee

		if employee not in checkins_by_employee:
			checkins_by_employee[employee] = []

		checkins_by_employee[employee].append(frappe._dict({
			"idx": index,
			"employee": employee,
			"time": get_datetime(row.time),
			"log_type": (row.get("log_type") or "").upper(),
			"shift": row.get("shift") or ""
		}))

	return checkins_by_employee


# =========================================================
# SHIFT HELPERS
# =========================================================

def get_shift_map(employees, schedules, raw_checkins):
	if not doctype_exists("Shift Type"):
		return {}

	shift_names = set()

	for employee in employees:
		default_shift = employee.get("default_shift")

		if default_shift and not is_off_value(default_shift):
			shift_names.add(default_shift)

	for schedule in schedules.values():
		if schedule.get("shift") and not is_off_schedule(schedule):
			shift_names.add(schedule.shift)

	for employee_rows in raw_checkins.values():
		for row in employee_rows:
			if row.get("shift") and not is_off_value(row.shift):
				shift_names.add(row.shift)

	if not shift_names:
		return {}

	fields = ["name"]

	for field in [
		"start_time",
		"end_time",
		"late_entry_grace_period",
		"early_exit_grace_period",
		"working_hours_threshold_for_half_day",
		"working_hours_threshold_for_absent"
	]:
		if has_field("Shift Type", field):
			fields.append(field)

	rows = frappe.get_all(
		"Shift Type",
		fields=fields,
		filters={"name": ["in", list(shift_names)]}
	)

	shift_map = {}

	for row in rows:
		row.setdefault("start_time", None)
		row.setdefault("end_time", None)
		row.setdefault("late_entry_grace_period", 0)
		row.setdefault("early_exit_grace_period", 0)
		row.setdefault("working_hours_threshold_for_half_day", 4)
		row.setdefault("working_hours_threshold_for_absent", 1)
		shift_map[row.name] = row

	return shift_map


def to_time(value):
	if not value:
		return None

	if isinstance(value, time):
		return value

	if isinstance(value, timedelta):
		total_seconds = int(value.total_seconds())
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		seconds = total_seconds % 60
		return time(hours % 24, minutes, seconds)

	if isinstance(value, str):
		parts = value.split(":")
		hour = int(parts[0] or 0)
		minute = int(parts[1] or 0) if len(parts) > 1 else 0
		second = int(parts[2] or 0) if len(parts) > 2 else 0
		return time(hour, minute, second)

	return None


def combine_date_time(attendance_date, time_value):
	t = to_time(time_value)

	if not t:
		return None

	return datetime.combine(attendance_date, t)


def get_calendar_window(attendance_date):
	start_dt = get_datetime(f"{attendance_date} 00:00:00")
	end_dt = get_datetime(f"{attendance_date} 23:59:59")
	return start_dt, end_dt


def get_shift_start_end(attendance_date, shift_name, shift_map):
	if not shift_name or shift_name not in shift_map:
		return None, None

	shift = shift_map[shift_name]
	shift_start = combine_date_time(attendance_date, shift.get("start_time"))
	shift_end = combine_date_time(attendance_date, shift.get("end_time"))

	if not shift_start or not shift_end:
		return None, None

	if shift_end <= shift_start:
		shift_end = shift_end + timedelta(days=1)

	return shift_start, shift_end


def get_shift_window(attendance_date, shift_name, shift_map):
	shift_start, shift_end = get_shift_start_end(attendance_date, shift_name, shift_map)

	if not shift_start or not shift_end:
		return get_calendar_window(attendance_date)

	window_start = shift_start - timedelta(hours=4)
	window_end = shift_end + timedelta(hours=6)

	return window_start, window_end


# =========================================================
# BUILD CHECKINS BY DAY
# =========================================================

def make_checkin_item(selected_rows):
	if not selected_rows:
		return None

	selected_rows = sorted(selected_rows, key=lambda x: x.time)

	first_check_in = None
	last_check_out = None
	all_times = [row.time for row in selected_rows]
	shift = ""

	for row in selected_rows:
		if row.get("shift") and not shift:
			shift = row.shift

		if row.log_type == "IN":
			if not first_check_in or row.time < first_check_in:
				first_check_in = row.time

		elif row.log_type == "OUT":
			if not last_check_out or row.time > last_check_out:
				last_check_out = row.time

	if not first_check_in:
		first_check_in = all_times[0]

	if not last_check_out and len(all_times) > 1:
		last_check_out = all_times[-1]

	if last_check_out == first_check_in:
		last_check_out = None

	return frappe._dict({
		"first_check_in": first_check_in,
		"last_check_out": last_check_out,
		"all_times": all_times,
		"shift": shift
	})


def build_checkins(employees, dates, raw_checkins, schedules, shift_map):
	checkins = {}

	for employee in employees:
		employee_rows = raw_checkins.get(employee.name, [])
		used_checkin_ids = set()

		for attendance_date in dates:
			key = (employee.name, attendance_date)
			schedule_data = schedules.get(key)
			shift_name = get_effective_shift(employee, schedule_data)

			if shift_name:
				window_start, window_end = get_shift_window(attendance_date, shift_name, shift_map)
			else:
				window_start, window_end = get_calendar_window(attendance_date)

			selected_rows = []

			for row in employee_rows:
				if row.idx in used_checkin_ids:
					continue

				if window_start <= row.time <= window_end:
					selected_rows.append(row)

			if not selected_rows:
				continue

			for row in selected_rows:
				used_checkin_ids.add(row.idx)

			checkin_item = make_checkin_item(selected_rows)

			if checkin_item:
				checkins[key] = checkin_item

	return checkins


# =========================================================
# LEAVES ASSIGMENT
# =========================================================

def get_leaves(employee_names, from_date, to_date):
	leaves = {}

	if not employee_names:
		return leaves

	if not doctype_exists(LEAVE_DOCTYPE):
		return leaves

	meta = frappe.get_meta(LEAVE_DOCTYPE)

	required_fields = [
		LEAVE_EMPLOYEE_FIELD,
		LEAVE_FROM_DATE_FIELD,
		LEAVE_TO_DATE_FIELD
	]

	for field in required_fields:
		if not meta.has_field(field):
			return leaves

	fields = [
		"name",
		LEAVE_EMPLOYEE_FIELD,
		LEAVE_FROM_DATE_FIELD,
		LEAVE_TO_DATE_FIELD
	]

	if meta.has_field(LEAVE_TYPE_FIELD):
		fields.append(LEAVE_TYPE_FIELD)

	if meta.has_field(LEAVE_REASON_FIELD):
		fields.append(LEAVE_REASON_FIELD)

	if meta.has_field(LEAVE_STATUS_FIELD):
		fields.append(LEAVE_STATUS_FIELD)

	records = frappe.get_all(
		LEAVE_DOCTYPE,
		fields=fields,
		filters={
			LEAVE_EMPLOYEE_FIELD: ["in", employee_names],
			LEAVE_FROM_DATE_FIELD: ["<=", to_date],
			LEAVE_TO_DATE_FIELD: [">=", from_date],
		}
	)

	for leave in records:
		employee = leave.get(LEAVE_EMPLOYEE_FIELD)
		start = getdate(leave.get(LEAVE_FROM_DATE_FIELD))
		end = getdate(leave.get(LEAVE_TO_DATE_FIELD))

		leave_type = leave.get(LEAVE_TYPE_FIELD) if meta.has_field(LEAVE_TYPE_FIELD) else ""
		reason = leave.get(LEAVE_REASON_FIELD) if meta.has_field(LEAVE_REASON_FIELD) else ""
		status = leave.get(LEAVE_STATUS_FIELD) if meta.has_field(LEAVE_STATUS_FIELD) else ""

		if status and status in IGNORE_LEAVE_STATUSES:
			continue

		current = max(start, from_date)
		last = min(end, to_date)

		while current <= last:
			leaves[(employee, current)] = frappe._dict({
				"leave_type": leave_type or "Leave",
				"reason": reason or "",
				"status": status or ""
			})
			current = getdate(add_days(current, 1))

	return leaves


# =========================================================
# HOLIDAYS
# =========================================================

def get_holidays(employees, from_date, to_date):
	holidays_by_list = {}

	if not doctype_exists("Holiday"):
		return holidays_by_list

	holiday_lists = set()

	for employee in employees:
		if employee.get("holiday_list"):
			holiday_lists.add(employee.holiday_list)

	if not holiday_lists:
		return holidays_by_list

	rows = frappe.get_all(
		"Holiday",
		fields=["parent", "holiday_date", "description"],
		filters={
			"parent": ["in", list(holiday_lists)],
			"holiday_date": ["between", [from_date, to_date]]
		}
	)

	for row in rows:
		holiday_list = row.parent
		holiday_date = getdate(row.holiday_date)

		if holiday_list not in holidays_by_list:
			holidays_by_list[holiday_list] = {}

		holidays_by_list[holiday_list][holiday_date] = row.description or "Holiday"

	return holidays_by_list


def get_holiday_description(employee, attendance_date, holidays):
	holiday_list = employee.get("holiday_list")

	if not holiday_list:
		return ""

	return holidays.get(holiday_list, {}).get(attendance_date, "")


# =========================================================
# TIME CALCULATION
# =========================================================

def calculate_working_hours(first_check_in, last_check_out):
	if not first_check_in or not last_check_out:
		return 0

	seconds = (last_check_out - first_check_in).total_seconds()

	if seconds < 0:
		return 0

	return flt(seconds / 3600, 2)


def calculate_time_balance(attendance_date, first_check_in, last_check_out, shift_name, shift_map):
	early_in_seconds = 0
	late_in_seconds = 0
	early_out_seconds = 0
	late_out_seconds = 0

	shift_start, shift_end = get_shift_start_end(attendance_date, shift_name, shift_map)

	if not shift_start or not shift_end:
		return early_in_seconds, late_in_seconds, early_out_seconds, late_out_seconds

	if first_check_in:
		diff_in = int((first_check_in - shift_start).total_seconds())

		if diff_in > 0:
			late_in_seconds = diff_in
		elif diff_in < 0:
			early_in_seconds = abs(diff_in)

	if last_check_out:
		diff_out = int((last_check_out - shift_end).total_seconds())

		if diff_out > 0:
			late_out_seconds = diff_out
		elif diff_out < 0:
			early_out_seconds = abs(diff_out)

	return early_in_seconds, late_in_seconds, early_out_seconds, late_out_seconds


# =========================================================
# DAILY ATTENDANCE LOGIC
# =========================================================

def get_daily_attendance(employee, attendance_date, checkins, leaves, holidays, shift_map, schedules):
	key = (employee.name, attendance_date)

	schedule_data = schedules.get(key)

	schedule_is_off = is_off_schedule(schedule_data)
	default_shift_is_off = is_off_value(employee.get("default_shift"))

	shift_name = get_effective_shift(employee, schedule_data)
	display_shift = get_display_shift(employee, schedule_data)
	schedule_label = get_schedule_label(schedule_data)

	checkin_data = checkins.get(key)
	leave_data = leaves.get(key)
	holiday_description = get_holiday_description(employee, attendance_date, holidays)

	first_check_in = None
	last_check_out = None
	working_hours = 0

	early_in_seconds = 0
	late_in_seconds = 0
	early_out_seconds = 0
	late_out_seconds = 0

	leave_type = ""
	remarks = ""

	if checkin_data:
		first_check_in = checkin_data.get("first_check_in")
		last_check_out = checkin_data.get("last_check_out")

		if not shift_name and checkin_data.get("shift") and not is_off_value(checkin_data.shift):
			shift_name = checkin_data.shift

		if not display_shift and checkin_data.get("shift"):
			display_shift = checkin_data.shift

		working_hours = calculate_working_hours(first_check_in, last_check_out)

		early_in_seconds, late_in_seconds, early_out_seconds, late_out_seconds = calculate_time_balance(
			attendance_date,
			first_check_in,
			last_check_out,
			shift_name,
			shift_map
		)

		if first_check_in and not last_check_out:
			status = "Missing Checkout"
			remarks = "Check-in exists but checkout is missing"
		else:
			status = "Present"

			if shift_name and shift_name in shift_map:
				half_day_threshold = flt(
					shift_map[shift_name].get("working_hours_threshold_for_half_day") or 0
				)

				if half_day_threshold and working_hours and working_hours < half_day_threshold:
					status = "Half Day"

		if schedule_is_off or default_shift_is_off:
			remarks = "Worked on FREE / Off Day"

	elif leave_data:
		status = "On Leave"
		leave_type = leave_data.get("leave_type") or "Leave"
		reason = leave_data.get("reason") or ""
		remarks = f"{leave_type} - {reason}" if reason else leave_type

	elif holiday_description:
		status = "Holiday"
		remarks = holiday_description

	elif schedule_is_off or default_shift_is_off:
		status = "Off Day"
		remarks = schedule_label or "FREE / Day Off"

	elif not shift_name:
		status = "No Schedule"
		remarks = "No schedule and no default shift"

	else:
		status = "Absent"
		remarks = "No check-in found"

	return frappe._dict({
		"attendance_date": attendance_date,
		"employee": employee.name,
		"employee_name": employee.employee_name,
		"department": employee.get("department"),
		"designation": employee.get("designation"),
		"branch": employee.get("branch"),

		"attendance_status": status,
		"shift": display_shift,
		"time_in": format_time(first_check_in),
		"time_out": format_time(last_check_out),
		"working_hours": working_hours,

		"early_in": format_duration(early_in_seconds),
		"late_in": format_duration(late_in_seconds),
		"early_out": format_duration(early_out_seconds),
		"late_out": format_duration(late_out_seconds),

		"early_in_seconds": early_in_seconds,
		"late_in_seconds": late_in_seconds,
		"early_out_seconds": early_out_seconds,
		"late_out_seconds": late_out_seconds,

		"schedule_label": schedule_label,
		"leave_type": leave_type,
		"remarks": remarks
	})


def status_matches_filter(row, filters):
	if not filters.get("status"):
		return True

	return row.attendance_status == filters.status


# =========================================================
# DATA BUILDERS
# =========================================================

def build_detail_data(employees, dates, checkins, leaves, holidays, shift_map, schedules, filters):
	data = []

	for employee in employees:
		for attendance_date in dates:
			row = get_daily_attendance(
				employee=employee,
				attendance_date=attendance_date,
				checkins=checkins,
				leaves=leaves,
				holidays=holidays,
				shift_map=shift_map,
				schedules=schedules
			)

			if not status_matches_filter(row, filters):
				continue

			data.append(row)

	return data


def build_summary_data(employees, dates, checkins, leaves, holidays, shift_map, schedules, filters):
	data = []

	for employee in employees:
		total_days = len(dates)
		working_days = 0
		present_days = 0
		absent_days = 0
		half_days = 0
		leave_days = 0
		holiday_days = 0
		off_days = 0
		no_schedule_days = 0
		missing_checkout_days = 0
		total_working_hours = 0

		total_early_in_seconds = 0
		total_late_in_seconds = 0
		total_early_out_seconds = 0
		total_late_out_seconds = 0

		filtered_status_found = False

		for attendance_date in dates:
			daily = get_daily_attendance(
				employee=employee,
				attendance_date=attendance_date,
				checkins=checkins,
				leaves=leaves,
				holidays=holidays,
				shift_map=shift_map,
				schedules=schedules
			)

			if filters.get("status") and daily.attendance_status == filters.status:
				filtered_status_found = True

			if daily.attendance_status == "Holiday":
				holiday_days += 1
				continue

			if daily.attendance_status == "Off Day":
				off_days += 1
				continue

			if daily.attendance_status == "No Schedule":
				no_schedule_days += 1
				continue

			working_days += 1

			if daily.attendance_status == "Present":
				present_days += 1

			elif daily.attendance_status == "Half Day":
				half_days += 1

			elif daily.attendance_status == "On Leave":
				leave_days += 1

			elif daily.attendance_status == "Missing Checkout":
				present_days += 1
				missing_checkout_days += 1

			elif daily.attendance_status == "Absent":
				absent_days += 1

			total_working_hours += flt(daily.working_hours or 0)

			total_early_in_seconds += int(daily.early_in_seconds or 0)
			total_late_in_seconds += int(daily.late_in_seconds or 0)
			total_early_out_seconds += int(daily.early_out_seconds or 0)
			total_late_out_seconds += int(daily.late_out_seconds or 0)

		if filters.get("status") and not filtered_status_found:
			continue

		attendance_score = present_days + (half_days * 0.5)

		if working_days:
			attendance_percentage = flt((attendance_score / working_days) * 100, 2)
		else:
			attendance_percentage = 0

		data.append({
			"employee": employee.name,
			"employee_name": employee.employee_name,
			"department": employee.get("department"),
			"designation": employee.get("designation"),
			"branch": employee.get("branch"),

			"total_days": total_days,
			"working_days": working_days,
			"present_days": present_days,
			"absent_days": absent_days,
			"half_days": half_days,
			"leave_days": leave_days,
			"holiday_days": holiday_days,
			"off_days": off_days,
			"no_schedule_days": no_schedule_days,
			"missing_checkout_days": missing_checkout_days,

			"total_working_hours": flt(total_working_hours, 2),

			"total_early_in": format_duration(total_early_in_seconds),
			"total_late_in": format_duration(total_late_in_seconds),
			"total_early_out": format_duration(total_early_out_seconds),
			"total_late_out": format_duration(total_late_out_seconds),

			"total_early_in_seconds": total_early_in_seconds,
			"total_late_in_seconds": total_late_in_seconds,
			"total_early_out_seconds": total_early_out_seconds,
			"total_late_out_seconds": total_late_out_seconds,

			"attendance_percentage": attendance_percentage
		})

	return data


# =========================================================
# TOTAL ROW
# =========================================================

def add_total_row(data, view_type):
	if not data:
		return data

	total_row = frappe._dict({
		"is_total_row": 1,
		"employee": "",
		"employee_name": "TOTAL",
		"department": "",
		"designation": "",
		"branch": "",
		"attendance_status": "",
		"shift": "",
		"remarks": "Grand Total"
	})

	if view_type == "Summary":
		total_early_in_seconds = sum(int(row.get("total_early_in_seconds") or 0) for row in data)
		total_late_in_seconds = sum(int(row.get("total_late_in_seconds") or 0) for row in data)
		total_early_out_seconds = sum(int(row.get("total_early_out_seconds") or 0) for row in data)
		total_late_out_seconds = sum(int(row.get("total_late_out_seconds") or 0) for row in data)

		total_row.update({
			"total_days": "",
			"working_days": "",
			"present_days": "",
			"absent_days": "",
			"half_days": "",
			"leave_days": "",
			"holiday_days": "",
			"off_days": "",
			"no_schedule_days": "",
			"missing_checkout_days": "",
			"total_working_hours": flt(sum(flt(row.get("total_working_hours") or 0) for row in data), 2),

			"total_early_in": format_duration(total_early_in_seconds),
			"total_late_in": format_duration(total_late_in_seconds),
			"total_early_out": format_duration(total_early_out_seconds),
			"total_late_out": format_duration(total_late_out_seconds),

			"attendance_percentage": "",
		})

		return data + [total_row]

	total_early_in_seconds = sum(int(row.get("early_in_seconds") or 0) for row in data)
	total_late_in_seconds = sum(int(row.get("late_in_seconds") or 0) for row in data)
	total_early_out_seconds = sum(int(row.get("early_out_seconds") or 0) for row in data)
	total_late_out_seconds = sum(int(row.get("late_out_seconds") or 0) for row in data)

	total_row.update({
		"attendance_date": "",
		"time_in": "",
		"time_out": "",
		"working_hours": flt(sum(flt(row.get("working_hours") or 0) for row in data), 2),

		"early_in": format_duration(total_early_in_seconds),
		"late_in": format_duration(total_late_in_seconds),
		"early_out": format_duration(total_early_out_seconds),
		"late_out": format_duration(total_late_out_seconds),

		"schedule_label": "",
		"leave_type": "",
	})

	return data + [total_row]


# =========================================================
# REPORT SUMMARY CARDS
# =========================================================

def get_report_summary(data, view_type):
	if not data:
		return []

	if view_type == "Summary":
		total_present = sum(flt(row.get("present_days") or 0) for row in data)
		total_absent = sum(flt(row.get("absent_days") or 0) for row in data)
		total_leave = sum(flt(row.get("leave_days") or 0) for row in data)
		total_off = sum(flt(row.get("off_days") or 0) for row in data)

		total_late_in_seconds = sum(int(row.get("total_late_in_seconds") or 0) for row in data)
		total_early_in_seconds = sum(int(row.get("total_early_in_seconds") or 0) for row in data)

	else:
		total_present = len([row for row in data if row.get("attendance_status") == "Present"])
		total_absent = len([row for row in data if row.get("attendance_status") == "Absent"])
		total_leave = len([row for row in data if row.get("attendance_status") == "On Leave"])
		total_off = len([row for row in data if row.get("attendance_status") == "Off Day"])

		total_late_in_seconds = sum(int(row.get("late_in_seconds") or 0) for row in data)
		total_early_in_seconds = sum(int(row.get("early_in_seconds") or 0) for row in data)

	return [
		{"value": total_present, "indicator": "Green", "label": _("Present Rows"), "datatype": "Float"},
		{"value": total_absent, "indicator": "Red", "label": _("Absent Rows"), "datatype": "Float"},
		{"value": total_leave, "indicator": "Blue", "label": _("Leave Rows"), "datatype": "Float"},
		{"value": total_off, "indicator": "Grey", "label": _("Off / FREE Days"), "datatype": "Float"},
		{"value": format_duration(total_early_in_seconds) or "0", "indicator": "Blue", "label": _("Early In"), "datatype": "Data"},
		{"value": format_duration(total_late_in_seconds) or "0", "indicator": "Orange", "label": _("Late In"), "datatype": "Data"},
	]