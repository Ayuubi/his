import frappe
@frappe.whitelist()
def insert_to_gl_entery(**args):
    company = frappe.defaults.get_global_default("company")
    abbr = frappe.get_value("Company", company, "abbr")
    p_date=args.get("post_date")
    acc=args.get("account")
    am=args.get("amount")
    desc=args.get("des")
    part=args.get("party")
    em=args.get("emp_id")
    new_app = frappe.get_doc({
        "doctype" : "Journal Entry",
        "posting_date": p_date,
        "accounts": [{
        "account": acc,
        "debit_in_account_currency": am,
        "doctype": "Journal Entry Account"


                },
        {
        "account": "Creditors - "+abbr,
        "party_type": part,
        "party": em,
        "credit_in_account_currency": am,
        "doctype": "Journal Entry Account"


                }],
        "user_remark":desc
    })

    new_app.insert(ignore_permissions = 1)
    new_app.submit()
    return "Success"
@frappe.whitelist()
def Get_Cashier_Account(**args):
    casheir=args.get("user") 
    sql=frappe.db.sql(f""" select  

    account,
    against,
    posting_date     as Posting_Date ,
    owner   as User,

    (select  

    IFNULL (sum(Credit), 0) as Sales    

    from `tabGL Entry` A
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner='{casheir}'
    ) as Total_Sales ,


    (select  

    IFNULL (sum(Credit), 0) as Cash_Sales   

    from `tabGL Entry` B
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner='{casheir}'


    ) as Cash_Sales ,

    (select  
    IFNULL (sum(Credit), 0) as Sales    

    from `tabGL Entry` B
    where voucher_type like '%%Pay%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'

    and Debit = 0
    and owner='{casheir}'

    ) as Collected_Payments 


    , 

    (select  
    IFNULL (sum(Credit) , 0) as Sales   

    from `tabGL Entry` B
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner='{casheir}'



    ) +

    (select  
    IFNULL (sum(Credit), 0) as Sales    

    from `tabGL Entry` B
    where voucher_type like '%%Pay%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'

    and Debit = 0
    and owner='{casheir}'
    ) as Total_Cash_Expected 






    from `tabGL Entry` C
    where posting_date = current_date()
    and is_cancelled = 0
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner='{casheir}'
    group by 
    posting_date    , account,against,
    owner  """, as_dict=True)
    return sql

@frappe.whitelist()
def get_cashier_score(**args):
    casheir=args.get("c_name") 
    sql=frappe.db.sql(f""" select  

    account,
    against,
    posting_date     as Posting_Date ,
    owner   as User,


    (select  

    IFNULL (sum(Debit), 0) as Sales 

    from `tabGL Entry` A
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and owner='{casheir}'

    ) as Total_Sales ,


    (select  

    IFNULL (sum(Credit), 0) as Cash_Sales   

    from `tabGL Entry` B
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner='{casheir}'


    ) as Cash_Sales ,

    (select  
    IFNULL (sum(Credit), 0) as Sales    

    from `tabGL Entry` B
    where voucher_type like '%%Pay%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and owner = C.owner
    and party_type like '%%Cust%%'
    and owner='{casheir}'


    ) as Collected_Payments 


    , 

    (select  
    IFNULL (sum(Credit) , 0) as Sales   

    from `tabGL Entry` B
    where voucher_type like '%%Sales%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and Debit = 0
    and owner = C.owner
    and owner='{casheir}'



    ) +

    (select  
    IFNULL (sum(Credit), 0) as Sales    

    from `tabGL Entry` B
    where voucher_type like '%%Pay%%'
    and posting_date = current_date()
    and is_cancelled = 0
    and owner = C.owner
    and against = C.against
    and party_type like '%%Cust%%'
    and owner='{casheir}'

    and Debit = 0

    ) as Total_Cash_Expected 

    from `tabGL Entry` C
    where posting_date = current_date()
    and is_cancelled = 0
    and party_type like '%%Cust%%'
    and owner = C.owner
    and owner='{casheir}'

    group by 
    posting_date    , account,against,
    owner """, as_dict=True)
    return sql

@frappe.whitelist()
def Daily_Cashier_Status(**args):
    company = frappe.defaults.get_global_default("company")
    abbr = frappe.get_value("Company", company, "abbr")
    cash=args.get("cash_in_hand") 
    dat=args.get("posting_date") 
    user=args.get("user") 
    accoun=args.get("account") 
    cash_exp=args.get("expected") 
    msg=""
    query=frappe.db.sql(f""" select count(*) as num from `tabDaily Cashier Status` where posting_date='{dat}' and user='{user}'  """ , as_dict=True)
    for i in query:
        if i.num>0:
            msg="Already sent your Cash Closing to main cashier Today!"
        else:

            msg="Waiting to Approve Main Cashier!!"
            frappe.db.sql(f""" update `tabDaily Cashier Status` set status='Requesting To Approve' where posting_date='{dat}' and  user='{user}'  """)
            Cashier_Status = frappe.get_doc({
            "doctype" : "Daily Cashier Status",
            "status" : "Requesting To Approve",
            "user": user,
            "posting_date": dat,
            "total_cash_expected":cash_exp,
            "accounts": [{
            "account": accoun,
            "credit_in_account_currency": cash,
            "recash_date":dat,
            "username":user,
            "doctype": "Journal Entry Account"
            },
            {
            "account": "Main Cashier - "+abbr,
            "debit_in_account_currency": cash,
            "recash_date":dat,
            "username":user,
            "doctype": "Journal Entry Account"
            }]
            })
            Cashier_Status.insert(ignore_permissions = 1)
            frappe.msgprint(str())
           
    

