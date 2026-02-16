import frappe

@frappe.whitelist(allow_guest = 1)
def get_p_histy(patient = ""):
    
    # frappe.msgprint(patient)
    vitals = vitals_h(patient)
    visits = visits_h(patient)
    labs = lab_h(patient)
    med = medic_h(patient)
    drug_pres = medic_hh(patient)
    
    comp = comp_h(patient)
    diag = diag_h(patient)
    imaging = imaging_h(patient)
    drug_sheet = drug_sheets(patient)
    doctor_progress_note  = progress_no(patient)
    nursing_progress_note  = progress_note(patient)
    procedures = pro(patient)
    news_action__chart = news(patient)
    lab_prescription=lab_pres_h(patient)
    doctor_plan  = plan(patient)
       
    vitals_cur = vitals_h(patient ,  True)
    labs_today = lab_h(patient , True)
    images  = imaging_h(patient , True)
    operation = surgery_h(patient)
    blood_transfusion = get_blood_transfusion(patient)
    dental_plan = get_dental_plan(patient)


    # docplan  = doc_plan(patient)

    
    all_his =  [visits , vitals , labs , med , comp , diag , imaging , vitals_cur , labs_today ,images , drug_sheet , doctor_progress_note , nursing_progress_note, doctor_plan  , lab_prescription,drug_pres , operation , blood_transfusion, dental_plan]
    data = {}
    all_his_key =  ["visits" , "vitals" , "labs" , "med" , "comp" , "diag" , "imaging" , "vitals_cur" , "labs_today" ,"images" ,"drug_sheet" , "doctor_progress_note" , "nursing_progress_note", "doctor_plan" , "lab_prescription","drug_pres" , "operation" ,  "blood_transfusion", "dental_plan"]
    columns = {}
    for   index , history in enumerate(all_his):
        # frappe.errprint(history)
        columns[all_his_key[index]] = []
        data[all_his_key[index]] = []
        if history:
            for idx, h in enumerate(history):
                data_inner = {}
                for key , val in h.items():
                   
                    if idx == 0:
                        columns[all_his_key[index]].append(
                            
                            {"title":key, "field":key.replace(' ', '_').lower()  ,  "formatter":"html"},
                            
                        )
                    data_inner[key.replace(' ', '_').lower()] = val
                data[all_his_key[index]].append(
                    data_inner
                )

   
    return columns, data



