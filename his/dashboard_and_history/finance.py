import frappe
from frappe import _, msgprint
from frappe.utils import getdate
from datetime import timedelta, date
from frappe.utils import nowdate
@frappe.whitelist()
def get_data(from_date , to_date):
	que = get_que(from_date , to_date)
	bills = get_bils(from_date , to_date)
	sales = get_sales(from_date , to_date)
	return [que , bills , sales]

@frappe.whitelist()
def get_que(from_date , to_date):
	que = frappe.db.sql(f"""
	
	select * from `tabQue` where date between '{from_date}' and '{to_date}'
	
	""", as_dict = 1)

	new_const = 0
	fallow_up = 0
	revisit = 0
	paid = 0
	unpaid = 0
	free = 0
	refer = 0
	for q in que:
		if q.que_type == "New Patient":
			new_const += 1
		if q.que_type == "Follow Up":
			fallow_up += 1
		if q.que_type  == "Revisit":
			revisit += 1
		if q.que_type  == "Refer":
			refer += 1
		if q.paid_amount:
			paid += q.paid_amount
		if not q.paid_amount and not q.is_free and q.que_type == "New Patient":
			unpaid += q.doctor_amount
		if q.is_free :
			free +=  q.doctor_amount
		
	return {"new" : new_const , "fall" : fallow_up , "rev" :  revisit , "paid" : paid ,"unpaid" : unpaid , "free" : free , "ref" : refer}


def get_bils(from_date , to_date):
	bills = frappe.db.sql(f""" 
	select
	source_order, 
	 sum(paid_amount) as paid,
	 sum(outstanding_amount) as unpaid
	   from `tabSales Invoice` 

	where posting_date between '{from_date}' and '{to_date}' and  is_free = 0 and docstatus = 1
	
	group by source_order 
	""", as_dict = 1)
	return bills

def get_sales(from_date , to_date):
	sales_sumery = []
	report_gl = frappe.get_doc("Report", "Sales Register")

	report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(from_date),
			"to_date": frappe.utils.getdate(to_date),
	
		}
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			)
	std_keys = ['posting_date' , 'outstanding_amount' , 'net_total' , 'invoice']
	sales = {}
	for key, value in data_gl[-1].items():
		# for key in d.keys():
		if key not in std_keys:
			if key[0].isdigit():
				sales[key.split('__')[1]] = value
			else:

				sales[key.split('__')[0]] = value
		# else:
		# 	sales[key] =value
	return sales 


def doctor_wise_sales(from_date , to_date):

	
	report_gl = frappe.get_doc("Report", "Sales Register")

	report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(from_date),
			"to_date": frappe.utils.getdate(to_date),
	
		}
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			)
	
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
def insurance():
    insurances = frappe.db.sql(f""" select patient, patient_name,mobile,source_order, posting_date, net_total from `tabSales Invoice` where docstatus=1 and posting_date= current_date() and is_insurance=1  """ , as_dict = True)

    return insurances

@frappe.whitelist()
def payables():

	
	report_gl = frappe.get_doc("Report", "Accounts Payable Summary")

	report_gl_filters = {
		"company":frappe.defaults.get_user_default("Company"),
		"report_date":nowdate(),
		"ageing_based_on":"Due Date",
		"range1": "30",
		"range2": "60",
		"range3": "90",
		"range4": "120",
	
		}
	data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			)
	return data_gl