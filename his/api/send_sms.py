import requests
import datetime
import json
import frappe
import urllib.parse


# print(resp_dict1)
@frappe.whitelist()
def send_sms(mobile , messge):
    username = "xx"
    password = "XX"
    passs = urllib.parse.quote(password)
    payload = f"grant_type=password&username={username}&password={passs}"
    response = requests.request("POST", 'https://smsapi.hormuud.com/token', data=payload,
    headers={'content-type': "application/x-www-form-urlencoded"})
    resp_dict1 = json.loads(response.text)
    payload = {
    "senderid":"Jazeera Specialist Hospital",
    "mobile":mobile,
    "message":messge
    }
    sendsmsResp = requests.request("POST", 'https://smsapi.hormuud.com/api/SendSMS',data= json.dumps(payload),
    headers={'Content-Type':'application/json', 'Authorization': 'Bearer ' + resp_dict1['access_token']})

    respObj = json.loads(sendsmsResp.text)
    frappe.msgprint("Sent SMS")
    frappe.errprint(respObj)
    return respObj