@frappe.whitelist()
def get_blood_transfusion(patient):
     
    data = frappe.db.sql(f""" 
    
    select    date as Date , 
    type_of_blood as  `Type of Blood`,
    started_by as `Started By`
    from `tabBLOOD TRANSFUSION OBSERVATION CHART`

 
    where patient = "{patient}"
   
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def get_dental_plan(patient):
     
    data = frappe.db.sql(f""" 
    
    SELECT   
        p.name AS sr, 
        p.date AS Date, 
    
        p.treatment_status AS Status,
        p.total as Total,
         p.discount AS Discount,
        p.grand_total AS "Net Total",
       
        p.agreed_fee AS Agreed
      
    FROM  `tabDental Plan` p
    WHERE p.patient = "{patient}";

   
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def news(patient):
 
    data = frappe.db.sql(f""" 
    
    select    date as Date , 
    time as  `time`,
    news as `News` ,
    action as `Action`,
    reassessment_time as `Reassessment Time`,
    is_the_action_working as `Is The Action Working`
  
  
    from `tabNews Action Summery Chart`
 
    where patient = "{patient}"
   
    
    """ , as_dict = True)
    return data



@frappe.whitelist()
def pro(patient):
 
    data = frappe.db.sql(f""" 
    
    select    date as Date , 
    type_of_procedure as  `Type of Procedure`,
    practitioner as `Ordered by` ,
    carried_out_by as `Carried out by`,
    comment as Comment
  
    from `tabProcedures`
 
    where patient= "{patient}"
   
    
    """ , as_dict = True)
    return data




@frappe.whitelist()
def progress_no(patient):
 
    data = frappe.db.sql(f""" 
    
    select    date as Date , 
    practitioner as Doctor ,
    note as Note,
    full_name as User
    from `tabProgress Note`
 
    where patient= "{patient}"
    ORDER BY date DESC
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def progress_note(patient):
 
    data = frappe.db.sql(f""" 
    
    select    date as Date , 
    practitioner as Doctor ,
    note as Note,
    full_name as User
    from `tabNURSES PROGRESS NOTE`
 
    where patient= "{patient}"
    ORDER BY date DESC
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def drug_sheets(patient):
 
    data = frappe.db.sql(f""" 
    
    select   
    p.name as sr, 
     c.date  as Date, 
    c.time as Time , c.drug  as Drug, 
    c.type as `Root`,
     c.quantity as QTY ,
    
     p.nurse_name as Nurse
     from `tabTreatment Sheet` c
     left join `tabInpatient Medication` p
    on c.parent = p.name  
    where p.patient= "{patient}"
   Order by date DESC
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def vitals_h(patient , curr_date = False):
    condition = ''
    if curr_date:
        condition += 'and signs_date = current_date()'
    data = frappe.db.sql(f""" 
    
    select name as sr,   signs_date  as Date, 
    signs_time as Time ,
            temperature as Tem, pulse  as Pulse,
        bp_systolic as 'BP systolic', bp_diastolic as 'BP Diastolic',respiratory_rate as RR,
         spo as SPO2,
                       
         blood_sugar as `Blood Sugar`,
         height as Height,
         weight as Weight,  
       owner as `Nurse`
        from `tabVital Signs` where patient ='{patient}' {condition} Order by modified desc
   
   
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def visits_h(patient ):
    #  appointment_date  as Date,
    data = frappe.db.sql(f""" 
    
    select  
    name as sr, 
        date as Date,
    name  as `Visit No`,
   
    department  as Department, 
    practitioner as Doctor , 
    status as Status 

    from `tabQue`  
      where patient = "{patient}"
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def medic_h(patient ):
    #  appointment_date  as Date,
    data = frappe.db.sql(f""" 
    
     select p.name as sr,    p.encounter_date  as Date, 
     c.drug_code  as Drug, 
      c.qty as QTY ,
    c.dosage as `Dosage`,

    
     p.full_name as Ordered
     from `tabDrug Prescription` c
     left join `tabInpatient Order` p
    on c.parent = p.name    
      where p.patient = "{patient}" order by p.encounter_date DESC
    
    """ , as_dict = True)
    return data
@frappe.whitelist()
def lab_pres_h(patient ):
    #  appointment_date  as Date,
    data = frappe.db.sql(f""" 
    
     select    p.encounter_date  as Date, 
     c.lab_test_code  as Test, 
     
    
     p.practitioner as Doctor
     from `tabLab Prescription` c
     left join `tabInpatient Order` p
    on c.parent = p.name    
      where p.patient = "{patient}" order by p.encounter_date DESC
    
    """ , as_dict = True)
    return data

@frappe.whitelist()
def medic_hh(patient ):
    data = frappe.db.sql(f""" 
    
    select 
    p.name as sr, 
    d.drug_name  as drug, 
    d.dosage  as frequecny,
    d.period  as preriod ,
    d.parenttype,
    d.parent
    
  
    from `tabDrug Prescription` d  
	left join `tabPatient Encounter` p
    on d.parent = p.name  
    where p.patient= "{patient}"
  
    
    """ , as_dict = True)


    doc_plan = frappe.db.sql(f""" 
    
    select 
    
    d.drug_name  as Drug, 
    d.dosage  as Frequecy,
    d.period  as Prediod ,
 
    e.ref_practitioner as Consultant,
       e.date as Date

    
    
    from `tabIPD Drug Prescription` d 
      left join `tabDoctor Plan` e 
     on d.parent = e.name  
      where e.patient= "{patient}"
   
  
    
    """ , as_dict = True)

    #   where e.patient= "{patient}"
    # left join `tabPatient Encounter` e 
    # on d.parent = e.name 
    drug_pre_list = []
    for d in data:
        drug_pre = {}
        pa_doc = frappe.get_doc(d.parenttype , d.parent)
       
            
        if pa_doc.patient == patient:
            drug_pre['Drug'] = d.drug
            drug_pre['Frequecy'] = d.frequecny
            drug_pre['Prediod'] = d.preriod
            if d.parenttype == "Patient Encounter" or d.parenttype == "Emergency":
                drug_pre['Consultant'] = pa_doc.practitioner
                drug_pre['Date'] = pa_doc.encounter_date
            else:
                drug_pre['Consultant'] = pa_doc.practitioner
                drug_pre['Date'] = pa_doc.date

            drug_pre_list.append(drug_pre)    


    # frappe.errprint(data)
    return data


@frappe.whitelist()
def comp_h(patient ):
  
    data = frappe.db.sql(f""" 
  
   select
   p.name as sr, 
      p.encounter_date  as Date, 
      p.cheif_complaint as Complaint , 
   

   p.practitioner as Doctor
   from  `tabPatient Encounter` p
     
     where p.patient = '{patient}';

    """ , as_dict = True)
    return data



# @frappe.whitelist()
# def comp_h(patient = "PID-00012"):
#     data = frappe.db.sql(f""" 
    
#      select c.complaint , p.encounter_date , p.encounter_time from `tabPatient Encounter Symptom` c left join `tabPatient Encounter` p on c.parent = p.name where e.patient = "PID-00006";

#     """ , as_dict = True)
#     return data


@frappe.whitelist()
def diag_h(patient):
    data = frappe.db.sql(f""" 
    
   select 
   p.name as sr, 
   p.encounter_date as Date , 
   c.diagnosis as  Diagnosis , 
   
  
   p.practitioner as Doctor
   from `tabPatient Encounter Diagnosis` c left join `tabPatient Encounter` p 
   on c.parent = p.name 
   where p.patient = "{patient}";

    """ , as_dict = True)
    return data


@frappe.whitelist()
def lab_h(patient , curr_date = False):
    condition = ''
    if curr_date:
        condition += 'and date = current_date()'
    condition += ' and docstatus != 2' 
    data = frappe.db.sql(f""" 

    
            select 
            date  as Date,
            practitioner as Doctor,
            name
            from `tabLab Result`
            where patient = "{patient}"  {condition}
            order by date desc


         
          
            ;

        """ , as_dict = True)
    #    c.test as `Test Name`,
    #         c.lab_test_name as Test, 
            
    #   c.lab_test_event as Event,
    #         c.normal_range  as `Normal Range`, 
    #         c.result_value as Result 
    #         from `tabNormal Test Result` c 
    #         left join `tabLab Result` p 
    #         on c.parent = p.name 
    #         where p.patient = "{patient}"  {condition}
    #         order by c.creation 
    return data

@frappe.whitelist()
def lab_encounter(patient , encounter):
    data = frappe.db.sql(f""" 
    
            select 
            p.result_date  as Date,
            c.lab_test_name as Test, 
            c.lab_test_event as Event,
            c.normal_range  as `Normal Range`, 
            c.result_value as Result 
            from `tabNormal Test Result` c 
            left join `tabLab Result` p on c.parent = p.name 
            where p.patient = "{patient}" and p.patient_encounter = "{encounter}";

        """ , as_dict = True)
    return data

@frappe.whitelist()
def surgery_h(patient):
    data = frappe.db.sql(f""" 
    
            select 
            name as sr, 
             start_date as Date,  
           procedure_template as `Operation Name`,
           
           practitioner as Doctor
          
          
      
          
           
          
        
           from `tabClinical Procedure`
            where patient = "{patient}";

        """ , as_dict = True)
    return data


@frappe.whitelist()
def imaging_h(patient , curr_date = False):
    condition = ''
    if curr_date:
        condition += 'and date = current_date()'
    data = frappe.db.sql(f""" 
    
            select 
            name as sr, 
            date as Date,
         
            practitioner as Doctor,
        
           eximination  as Eximination, 
           indication as Indication 
            
        
           from `tabRadiology`
            where patient = "{patient}"  {condition}

            order by date desc
        """ , as_dict = True)
    return data



@frappe.whitelist()
def finalize(docname):
    encounter = frappe.get_doc("Patient Encounter" , docname)
    encounter.submit()

    return {"res" : "Submitted"}




@frappe.whitelist()
def delete_childoc_row(doctype , docname):
    frappe.delete_doc(doctype ,docname )
@frappe.whitelist()
def plan(patient):
#  doc_plan = frappe.db.get_value("Doctor Plan" , {"patient": patient, "docstatus": 0}, "name")
    doc_plan = frappe.db.sql(f"""
    select name from `tabDoctor Plan` where patient='{patient}' and docstatus=0

    """, as_dict = 1)

    return doc_plan





