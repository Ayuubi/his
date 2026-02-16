import  frappe
@frappe.whitelist()
def all():
    que = frappe.db.sql(f""" select count(*) as num from `tabQue` """ , as_dict = True)

    return que

@frappe.whitelist()
def week():
    que = frappe.db.sql(f""" select count(*) as num from `tabQue` where  week(date) = WEEK(current_date());""" , as_dict = True)

    return que

@frappe.whitelist()
def month():
    que = frappe.db.sql(f""" select count(*) as num from `tabQue` where month(date)=month(current_date()) """ , as_dict = True)

    return que
        
@frappe.whitelist()
def year():
    que = frappe.db.sql(f""" select count(*) as num from `tabQue` where YEAR(date) = YEAR(CURDATE()) """ , as_dict = True)

    return que
@frappe.whitelist()
def today():
    que = frappe.db.sql(f""" select count(*) as num from `tabQue` where date=current_date() """ , as_dict = True)

    return que




@frappe.whitelist()
def account_balance():
    
    abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
    report_re = frappe.get_doc("Report", "General Ledger")
    report_re_filters = {
        
        "company": frappe.defaults.get_user_default("company"),
        # "party_type": "Customer",
        "from_date": frappe.utils.getdate(),
        "to_date": frappe.utils.getdate(),
        "account":["1100 - Cash In Hand - "+abbr, "1200 - Bank Accounts - "+abbr],
        "group_by": "Group By Account" ,



    }

    columns_re, data_re = report_re.get_data(
            limit=500, user="Administrator", filters=report_re_filters, as_dict=True
    )
    acc={}
    res=[]
    debit=0
    credit=0
    for i in data_re:
        if i.posting_date:
            if i.account not in acc:
                if i.credit:
                        acc[i.account]=i.credit*-1
                if i.debit:
                        acc[i.account]=i.debit

            else:                   
                if i.credit:
                        acc[i.account]-=i.credit
                if i.debit:
                    acc[i.account]+=i.debit


    if acc:
        for key, value in acc.items():
            res.append({
                "account": key,
                "balance": value
                })
            
        return res
       
        

@frappe.whitelist()
def cards():
    ins=[]
    que = frappe.db.sql(f""" select count(*) as que from `tabQue` where date=current_date() and status="Closed" """ , as_dict = True)
    open_que = frappe.db.sql(f""" select count(*) as que from `tabQue` where date=current_date() and status="Open" """ , as_dict = True)
    encounter = frappe.db.sql(f""" select count(*) as num from `tabPatient Encounter` where encounter_date=current_date() """ , as_dict = True)
    invoices = frappe.db.sql(f""" select count(*) as num from `tabSales Invoice` where docstatus=1 and posting_date= current_date() and status in ("paid","Partly Paid") """ , as_dict = True)
    unpaid = frappe.db.sql(f""" select count(*) as num from `tabSales Invoice` where docstatus=1 and posting_date= current_date() and status="Unpaid" and source_order="OPD" """ , as_dict = True)
    lab = frappe.db.sql(f""" select count(*) as num from `tabLab Result` where docstatus=1 and date=current_date()""" , as_dict = True)
    lab_draft = frappe.db.sql(f""" select count(*) as num from `tabLab Result` where docstatus=0 and date=current_date()""" , as_dict = True)
    
    radiology = frappe.db.sql(f""" select count(*) as num from `tabRadiology` where docstatus=1 and date=current_date()""" , as_dict = True)
    radiology_draft = frappe.db.sql(f""" select count(*) as num from `tabRadiology` where docstatus=0 and date=current_date()""" , as_dict = True)
    unpaid_list = frappe.db.sql(f""" select patient, patient_name,mobile,source_order, posting_date, outstanding_amount from `tabSales Invoice` where docstatus=1 and posting_date= current_date() and status in ("Unpaid","Partly Paid") and source_order="OPD" """ , as_dict = True)
    insurance_list = frappe.db.sql(f""" select patient, patient_name,mobile,source_order, posting_date, net_total from `tabSales Invoice` where docstatus=1 and posting_date= current_date() and is_insurance=1  """ , as_dict = True)
    ubilled_order = frappe.db.sql(f""" select patient, patient_name,ref_practitioner, transaction_date,grand_total from `tabSales Order` where docstatus = 1 and transaction_date= current_date() and status="To Deliver and Bill" """ , as_dict = True)
    Ot_schedule = frappe.db.sql(f""" select patient, patient_name,practitioner, appointment_time from `tabOT Schedule` where  appointment_date= current_date() """ , as_dict = True)
    for i in insurance_list:
        ins.append({
            'patient': i.patient,
            'patient_name': i.patient_name,
            'mobile': i.mobile,
            'insurance': frappe.db.get_value("Patient",i.patient,"ref_insturance"),
            'posting_date': i.posting_date,
            'total': i.net_total
            })
    return que, encounter,invoices, lab, radiology, lab_draft, radiology_draft,open_que,unpaid,unpaid_list,ins,ubilled_order,Ot_schedule
        
@frappe.whitelist()
def doctorwise():
    doc = frappe.db.sql(f""" 
        select
        Practitioner,
        count(name) Qty,
        sum(paid_amount) as Amount

         from `tabQue` where date=current_date() group by Practitioner 
     """ , as_dict = True)

    return doc  

@frappe.whitelist()
def departmentwise():
    doc = frappe.db.sql(f""" 
        select
        department,
        count(name) Qty,
        sum(paid_amount) as Amount

         from `tabQue` where date=current_date()  group by department 
     """ , as_dict = True)

    return doc  


