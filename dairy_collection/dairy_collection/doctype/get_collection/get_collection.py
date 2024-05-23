
import frappe
import requests
import json
from frappe.model.document import Document

class GetCollection(Document):
    
    def before_save(self):
        url = 'https://smartx.shivinfotech.co.in/api/mydairy'
        headersList = {
            "Accept": "*/*",
            "User-Agent": "BDF",
            "Content-Type": "application/json" 
        }
        payload = json.dumps({
            "Shift": str(self.shift),
            "FromDate": str(self.from_date),
            "ToDate": str(self.to_date),
            "StationId": str(self.station_id)
            
        })
        is_exists = frappe.db.exists('Get Collection',{
            "shift":self.shift,
            "from_date":self.from_date,
            "to_date":self.to_date,
            "station_id":self.station_id
        })
         
        # frappe.throw("hello")
        if not is_exists:
            response = requests.request("POST", url, data=payload,  headers=headersList)
            dairy_collections = response.json()
            # frappe.throw(str(dairy_collections))
            if response.status_code == 200 and dairy_collections["IsValid"]:
                if dairy_collections["Data"]!= None and dairy_collections["Data"]:
                    for item in dairy_collections["Data"]:
                        doc_exists = frappe.db.exists("Dairy Collection", {
                                            "farmer_id": item["FarmerId"],
                                            "entry_date": item["EntryDate"],
                                            "milk_type": item["MilkType"],
                                            "shift": item["Shift"]})
                        
                        
                        if doc_exists:
                            doc = frappe.get_doc("Dairy Collection", {
                                            "farmer_id": item["FarmerId"],
                                            "entry_date": item["EntryDate"],
                                            "milk_type": item["MilkType"],
                                            "shift": item["Shift"]})
                            doc.update({
                                doc.farmer_id : item["FarmerId"],
                                doc.station_id : item["StationId"],
                                doc.sample_no :item["SampleNo"],
                                doc.qty : item["Qty"],
                                doc.fat : item["Fat"],
                                doc.snf : item["Snf"],
                                doc.water : item["Water"],
                                doc.clr : item["Clr"],
                                doc.shift : item["Shift"],
                                doc.milk_type : item["MilkType"],
                                doc.entry_date : item["EntryDate"],
                                doc.time : item["Rate"],
                                doc.amount : item["Amount"]
                            })
                        else:    
                            doc = frappe.new_doc('Dairy Collection') 
                            doc.farmer_id = item["FarmerId"]
                            doc.station_id = item["StationId"]
                            doc.sample_no = item["SampleNo"]
                            doc.qty = item["Qty"]
                            doc.fat = item["Fat"]
                            doc.snf = item["Snf"]
                            doc.water = item["Water"]
                            doc.clr = item["Clr"]
                            doc.shift = item["Shift"]
                            doc.milk_type = item["MilkType"]
                            doc.entry_date = item["EntryDate"]
                            doc.time = item["Rate"]
                            doc.amount = item["Amount"]
                            doc.insert()
                            doc.save()
                    frappe.msgprint("Data saved succesfully")
                else:
                    frappe.throw("No data found")
            else:
                frappe.throw("Failed to fetch")
        else:
            frappe.throw("Data Already Inserted")
