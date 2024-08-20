// Copyright (c) 2024, quantdairy and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Route Wise Sales Analytics"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_start_date"),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_user_default("year_end_date"),
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "MultiSelectList",
			options: "Item",
			get_data: function(txt) {
				return frappe.db.get_link_options("Item", txt);
			},
			reqd: 0,
		},
		{
			fieldname: "Warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function(txt) {
				return frappe.db.get_link_options("Warehouse", txt);
			},
			reqd: 0,
		},
		{
			fieldname: "gatepass",
			label: __("Gate Pass"),
			fieldtype: "MultiSelectList",
			options: "Gate Pass",
			get_data: function(txt) {
				return frappe.db.get_link_options("Gate Pass", txt);
			},
			reqd: 0,
		},
		// {
		// 	fieldname: "item_code",
		// 	fieldtype: "Link",
		// 	label: "Item Code",
		// 	options: "Item",
		// },
	]
};