@frappe.whitelist()
def open_que():
    doc = frappe.db.sql(f""" 
        select
        patient_name,
        practitioner,
        status

         from `tabQue` where date=current_date() and status="Open"
     """ , as_dict = True)

    return doc  

@frappe.whitelist()
def doctor_wise_que():
    doc = frappe.db.sql(f""" 
        select
        practitioner,
        SUM(if(que_type = 'New Patient', 1, 0)) AS New,
        SUM(if(que_type = 'Follow Up', 1, 0)) AS 'FollowUp',
        SUM(if(que_type = 'Refer', 1, 0)) AS 'Refer',
        SUM(if(que_type = 'Revisit', 1, 0)) AS 'Revisit',

        SUM(if(que_type = 'New Patient', 1, 0)+if(que_type = 'Follow Up', 1, 0)+if(que_type = 'Refer', 1, 0)+if(que_type = 'Revisit', 1, 0)) as Total,
        SUM(if(status = 'Open', 1, 0)) AS 'Open',
        SUM(if(status = 'Closed', 1, 0)) AS 'Closed'

         from `tabQue` where date=current_date() group by practitioner
     """ , as_dict = True)

    return doc  

@frappe.whitelist()
def department_wise_que():
    doc = frappe.db.sql(f""" 
        select
        department,
        SUM(if(que_type = 'New Patient', 1, 0)) AS New,
        SUM(if(que_type = 'Follow Up', 1, 0)) AS 'FollowUp',
        SUM(if(que_type = 'Refer', 1, 0)) AS 'Refer',
        SUM(if(que_type = 'Revisit', 1, 0)) AS 'Revisit',

        SUM(if(que_type = 'New Patient', 1, 0)+if(que_type = 'Follow Up', 1, 0)+if(que_type = 'Refer', 1, 0)+if(que_type = 'Revisit', 1, 0)) as Total,
        SUM(if(status = 'Open', 1, 0)) AS 'Open',
        SUM(if(status = 'Closed', 1, 0)) AS 'Closed'

         from `tabQue` where date=current_date() group by department
     """ , as_dict = True)

    return doc  


@frappe.whitelist()
def doctor_wise_income():
    res=[]
    practitioner=''
    
    totl_orders = frappe.db.sql(f""" 
        select
        s.ref_practitioner as ref_practitioner,
        i.item_group,
        sum(i.net_amount) as 'total_orders'

         from `tabSales Order` s 
         JOIN   `tabSales Order Item` i 
         ON s.name=i.parent 
         
         and s.docstatus=1 
         and s.transaction_date=current_date() 
         group by s.ref_practitioner, i.item_group
     """ , as_dict = True)
   
    totl_bills = frappe.db.sql(f""" 
        select
        s.ref_practitioner as ref_practitioner,
        i.item_group,
        sum(i.net_amount) as 'totl_bills'

         from `tabSales Invoice` s 
         JOIN   `tabSales Invoice Item` i 
         ON s.name=i.parent 
         
         and s.docstatus=1 
         and s.posting_date=current_date() 
         group by s.ref_practitioner
     """ , as_dict = True)

    # Convert list1 to a dictionary
    dict1 = {}
    for item in totl_orders:
        key = (item["ref_practitioner"], item["item_group"])
        dict1[key] = item

    # Merge list2 into dict1
    for item in totl_bills:
        key = (item["ref_practitioner"], item["item_group"])
        if key in dict1:
            dict1[key].update(item)
        else:
            dict1[key] = item

    # Convert dict1 back to a list
    merged_list = list(dict1.values())
   
    return merged_list


@frappe.whitelist()
def patient_wise_income():
    
    totl_orders = frappe.db.sql(f""" 
        select
        s.patient as patient,
        i.item_group,
        sum(i.net_amount) as 'total_orders'

         from `tabSales Order` s 
         JOIN   `tabSales Order Item` i 
         ON s.name=i.parent 
         
         and s.docstatus=1 
         and s.transaction_date=current_date() 
         group by s.patient, i.item_group
     """ , as_dict = True)
   
    totl_bills = frappe.db.sql(f""" 
        select
        s.patient as patient,
        i.item_group,
        sum(i.net_amount) as 'totl_bills'

         from `tabSales Invoice` s 
         JOIN   `tabSales Invoice Item` i 
         ON s.name=i.parent 
         
         and s.docstatus=1 
         and s.posting_date=current_date() 
         group by s.patient, i.item_group
     """ , as_dict = True)
    frappe.errprint(totl_bills)
    # Convert list1 to a dictionary
    data = [{
        "patient" : "Cali" , 
        "que" : [{
            "total_bils":10,
            "total_order" : 20
        }

        ],
         "lab" : [{
            "total_bils":10,
            "total_order" : 20
        }
        ],

        "imaging" : [{
            "total_bils":10,
            "total_order" : 20
        }
        ],

         "ot" : [{
            "total_bils":10,
            "total_order" : 20
        }
        ],

         "pharmacy" : [{
            "total_bils":10,
            "total_order" : 20
        }
        ],
          "others" : [{
            "total_bils":10,
            "total_order" : 20
        }
        ],
    }]
    dict1 = {}
    for item in totl_orders:
        key = (item["patient"], item["item_group"])
        dict1[key] = item

    # Merge list2 into dict1
    for item in totl_bills:
        key = (item["patient"], item["item_group"])
        if key in dict1:
            dict1[key].update(item)
        else:
            dict1[key] = item

    # Convert dict1 back to a list
    patient_list = list(dict1.values())
        
    return patient_list