@frappe.whitelist()
def daily_cashier_closing_status(**args):
    date=args.get("pos_date")
    user=args.get("user")
    status=args.get("status")
    message=args.get("message")
    if status=="Requesting To Approve":
        frappe.db.sql(f""" update `tabDaily casheir cash closing` set status='Rejected!' where posting_date="{date}" and  full_name ="{user}"  """)
        frappe.db.sql(f""" update `tabDaily Cashier Status` set status='Rejected!' where posting_date="{date}" and  user ="{user}"  """)
        frappe.db.sql(f""" update `tabDaily casheir cash closing` set message='{message}' where posting_date="{date}" and  full_name ="{user}"  """)
        print(args)
        frappe.msgprint("Rejected Success!!")
        #return message
        

@frappe.whitelist()
def daily_cashier_approved(**args):
    post_date=args.get("pos_date")
    user=args.get("user")
    frappe.db.sql(f""" update `tabDaily casheir cash closing` set status='Approved!' where posting_date="{post_date}" and  full_name ="{user}"  """)
    frappe.db.sql(f""" update `tabDaily Cashier Status` set status='Approved!' where posting_date="{post_date}" and  user ="{user}"  """)
    print(args)
@frappe.whitelist()
def note(**args):
    post_date=args.get("posting_date")
    user=args.get("user")
    note=args.get("note")
    frappe.db.sql(f""" update `tabDaily Cashier Status` set note="{note}" where posting_date="{post_date}" and  user ="{user}"  """)
    print(args)
    return "Success"

@frappe.whitelist()
def Create_new_doc_cash_closing(**args):
    post_date=args.get("posting_date")
    user=args.get("user")
    msg=""
    sql=frappe.db.sql(f""" select count(*) as num from `tabDaily casheir cash closing` where posting_date='{args.get("posting_date")}' and full_name='{args.get("user")}'  """ , as_dict=True)
    for i in sql:

        if i.num>0:
            msg="Already sent your Cash Closing to main cashier Today!"
        else:
            msg="Waiting to Approve Main Cashier!!"
            Cash_Closing = frappe.get_doc({
            "doctype" : "Daily casheir cash closing",
            "full_name":args.get("user"),
            "account":args.get("account"),
            "posting_date": args.get("posting_date"),
            "status":args.get("status"),
            "total_sales": args.get("total_sales"),
            "cash_sales":args.get("cash_sales"),
            "collected_payments": args.get("collected_payments"),
            "total_cash_expected": args.get("total_cash_expected"),
            "cash_in_hand": args.get("cash_in_hand"),
            "diffrence": args.get("diffrence")


            })

            Cash_Closing.insert(ignore_permissions = True)
        return msg

@frappe.whitelist()
def request(**args):
    date=args.get("posting_date")
    user=args.get("user")
    recash=args.get("recash")
    status=args.get("status")
    accoun=args.get("account")
    if status=='Rejected!':
        frappe.db.sql(f""" update `tabJournal Entry Account` set  credit_in_account_currency={recash}  where recash_date ='{date}' and username="{user}" and Account='{accoun}' """)
        frappe.db.sql(f""" update `tabJournal Entry Account` set debit_in_account_currency={recash}  where recash_date ='{date}' and username="{user}" and Account like '%%Main Cashie%%'  """)
        frappe.db.sql(f""" update `tabDaily casheir cash closing` set cash_in_hand="{recash}" where posting_date="{date}" and  full_name ="{user}"  """)
        frappe.db.sql(f""" update `tabDaily casheir cash closing` set status='Requesting To Approve' where posting_date="{date}" and  full_name ="{user}"  """)
        frappe.db.sql(f""" update `tabDaily Cashier Status` set status='Requesting To Approve' where posting_date="{date}" and  user ="{user}"  """)


        
    
        return "Your request has been reached"

@frappe.whitelist()
def get_Main_Cashier(**args):
    user=args.get("user") 
    date=args.get("posting_date")
    sql=frappe.db.sql(f""" select account, owner, ifnull(sum(debit),0)-ifnull(sum(credit),0) as Total from `tabGL Entry` where account like '%%Main Cashie%%' and posting_date=current_date() and is_cancelled=0 """, as_dict=True)
    return sql

    

    
    

    
    
