# Copyright (c) 2024, quantdairy and contributors
# For license information, please see license.txt

import frappe   


def execute(filters=None):
    if not filters:
        filters = {}
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    return [
        {
            "fieldname": "date",
            "fieldtype": "Date",
            "label": "Date",
        },
        {
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "label": "Sales Order",
            "options": "Sales Order",
        },
        {
            "fieldname": "status",
            "fieldtype": "Data",
            "label": "Status",
        },
        {
            "fieldname": "customer",
            "fieldtype": "Link",
            "label": "Party",
            "options": "Customer",
        },
        {
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "label": "Party Name",
        },
        {
            "fieldname": "route",
            "fieldtype": "data",
            "label": "Route",
        },
        {
            "fieldname": "item_group",
            "fieldtype": "Link",
            "label": "Item Group",
            "options": "Item Group",
        },
        {
            "fieldname": "item_code",
            "fieldtype": "Link",
            "label": "Item Code",
            "options": "Item",
        },
        {
            "fieldname": "item_name",
            "fieldtype": "Data",
            "label": "Item Name",
        },
        {
            "fieldname": "uom",
            "fieldtype": "Data",
            "label": "UOM",
        },
        {
            "fieldname": "qty",
            "fieldtype": "float",
            "label": "QTY",
        },
        {
            "fieldname": "qty_per_stock_uom",
            "fieldtype": "float",
            "label": "QTY As Per Stock UOM",
        },
        {
            "fieldname": "total",
            "fieldtype": "Currency",
            "label": "Total",
        },
    ]


def get_data(filters):
    
    from_date = filters.get('from_date')
    to_date =  filters.get('to_date')
    item_code = filters.get('item_code')
    customer =  filters.get('customer')
    route =  filters.get('route')
    conditions = []
    params = [from_date, to_date]

    sql_query = """
                    SELECT DATE(s.creation) AS 'date', 
                    s.name AS 'sales_order', 
                    s.status AS 'status', 
                    s.customer AS 'Customer', 
                    s.customer_name AS 'customer_name', 
                    s.route AS 'route', 
                    i.item_code AS 'item_code',
                    i.item_name AS 'item_name', 
                    i.uom AS 'uom', 
                    SUM(si.qty) AS 'qty', 
                    i.stock_qty AS 'qty_per_stock_uom',
                    SUM(s.total) AS 'total'
                    FROM `tabSales Order` s
                    LEFT OUTER JOIN `tabSales Order Item` i ON s.name = i.parent
                    LEFT OUTER JOIN `tabSales Invoice Item` si ON s.name = si.sales_order AND si.item_code = i.item_code
                    WHERE DATE(s.creation) BETWEEN %s AND %s
                """

    
    if item_code:
        conditions.append("i.item_code = %s")
        params.append(item_code)

    if route:
        conditions.append("s.route = %s")
        params.append(route)

    if customer:
        conditions.append("s.customer = %s")
        params.append(customer)

    if conditions:
        sql_query += " AND " + " AND ".join(conditions)

    sql_query += """
                    GROUP BY s.creation, s.name, s.status, s.customer, s.customer_name, s.route, i.item_code, i.item_name, i.uom, i.stock_qty
                """

    data = frappe.db.sql(sql_query, tuple(params), as_dict=True)
    return data

	# data = frappe.db.sql(
	# 	"""
	# 		SELECT DATE(s.creation) AS 'Date', 
	# 		s.name AS 'Sales Order', 
	# 		s.status AS 'Status', 
	# 		s.customer AS 'Party', 
	# 		s.customer_name AS 'Party Name', 
	# 		s.route AS 'Route', 
	# 		i.item_code AS 'Item Code',
	# 		i.item_name AS 'Item Name', 
	# 		i.uom AS 'UOM', 
	# 		SUM(si.qty) AS 'Qty', 
	# 		i.stock_qty AS 'Qty as Per Stock UOM',
	# 		SUM(s.total) AS 'Total'
	# 		FROM `tabSales Order` s
	# 		LEFT OUTER JOIN `tabSales Order Item` i ON s.name = i.parent
	# 		LEFT OUTER JOIN `tabSales Invoice Item` si ON s.name = si.sales_order AND si.item_code = i.item_code
               
	# 		WHERE DATE(s.creation) BETWEEN %s AND %s
	# 		and i.item_code = %s and s.route = %s and s.customer = %s
	# 		GROUP BY s.creation, s.name, s.status, s.customer, s.customer_name, s.route, i.item_code, i.item_name, i.uom, i.stock_qty
	# 	""",(from_date, to_date, item_code ,route ,customer),as_dict="True",)
     
	
	# frappe.msgprint(str(data))




		#AND CASE WHEN (i.item_code = %(item_code)s THEN %(item_code)s ELSE '%%')
		#AND CASE WHEN (s.route = %(route)s THEN %(route)s ELSE '%%')
		#AND CASE WHEN (s.customer = %(customer)s THEN %(customer)s ELSE '%%')
