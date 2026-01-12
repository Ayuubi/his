# Copyright (c) 2022, Anfac and contributors
# For license information, please see license.txt


import frappe
from frappe import _
import requests
import datetime
import json
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate
from his.api.send_sms import send_sms
from his.his.doctype.radiology.radiology import update_check_tests_stat

class LabResult(Document):
    def on_submit(self):
        doc=self
        status = ''
        mobile= frappe.db.get_value("Patient",doc.patient, "mobile_no")
        messge= doc.patient_name+" , Jawaabta sheybaarka waa soo baxday fadlan aad qaybta shaybaarka"
        labs = frappe.db.get_list("Lab Result", filters={"patient": doc.patient, "date": doc.date}, fields=['docstatus'])
        all_docstatus_one = all(lab.docstatus == 1 for lab in labs)
        if all_docstatus_one:
            try:
                send_sms(mobile, messge)
            except Exception as e:
                a="l"

        # update_check_tests_stat(self)
        itms= []
        for i in self.normal_test_items:
            itms.append({
                "test_name" : i.lab_test_name,
                "result" : i.result_value
            })
            name=frappe.db.get_value("Lab Test preparion", {"test":i.lab_test_name }, "name")
            frappe.db.set_value("Lab Test preparion", name, "result" , i.result_value)  
            frappe.db.set_value("Lab Test preparion", name, "status" , 1)  
            
    def get_lab_tests_hor(self):
            test ={}
            for item in self.normal_test_items:
                
                # frappe.errprint(test)
                is_template = 0
                template = {}
                if item.test:
                    is_template = frappe.db.exists("Lab Test Template", item.test)
                    if is_template:
                        template = frappe.get_doc('Lab Test Template', item.test)
                # else:
                # 	is_template = frappe.db.exists("Lab Test Template", item.lab_test_name)
                # 	if is_template:
                # 		template = frappe.get_doc('Lab Test Template', item.lab_test_name)
                if template:
                    if template.department:
                        # template = frappe.get_doc('Lab Test Template', item.test)
                        
                        
                        if not f'{template.department}' in test:
                            test[f'{template.department}'] = [{'test':item.test , 'lab_event' : '', 'lab_test_name' : item.lab_test_name , 'result_value' : item.result_value , 'normal_range' :item.normal_range}]

                            if template.lab_test_template_type == "Compound":
                                # frappe.msgprint(template.name)
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    
                                    test[f'{template.department}'].append({ "lab_event":'', 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                            
                            
                            if template.lab_test_template_type == "Grouped":
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    test[f'{template.department}'].append({'test':'' ,"lab_event":'', 'lab_test_name' : event.lab_test_name , 'result_value' : event.result_value , 'normal_range' :event.normal_range})
                    
                                    lab_events = frappe.db.get_list('Normal Test Result',
                                        filters={
                                            'template': event.lab_test_name,
                                            'parent' : self.name
                                        },
                                        
                                        fields=['lab_test_event', 'result_value' , 'normal_range'],
                                    
                                    )
                                    for eve in lab_events:

                                        test[f'{template.department}'].append({ 'lab_test_name' : '', 'lab_event' : eve.lab_test_event  ,  'normal_range' :eve.normal_range , 'result_value' : eve.result_value})

                        
                        else:
                            test[f'{template.department}'].append({'test':item.test ,"lab_event":'', 'lab_test_name' : '' , 'result_value' : item.result_value , 'normal_range' :item.normal_range})

                            if template.lab_test_template_type == "Compound":
                                # frappe.msgprint(template.name)
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    
                                    test[f'{template.department}'].append({ "lab_event":'', 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                            
                            
            # frappe.errprint(test)					
            return test


    def get_lab_tests(self):
        test ={}
        for item in self.normal_test_items:
            
            # frappe.errprint(test)
            is_template = 0
            template = {}
            if item.test:
                is_template = frappe.db.exists("Lab Test Template", item.test)
                if is_template:
                    template = frappe.get_doc('Lab Test Template', item.test)
            # else:
            # 	is_template = frappe.db.exists("Lab Test Template", item.lab_test_name)
            # 	if is_template:
            # 		template = frappe.get_doc('Lab Test Template', item.lab_test_name)
            if template:
                if template.department:
                    # template = frappe.get_doc('Lab Test Template', item.test)
                    # frappe.msgprint(template.name)
                    if not f'{template.department}' in test:
                        test[f'{template.department}'] = [{'test':item.test , 'lab_event' : '', 'lab_test_name' : item.lab_test_name , 'result_value' : item.result_value , 'normal_range' :item.normal_range}]

                        if template.lab_test_template_type == "Compound":
                            events = frappe.db.get_list('Normal Test Result',
                                filters={
                                    'template': template.name,
                                    'parent' : self.name
                                },
                                fields=['lab_test_name', 'result_value' , 'normal_range'],
                            
                            )
                            # frappe.errprint(events)	
                            # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                            for event in events:
                                test[f'{template.department}'].append({ "lab_event":'', 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                        if template.lab_test_template_type == "Grouped":
                            events = frappe.db.get_list('Normal Test Result',
                                filters={
                                    'template': template.name,
                                    'parent' : self.name
                                },
                                fields=['lab_test_name', 'result_value' , 'normal_range'],
                            
                            )
                            
                            # frappe.errprint(events)	
                            # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                            for event in events:
                                test[f'{template.department}'].append({'test':'' ,"lab_event":'', 'lab_test_name' : event.lab_test_name , 'result_value' : event.result_value , 'normal_range' :event.normal_range})
                
                                lab_events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': event.lab_test_name,
                                        'parent' : self.name
                                    },
                                    
                                    fields=['lab_test_event', 'result_value' , 'normal_range'],
                                
                                )
                                for eve in lab_events:

                                    test[f'{template.department}'].append({ 'lab_test_name' : '', 'lab_event' : eve.lab_test_event  ,  'normal_range' :eve.normal_range , 'result_value' : eve.result_value})

                    
                    else:
                        test[f'{template.department}'].append({'test':item.lab_test_name ,"lab_event":'', 'lab_test_name' : '' , 'result_value' : item.result_value , 'normal_range' :item.normal_range})
                
        # frappe.errprint(test)					
        return test


    # def get_lab_tests_for_all(self):
        test = {}
        processed = set()  # prevent grouped duplication

        for item in (self.normal_test_items or []):
            template = {}

            # Get template doc from item.test, otherwise from item.lab_test_name
            template_name = (item.test or "").strip()
            if not template_name:
                template_name = (item.lab_test_name or "").strip()

            if template_name and frappe.db.exists("Lab Test Template", template_name):
                template = frappe.get_doc("Lab Test Template", template_name)
            else:
                continue

            if not template.department:
                continue

            key = f"{template.department}"

            # -----------------------------
            # FIRST TIME for this department
            # -----------------------------
            if key not in test:
                # Header row (template name row) -> NO UNIT / NO RANGE
                test[key] = [{
                    "test": item.test,
                    "lab_event": "",
                    "lab_test_name": item.lab_test_name,
                    "result_value": "",
                    "lab_test_uom": "",
                    "normal_range": ""
                }]

                # ✅ FIX: add the actual first test row for Single-type tests
                if template.lab_test_template_type not in ("Compound", "Grouped") and item.result_value:
                    test[key].append({
                        "test": item.lab_test_name,
                        "lab_event": "",
                        "lab_test_name": "",
                        "result_value": item.result_value,
                        "lab_test_uom": (getattr(item, "lab_test_uom", "") or ""),
                        "normal_range": (item.normal_range or "")
                    })

                # -------- Compound ----------
                if template.lab_test_template_type == "Compound":
                    events = frappe.db.get_list(
                        "Normal Test Result",
                        filters={"template": template.name, "parent": self.name},
                        fields=["lab_test_name", "result_value", "normal_range", "lab_test_uom"],
                        order_by="idx asc",
                        ignore_permissions=True
                    )

                    for event in events:
                        test[key].append({
                            "lab_event": "",
                            "lab_test_name": event.lab_test_name,
                            "result_value": event.result_value,
                            "lab_test_uom": (event.lab_test_uom or ""),
                            "normal_range": (event.normal_range or "")
                        })

                # -------- Grouped ----------
                if template.lab_test_template_type == "Grouped":
                    events = frappe.db.get_list(
                        "Normal Test Result",
                        filters={"template": template.name, "parent": self.name},
                        fields=["lab_test_name", "result_value", "normal_range", "lab_test_uom"],
                        order_by="idx asc",
                        ignore_permissions=True
                    )

                    for event in events:
                        test[key].append({
                            "test": "",
                            "lab_event": "",
                            "lab_test_name": event.lab_test_name,
                            "result_value": event.result_value,
                            "lab_test_uom": (event.lab_test_uom or ""),
                            "normal_range": (event.normal_range or "")
                        })

                        lab_events = frappe.db.get_list(
                            "Normal Test Result",
                            filters={"template": event.lab_test_name, "parent": self.name},
                            fields=["lab_test_event", "result_value", "normal_range", "lab_test_uom"],
                            order_by="idx asc",
                            ignore_permissions=True
                        )

                        for eve in lab_events:
                            test[key].append({
                                "lab_test_name": "",
                                "lab_event": eve.lab_test_event,
                                "result_value": eve.result_value,
                                "lab_test_uom": (eve.lab_test_uom or ""),
                                "normal_range": (eve.normal_range or "")
                            })

                processed.add(item.test)  # keep as-is

            # -----------------------------
            # department already exists
            # -----------------------------
            else:
                if template.lab_test_template_type == "Grouped" and item.test in processed:
                    continue

                test[key].append({
                    "test": item.lab_test_name,
                    "lab_event": "",
                    "lab_test_name": "",
                    "result_value": item.result_value,
                    "lab_test_uom": (getattr(item, "lab_test_uom", "") or ""),
                    "normal_range": (item.normal_range or "")
                })

        return test

    def get_lab_tests_for_all(self):
        import frappe

        out = {}
        processed_grouped = set()   # header once per grouped parent template (Electrolytes)
        processed_compound = set()  # build compound section once per compound template

        def add_row(dept, rowdict):
            out.setdefault(dept, []).append(rowdict)

        def get_template(name: str):
            name = (name or "").strip()
            if not name:
                return None
            if not frappe.db.exists("Lab Test Template", name):
                return None
            return frappe.get_cached_doc("Lab Test Template", name)

        # Helper: resolve a template for this row
        # Priority: item.test (Grouped parent like Electrolytes) -> item.template -> item.lab_test_name
        def resolve_template_for_row(r):
            for cand in [(r.test or "").strip(),
                        (getattr(r, "template", "") or "").strip(),
                        (r.lab_test_name or "").strip()]:
                t = get_template(cand)
                if t:
                    return t
            return None

        rows = list(self.normal_test_items or [])

        for r in rows:
            tpl = resolve_template_for_row(r)

            # If we can't resolve template, still print it under "Lab"
            if not tpl:
                dept = "Lab"
                add_row(dept, {
                    "test": "",
                    "lab_event": getattr(r, "lab_test_event", "") or "",
                    "lab_test_name": r.lab_test_name or "",
                    "result_value": r.result_value,
                    "lab_test_uom": getattr(r, "lab_test_uom", "") or "",
                    "normal_range": r.normal_range or "",
                })
                continue

            dept = (tpl.department or "Lab").strip()
            tpl_type = (tpl.lab_test_template_type or "").strip()

            # -------------------------
            # GROUPED (Electrolytes)
            # -------------------------
            if tpl_type == "Grouped":
                # In your new creation:
                # r.test = parent grouped template (e.g. Electrolytes)
                parent_group_name = (r.test or tpl.name or "").strip() or tpl.name

                # header once per grouped parent
                if parent_group_name not in processed_grouped:
                    add_row(dept, {
                        "test": parent_group_name,
                        "lab_event": "",
                        "lab_test_name": parent_group_name,
                        "result_value": "",
                        "lab_test_uom": "",
                        "normal_range": "",
                    })
                    processed_grouped.add(parent_group_name)

                # actual sub-test row (Sodium/Potassium/...)
                add_row(dept, {
                    "test": "",
                    "lab_event": getattr(r, "lab_test_event", "") or "",
                    "lab_test_name": r.lab_test_name or "",
                    "result_value": r.result_value,
                    "lab_test_uom": getattr(r, "lab_test_uom", "") or "",
                    "normal_range": r.normal_range or "",
                })
                continue

            # -------------------------
            # COMPOUND (LFT etc.)
            # -------------------------
            if tpl_type == "Compound":
                # Build the whole compound block ONCE, using the rows already on this Lab Result doc
                # Your compound creation sets: row.template = tpl.name
                if tpl.name in processed_compound:
                    continue

                # Header row (won't print because result_value is empty, but keeps structure)
                add_row(dept, {
                    "test": tpl.name,
                    "lab_event": "",
                    "lab_test_name": tpl.lab_test_name or tpl.name,
                    "result_value": "",
                    "lab_test_uom": "",
                    "normal_range": "",
                })

                compound_rows = [
                    x for x in rows
                    if (getattr(x, "template", "") or "").strip() == tpl.name
                ]

                # If somehow template field is missing, fallback to "test == tpl.name"
                if not compound_rows:
                    compound_rows = [x for x in rows if (x.test or "").strip() == tpl.name]

                for x in compound_rows:
                    add_row(dept, {
                        "test": "",
                        "lab_event": getattr(x, "lab_test_event", "") or "",
                        "lab_test_name": x.lab_test_name or getattr(x, "lab_test_event", "") or "",
                        "result_value": x.result_value,
                        "lab_test_uom": getattr(x, "lab_test_uom", "") or "",
                        "normal_range": x.normal_range or "",
                    })

                processed_compound.add(tpl.name)
                continue

            # -------------------------
            # SINGLE / Others (Blood)
            # -------------------------
            add_row(dept, {
                "test": "",
                "lab_event": getattr(r, "lab_test_event", "") or "",
                "lab_test_name": r.lab_test_name or (tpl.lab_test_name or tpl.name),
                "result_value": r.result_value,
                "lab_test_uom": getattr(r, "lab_test_uom", "") or (tpl.lab_test_uom or ""),
                "normal_range": r.normal_range or (getattr(tpl, "lab_test_normal_range", "") or ""),
            })

        return out

        

    # def after_insert(self):
    # 	if self.prescription:
    # 		frappe.db.set_value("Lab Prescription", self.prescription, "lab_test_created", 1)
    # 		if frappe.db.get_value("Lab Prescription", self.prescription, "invoiced"):
    # 			self.invoiced = True
    # 	if self.template:
    # 		self.load_test_from_template()
    # 		self.reload()
    # def load_test_from_template(self):
    # 	lab_test = self
    # 	create_test_from_template(lab_test)
    # 	self.reload()




def create_test_from_template(lab_test):
    template = frappe.get_doc("Lab Test Template", lab_test.template)
    patient = frappe.get_doc("Patient", lab_test.patient)

    lab_test.lab_test_name = template.lab_test_name
    lab_test.result_date = getdate()
    lab_test.department = template.department
    lab_test.lab_test_group = template.lab_test_group
    lab_test.legend_print_position = template.legend_print_position
    lab_test.result_legend = template.result_legend
    lab_test.worksheet_instructions = template.worksheet_instructions

    # lab_test = create_sample_collection(lab_test, template, patient, None)
    lab_test = load_result_format(lab_test, template, None, None)



def load_result_format(lab_test, template, prescription, invoice):
    if template.lab_test_template_type == "Single":
        create_normals(template, lab_test)

    elif template.lab_test_template_type == "Compound":
        create_compounds(template, lab_test, False)

    elif template.lab_test_template_type == "Descriptive":
        create_descriptives(template, lab_test)

    elif template.lab_test_template_type == "Grouped":
        # Iterate for each template in the group and create one result for all.
        for lab_test_group in template.lab_test_groups:
            # Template_in_group = None
            if lab_test_group.lab_test_template:
                template_in_group = frappe.get_doc("Lab Test Template", lab_test_group.lab_test_template)
                if template_in_group:
                    if template_in_group.lab_test_template_type == "Single":
                        create_normals(template_in_group, lab_test)

                    elif template_in_group.lab_test_template_type == "Compound":
                        normal_heading = lab_test.append("normal_test_items")
                        normal_heading.lab_test_name = template_in_group.lab_test_name
                        normal_heading.require_result_value = 0
                        normal_heading.allow_blank = 1
                        normal_heading.template = template_in_group.name
                        create_compounds(template_in_group, lab_test, True)

                    elif template_in_group.lab_test_template_type == "Descriptive":
                        descriptive_heading = lab_test.append("descriptive_test_items")
                        descriptive_heading.lab_test_name = template_in_group.lab_test_name
                        descriptive_heading.require_result_value = 0
                        descriptive_heading.allow_blank = 1
                        descriptive_heading.template = template_in_group.name
                        create_descriptives(template_in_group, lab_test)

            else:  # Lab Test Group - Add New Line
                normal = lab_test.append("normal_test_items")
                normal.lab_test_name = lab_test_group.group_event
                normal.lab_test_uom = lab_test_group.group_test_uom
                normal.secondary_uom = lab_test_group.secondary_uom
                normal.conversion_factor = lab_test_group.conversion_factor
                normal.normal_range = lab_test_group.group_test_normal_range
                normal.allow_blank = lab_test_group.allow_blank
                normal.require_result_value = 1
                normal.template = template.name

    if template.lab_test_template_type != "No Result":
        if prescription:
            lab_test.prescription = prescription
            if invoice:
                frappe.db.set_value("Lab Prescription", prescription, "invoiced", True)
        lab_test.save(ignore_permissions=True)  # Insert the result
        return lab_test


def create_compounds(template, lab_test, is_group):
    lab_test.normal_toggle = 1
    for normal_test_template in template.normal_test_templates:
        normal = lab_test.append("normal_test_items")
        if is_group:
            normal.lab_test_event = normal_test_template.lab_test_event
        else:
            normal.lab_test_name = normal_test_template.lab_test_event

        normal.lab_test_uom = normal_test_template.lab_test_uom
        normal.secondary_uom = normal_test_template.secondary_uom
        normal.conversion_factor = normal_test_template.conversion_factor
        normal.normal_range = normal_test_template.normal_range
        normal.require_result_value = 1
        normal.allow_blank = normal_test_template.allow_blank
        normal.template = template.name




def create_normals(template, lab_test):
    lab_test.normal_toggle = 1
    normal = lab_test.append("normal_test_items")
    normal.lab_test_name = template.lab_test_name
    normal.lab_test_uom = template.lab_test_uom
    normal.secondary_uom = template.secondary_uom
    normal.conversion_factor = template.conversion_factor
    normal.normal_range = template.lab_test_normal_range
    normal.require_result_value = 1
    normal.allow_blank = 0
    normal.template = template.name

