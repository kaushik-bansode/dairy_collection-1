import frappe
import requests
from frappe.model.document import Document

class GetCollection(Document):
    
    @frappe.whitelist()
    def before_save(self,params=None):
        url = 'https://smartx.shivinfotech.co.in/api/mydairy'
        headers = {'Content-Type': 'application/json'}
        body = {
            "Shift": self.shift,
            "FromDate": self.from_date,
            "ToDate": self.to_date,
            "StationId": self.station_id
        }
        is_exists = frappe.db.exists('Get Collection',{
            "shift":self.shift,
            "from_date":self.from_date,
            "to_date":self.to_date,
            "station_id":self.station_id
        })
        
        if not is_exists:
            response = requests.post(url, json=body, headers=headers)
            dairy_collections = response.json()
            if response.status_code == 200 and dairy_collections["IsValid"]:
                if dairy_collections["Data"]!= None:
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
                    frappe.msgprint("Data saved succesfully")
                else:
                    frappe.throw("No data found")
            else:
                frappe.throw("Failed to fetch")
        else:
            frappe.throw("Data Already Inserted")
