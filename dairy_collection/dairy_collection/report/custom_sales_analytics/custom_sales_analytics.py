# # Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt
 

import frappe
from frappe import _, scrub
from frappe.utils import add_days, add_to_date, flt, getdate

from erpnext.accounts.utils import get_fiscal_year

def execute(filters=None):
    return Analytics(filters).run()

class Analytics(object):
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.date_field = (
            "transaction_date"
            if self.filters.doc_type in ["Sales Order", "Purchase Order"]
            else "posting_date"
        )
        self.months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.get_period_date_ranges()

    def run(self):
        self.get_columns()
        self.get_data()
        self.get_chart_data()

        # Skipping total row for tree-view reports
        skip_total_row = 0

        if self.filters.tree_type in ["Supplier Group", "Item Group", "Customer Group", "Territory"]:
            skip_total_row = 1

        return self.columns, self.data, None, self.chart, None, skip_total_row

    def get_columns(self):
        self.columns = [
            {
                "label": _(self.filters.tree_type),
                "options": self.filters.tree_type if self.filters.tree_type != "Order Type" else "",
                "fieldname": "entity",
                "fieldtype": "Link" if self.filters.tree_type != "Order Type" else "Data",
                "width": 140 if self.filters.tree_type != "Order Type" else 200,
            }
        ]
        if self.filters.tree_type in ["Customer", "Supplier", "Item","Route Master"]:
            self.columns.append(
                {
                    "label": _(self.filters.tree_type + " Name"),
                    "fieldname": "entity_name",
                    "fieldtype": "Data",
                    "width": 140,
                }
            )

        if self.filters.tree_type == "Item":
            self.columns.append(
                {
                    "label": _("UOM"),
                    "fieldname": "stock_uom",
                    "fieldtype": "Link",
                    "options": "UOM",
                    "width": 100,
                }
            )

        for end_date in self.periodic_daterange:
            period = self.get_period(end_date)
            self.columns.append({"label": _(period), "fieldname": scrub(period), "fieldtype": "Float", "width": 120})
        self.columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Float", "width": 120})

    def get_data(self):
        if self.filters.tree_type in ["Customer", "Supplier"]:
            self.get_sales_transactions_based_on_customers_or_suppliers()
            self.get_rows()

        elif self.filters.tree_type == "Item":
            self.get_sales_transactions_based_on_items()
            self.get_rows()

        elif self.filters.tree_type in ["Customer Group", "Supplier Group", "Territory"]:
            self.get_sales_transactions_based_on_customer_or_territory_group()
            self.get_rows_by_group()

        elif self.filters.tree_type == "Item Group":
            self.get_sales_transactions_based_on_item_group()
            self.get_rows_by_group()

        elif self.filters.tree_type == "Order Type":
            if self.filters.doc_type != "Sales Order":
                self.data = []
                return
            self.get_sales_transactions_based_on_order_type()
            self.get_rows_by_group()

        elif self.filters.tree_type == "Project":
            self.get_sales_transactions_based_on_project()
            self.get_rows()

    def get_sales_transactions_based_on_order_type(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total"
        else:
            value_field = "total_qty"

        self.entries = frappe.db.sql(
            """ select s.order_type as entity, s.{value_field} as value_field, s.{date_field}
            from `tab{doctype}` s where s.docstatus = 1 and s.company = %s and s.{date_field} between %s and %s
            and ifnull(s.order_type, '') != '' order by s.order_type
        """.format(
                date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type
            ),
            (self.filters.company, self.filters.from_date, self.filters.to_date),
            as_dict=1,
        )

        self.get_teams()

    def get_sales_transactions_based_on_customers_or_suppliers(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total as value_field"
        else:
            value_field = "total_qty as value_field"

        if self.filters.tree_type == "Customer":
            entity = "customer as entity"
            entity_name = "customer_name as entity_name"
        else:
            entity = "supplier as entity"
            entity_name = "supplier_name as entity_name"

        filters = {
        "docstatus": 1,
        "company": self.filters.company,
        self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
        }

        if self.filters.get("delivery_shift"):
            filters["delivery_shift"] = self.filters.delivery_shift

        if self.filters.get("warehouse"):
            filters["warehouse"] = self.filters.warehouse

        self.entries = frappe.get_all(
        self.filters.doc_type,
        fields=[entity, entity_name, value_field, self.date_field],
        filters=filters,
    )
        self.entity_names = {d.entity: d.entity_name for d in self.entries}
            # self.entries = frappe.get_all(
        #     self.filters.doc_type,
        #     fields=[entity, entity_name, value_field, self.date_field],
        #     filters={
        #         "docstatus": 1,
        #         "company": self.filters.company,
        #         self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
        #         "delivery_shift":self.filters.delivery_shift,
        #         "warehouse":self.filters.warehouse,
        #     },
        # )

        # self.entity_names = {}
        # for d in self.entries:
        #     self.entity_names.setdefault(d.entity, d.entity_name)

    def get_sales_transactions_based_on_items(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_amount"
        else:
            value_field = "stock_qty"

        self.entries = frappe.db.sql(
            """
            select i.item_code as entity, i.item_name as entity_name, i.stock_uom, i.{value_field} as value_field, s.{date_field}
            from `tab{doctype} Item` i , `tab{doctype}` s
            where s.name = i.parent and i.docstatus = 1 and s.company = %s
            and s.{date_field} between %s and %s
        """.format(
                date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type
            ),
            (self.filters.company, self.filters.from_date, self.filters.to_date),
            as_dict=1,
        )

        params = [self.filters.company, self.filters.from_date, self.filters.to_date]
        if self.filters.get("delivery_shift"):
            query += " AND s.delivery_shift = %s"
            params.append(self.filters.delivery_shift)

        if self.filters.get("warehouse"):
            query += " AND s.warehouse = %s"
            params.append(self.filters.warehouse)

        self.entries = frappe.db.sql(query, tuple(params), as_dict=1)
        self.entity_names = {}
        for d in self.entries:
            self.entity_names.setdefault(d.entity, d.entity_name)

    def get_sales_transactions_based_on_customer_or_territory_group(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total as value_field"
        else:
            value_field = "total_qty as value_field"

        if self.filters.tree_type == "Customer Group":
            entity_field = "customer_group as entity"
        elif self.filters.tree_type == "Supplier Group":
            entity_field = "supplier as entity"
            self.get_supplier_parent_child_map()
        else:
            entity_field = "territory as entity"

        self.entries = frappe.get_all(
            self.filters.doc_type,
            fields=[entity_field, value_field, self.date_field],
            filters={
                "docstatus": 1,
                "company": self.filters.company,
                self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
            },
        )
        self.get_groups()

    def get_sales_transactions_based_on_item_group(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_amount"
        else:
            value_field = "qty"

        self.entries = frappe.db.sql(
            """
            select i.item_group as entity, i.{value_field} as value_field, s.{date_field}
            from `tab{doctype} Item` i , `tab{doctype}` s
            where s.name = i.parent and i.docstatus = 1 and s.company = %s
            and s.{date_field} between %s and %s
        """.format(
                date_field=self.date_field, value_field=value_field, doctype=self.filters.doc_type
            ),
            (self.filters.company, self.filters.from_date, self.filters.to_date),
            as_dict=1,
        )

        self.get_groups()

    def get_sales_transactions_based_on_project(self):
        if self.filters["value_quantity"] == "Value":
            value_field = "base_net_total as value_field"
        else:
            value_field = "total_qty as value_field"

        entity = "project as entity"

        self.entries = frappe.get_all(
            self.filters.doc_type,
            fields=[entity, value_field, self.date_field],
            filters={
                "docstatus": 1,
                "company": self.filters.company,
                "project": ["!=", ""],
                self.date_field: ("between", [self.filters.from_date, self.filters.to_date]),
            },
        )

    def get_rows(self):
        self.data = []
        self.get_periodic_data()

        for entity, period_data in self.entity_periodic_data.items():
            row = {
                "entity": entity,
                "entity_name": self.entity_names.get(entity) if hasattr(self, "entity_names") else None,
            }
            total = 0
            for end_date in self.periodic_daterange:
                period = self.get_period(end_date)
                amount = flt(period_data.get(period, 0.0))
                row[scrub(period)] = amount
                total += amount
            row["total"] = total
            self.data.append(row)

    def get_rows_by_group(self):
        self.data = []
        self.get_periodic_data()

        for group, period_data in self.group_periodic_data.items():
            row = {
                "entity": group,
            }
            total = 0
            for end_date in self.periodic_daterange:
                period = self.get_period(end_date)
                amount = flt(period_data.get(period, 0.0))
                row[scrub(period)] = amount
                total += amount
            row["total"] = total
            self.data.append(row)

    def get_supplier_parent_child_map(self):
        self.parent_child_map = {}
        for d in frappe.get_all("Supplier", ["name", "supplier_group"]):
            if not self.parent_child_map.get(d.supplier_group):
                self.parent_child_map[d.supplier_group] = []
            self.parent_child_map[d.supplier_group].append(d.name)

    def get_groups(self):
        group_field = self.filters.tree_type.lower().replace(" ", "_")
        self.group_entries = frappe.get_all(
            self.filters.tree_type,
            fields=["name", "parent_" + group_field],
            filters={"is_group": 0},
        )
        self.group_entries = {d.name: d for d in self.group_entries}

    def get_teams(self):
        self.teams = frappe.get_all("Sales Team", fields=["name"])

    def get_periodic_data(self):
        self.entity_periodic_data = frappe._dict()
        self.group_periodic_data = frappe._dict()

        for d in self.entries:
            date = getdate(d[self.date_field])
            period = self.get_period(date)

            if hasattr(self, "entity_names"):
                self.entity_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
                self.entity_periodic_data[d.entity][period] += flt(d.value_field)

            if hasattr(self, "parent_child_map"):
                for parent in self.parent_child_map.get(d.entity, []):
                    self.group_periodic_data.setdefault(parent, frappe._dict()).setdefault(period, 0.0)
                    self.group_periodic_data[parent][period] += flt(d.value_field)

            if hasattr(self, "group_entries"):
                self.group_periodic_data.setdefault(d.entity, frappe._dict()).setdefault(period, 0.0)
                self.group_periodic_data[d.entity][period] += flt(d.value_field)

    def get_period(self, date):
        if self.filters.range == "Daily":
            return date.strftime("%d-%m-%Y")
        elif self.filters.range == "Weekly":
            week_start = getdate(add_to_date(date, days=-date.weekday()))
            week_end = getdate(add_to_date(week_start, days=6))
            return "{} to {}".format(week_start.strftime("%d-%m-%Y"), week_end.strftime("%d-%m-%Y"))
        elif self.filters.range == "Monthly":
            return self.months[date.month - 1] + " " + str(date.year)
        elif self.filters.range == "Quarterly":
            return "Quarter " + str((date.month - 1) // 3 + 1) + " " + str(date.year)
        elif self.filters.range == "Half-Yearly":
            return "Half-Year " + ("1" if date.month <= 6 else "2") + " " + str(date.year)
        elif self.filters.range == "Yearly":
            return str(date.year)

    def get_period_date_ranges(self):
        self.periodic_daterange = []
        start_date = getdate(self.filters.from_date)
        end_date = getdate(self.filters.to_date)

        if self.filters.range == "Daily":
            for i in range((end_date - start_date).days + 1):
                self.periodic_daterange.append(add_days(start_date, i))

        elif self.filters.range == "Weekly":
            week_start = start_date
            while week_start <= end_date:
                week_end = add_to_date(week_start, days=6)
                self.periodic_daterange.append(week_end if week_end <= end_date else end_date)
                week_start = add_to_date(week_start, days=7)

        elif self.filters.range == "Monthly":
            for d in self.get_monthly_date_ranges(start_date, end_date):
                self.periodic_daterange.append(d)

        elif self.filters.range == "Quarterly":
            quarter_start = start_date
            while quarter_start <= end_date:
                quarter_end = add_to_date(quarter_start, months=3, days=-1)
                self.periodic_daterange.append(quarter_end if quarter_end <= end_date else end_date)
                quarter_start = add_to_date(quarter_start, months=3)

        elif self.filters.range == "Half-Yearly":
            half_year_start = start_date
            while half_year_start <= end_date:
                half_year_end = add_to_date(half_year_start, months=6, days=-1)
                self.periodic_daterange.append(half_year_end if half_year_end <= end_date else end_date)
                half_year_start = add_to_date(half_year_start, months=6)

        elif self.filters.range == "Yearly":
            year_start = start_date
            while year_start <= end_date:
                year_end = add_to_date(year_start, years=1, days=-1)
                self.periodic_daterange.append(year_end if year_end <= end_date else end_date)
                year_start = add_to_date(year_start, years=1)

    def get_monthly_date_ranges(self, start_date, end_date):
        date_range = []
        month_start = start_date
        while month_start <= end_date:
            month_end = add_to_date(month_start, months=1, days=-1)
            date_range.append(month_end if month_end <= end_date else end_date)
            month_start = add_to_date(month_start, months=1)
        return date_range

    def get_chart_data(self):
        self.chart = {
            "data": {
                "labels": [self.get_period(end_date) for end_date in self.periodic_daterange],
                "datasets": [],
            },
            "type": "line",
            "colors": ["#7cd6fd", "#743ee2", "#ffa3ef", "#ff5858", "#00e676"],
        }

        for d in self.data:
            self.chart["data"]["datasets"].append(
                {
                    "name": d["entity"],
                    "values": [d.get(scrub(self.get_period(end_date)), 0) for end_date in self.periodic_daterange]
                }
            )

