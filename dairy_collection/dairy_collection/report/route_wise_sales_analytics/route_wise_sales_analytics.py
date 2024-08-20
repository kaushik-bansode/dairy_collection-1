import frappe

def execute(filters=None):
    if not filters:
        filters = {}
    columns, data = [], []
    columns = get_columns()
    raw_data = get_data(filters)
    data = pivot_data(raw_data)

    return columns, data

def get_columns():
    # Get distinct route names for dynamic column generation
    routes = frappe.db.sql("SELECT name FROM `tabRoute Master`", as_list=True)
    columns = [
        {
            'fieldname': "item_code",
            'fieldtype': "Link",
            'label': "Item Code",
            'options': "Item",
        },
        {
            'fieldname': "item_name",
            'fieldtype': "Data",
            'label': "Item Name",
        },
        
    ]

    for route in routes:
        route_name = route[0]
        columns.append({
            'fieldname': f"qty_{route_name}",
            'fieldtype': "Float",
            'label': f"Quantity ({route_name})",
        })
        columns.append({
            'fieldname': f"amount_{route_name}",
            'fieldtype': "Currency",
            'label': f"Amount ({route_name})",
        })
    columns.append({
        'fieldname': "total_qty",
        'fieldtype': "Float",
        'label': "Total Quantity",
    })
    columns.append({
        'fieldname': "total_amount",
        'fieldtype': "Currency",
        'label': "Total Amount",
    })

    return columns

def get_data(filters):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    company = filters.get('company')
    item_code = filters.get('item_code')
    Warehouse = filters.get('Warehouse')
    gatepass = filters.get('gatepass')
    conditions = []
    params = [from_date, to_date, company]

    sql_query = """
        SELECT
            r.name AS route,
            y.item_code AS item_code,
            y.item_name AS item_name,
            SUM(y.stock_qty) AS qty,
            SUM(y.base_amount) AS amount,
            g.warehouse AS Warehouse,
            c.parent as gatepass
        FROM
            `tabRoute Master` r
        LEFT JOIN
            `tabSales Invoice` x ON r.name = x.route
        LEFT JOIN
            `tabSales Invoice Item` y ON x.name = y.parent
        left join 
            `tabCrate Summary` c on x.name= c.voucher 
        left join
            `tabGate Pass`g on g.name = c.parent
        WHERE
            x.posting_date BETWEEN %s AND %s and x.docstatus = 1 
            AND x.company = %s
    """
    
    if Warehouse:
        conditions.append("g.warehouse in %s")
        params.append(Warehouse)

    if item_code:
        conditions.append("y.item_code in %s")
        params.append(item_code)
        
    if gatepass:
        conditions.append("c.parent in %s")
        params.append(gatepass)

    if conditions:
        sql_query += " AND " + " AND ".join(conditions)

    sql_query += " GROUP BY r.name, y.item_code, y.item_name,c.parent"

    data = frappe.db.sql(sql_query, tuple(params), as_dict=True)
    return data

def pivot_data(raw_data):
    pivoted_data = {}
    for entry in raw_data:
        item_key = (entry['item_code'], entry['item_name'])
        if item_key not in pivoted_data:
            pivoted_data[item_key] = {
                'item_code': entry['item_code'],
                'item_name': entry['item_name'],
                'total_qty': 0,
                'total_amount': 0,
            }
        route_qty_field = f"qty_{entry['route']}"
        route_amount_field = f"amount_{entry['route']}"
        pivoted_data[item_key][route_qty_field] = entry.get('qty', 0)
        pivoted_data[item_key][route_amount_field] = entry.get('amount', 0)
        
        # Summing up the quantities and amounts
        pivoted_data[item_key]['total_qty'] += entry.get('qty', 0)
        pivoted_data[item_key]['total_amount'] += entry.get('amount', 0)

    # Ensure 'total_qty' and 'total_amount' are last in the dictionary
    final_data = []
    for key, data in pivoted_data.items():
        # Move total_qty and total_amount to the end of the dictionary
        total_qty = data.pop('total_qty')
        total_amount = data.pop('total_amount')
        data['total_qty'] = total_qty
        data['total_amount'] = total_amount
        final_data.append(data)

    return final_data
