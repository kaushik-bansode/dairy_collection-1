// Copyright (c) 2024, quantdairy and contributors
// For license information, please see license.txt
//  eslint-disable 

frappe.query_reports["Sales Order Summary Script Report - Item and Route wise"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: "From Date",
			default:'Today',
			reqd: 1,
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: "To Date",
			default:'Today',
			reqd: 1,
		},
		{
			fieldname: "item_code",
			fieldtype: "Link",
			label: "Item Code",
			options: "Item",
			
		},
		{
			fieldname: "customer",
			fieldtype: "Link",
			label: "Customer",
			options: "Customer",
			
		},
		{
			fieldname: "route",
			fieldtype: "Link",
			label: "Route",
			options: "Route Master",
		},
		{
			fieldname: "item_group",
			fieldtype: "Link",
			label: "Item Group",
			options: "Item Group",
			
		},

	]
};
