# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import datetime
from typing import List

import frappe
from frappe import _, scrub
from frappe.query_builder.functions import CombineDatetime
from frappe.utils import get_first_day as get_first_day_of_month
from frappe.utils import get_first_day_of_week, get_quarter_start, getdate
from frappe.utils.nestedset import get_descendants_of

from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from erpnext.stock.utils import is_reposting_item_valuation_in_progress

from dateutil.relativedelta import relativedelta
from datetime import timedelta


def execute(filters=None):
	is_reposting_item_valuation_in_progress()
	filters = frappe._dict(filters or {})
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(columns)

	return columns, data, None, chart


def get_columns(filters):
	columns = [
		{"label": _("Item"), "options": "Item", "fieldname": "name", "fieldtype": "Link", "width": 140},
		{
			"label": _("Item Name"),
			"options": "Item",
			"fieldname": "item_name",
			"fieldtype": "Link",
			"width": 140,
		},
		{
			"label": _("Item Group"),
			"options": "Item Group",
			"fieldname": "item_group",
			"fieldtype": "Link",
			"width": 140,
		},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Data", "width": 120},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 120},
	]

	ranges = get_period_date_ranges(filters)

	for dummy, end_date in ranges:
		period = get_period(end_date, filters)

		columns.append(
			{"label": _(period), "fieldname": scrub(period), "fieldtype": "Float", "width": 120}
		)

	return columns


def get_period_date_ranges(filters):
    from dateutil.relativedelta import relativedelta

    from_date = round_down_to_nearest_frequency(filters.from_date, filters.range)
    to_date = getdate(filters.to_date)

    increment = {
        "Daily": 1,
        "Weekly": 7,
        "Monthly": 1,
        "Quarterly": 3,
        "Half-Yearly": 6,
        "Yearly": 12
    }.get(filters.range, 1)

    periodic_daterange = []
    current_date = from_date

    while current_date <= to_date:
        if filters.range == "Weekly":
            period_end_date = current_date + relativedelta(days=6)
        elif filters.range == "Daily":
            period_end_date = current_date
        else:
            period_end_date = current_date + relativedelta(months=increment, days=-1)

        if period_end_date > to_date:
            period_end_date = to_date

        periodic_daterange.append([current_date, period_end_date])

        current_date = period_end_date + relativedelta(days=1)
        if period_end_date == to_date:
            break

    return periodic_daterange


def round_down_to_nearest_frequency(date: str, frequency: str) -> datetime.datetime:
    def _get_first_day_of_fiscal_year(date):
        fiscal_year = get_fiscal_year(date)
        return fiscal_year and fiscal_year[1] or date

    round_down_function = {
        "Daily": lambda d: d,
        "Weekly": get_first_day_of_week,
        "Monthly": get_first_day_of_month,
        "Quarterly": get_quarter_start,
        "Yearly": _get_first_day_of_fiscal_year,
    }.get(frequency, getdate)

    return round_down_function(getdate(date))

def get_period(posting_date, filters):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    if filters.range == "Daily":
        period = posting_date.strftime("%d %b %Y")
    elif filters.range == "Weekly":
        period = _("Week {0} {1}").format(str(posting_date.isocalendar()[1]), str(posting_date.year))
    elif filters.range == "Monthly":
        period = _(str(months[posting_date.month - 1])) + " " + str(posting_date.year)
    elif filters.range == "Quarterly":
        period = _("Quarter {0} {1}").format(
            str(((posting_date.month - 1) // 3) + 1), str(posting_date.year)
        )
    else:
        year = get_fiscal_year(posting_date, company=filters.company)
        period = str(year[2])

    return period


def get_periodic_data(entry, filters):
    expected_ranges = get_period_date_ranges(filters)
    expected_periods = []
    for _start_date, end_date in expected_ranges:
        expected_periods.append(get_period(end_date, filters))

    periodic_data = {}
    for d in entry:
        period = get_period(d.posting_date, filters)
        bal_qty = 0

        fill_intermediate_periods(periodic_data, d.item_code, period, expected_periods)

        if periodic_data.get(d.item_code) and not periodic_data.get(d.item_code).get(period):
            previous_balance = periodic_data[d.item_code]["balance"].copy()
            periodic_data[d.item_code][period] = previous_balance

        if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
            if periodic_data.get(d.item_code) and periodic_data.get(d.item_code).get("balance").get(
                d.warehouse
            ):
                bal_qty = periodic_data[d.item_code]["balance"][d.warehouse]

            qty_diff = d.qty_after_transaction - bal_qty
        else:
            qty_diff = d.actual_qty

        if filters["value_quantity"] == "Quantity":
            value = qty_diff
        else:
            value = d.stock_value_difference

        periodic_data.setdefault(d.item_code, {}).setdefault("balance", {}).setdefault(d.warehouse, 0.0)
        periodic_data.setdefault(d.item_code, {}).setdefault(period, {}).setdefault(d.warehouse, 0.0)

        periodic_data[d.item_code]["balance"][d.warehouse] += value
        periodic_data[d.item_code][period][d.warehouse] = periodic_data[d.item_code]["balance"][
            d.warehouse
        ]

    return periodic_data

def fill_intermediate_periods(
    periodic_data, item_code: str, current_period: str, all_periods: List[str]
) -> None:
    previous_period_data = None
    for period in all_periods:
        if period == current_period:
            return

        if (
            periodic_data.get(item_code)
            and not periodic_data.get(item_code).get(period)
            and previous_period_data
        ):
            periodic_data[item_code][period] = previous_period_data.copy()

        previous_period_data = periodic_data.get(item_code, {}).get(period)


def get_data(filters):
    data = []
    items = get_items(filters)
    sle = get_stock_ledger_entries(filters, items)
    item_details = get_item_details(items, sle)
    periodic_data = get_periodic_data(sle, filters)
    ranges = get_period_date_ranges(filters)

    today = getdate()

    for dummy, item_data in item_details.items():
        row = {
            "name": item_data.name,
            "item_name": item_data.item_name,
            "item_group": item_data.item_group,
            "uom": item_data.stock_uom,
            "brand": item_data.brand,
        }
        previous_period_value = 0.0
        for start_date, end_date in ranges:
            period = get_period(end_date, filters)
            period_data = periodic_data.get(item_data.name, {}).get(period)
            if period_data:
                row[scrub(period)] = previous_period_value = sum(period_data.values())
            else:
                row[scrub(period)] = previous_period_value if today >= start_date else None

        data.append(row)

    return data

def scrub(period):
    return period.replace(" ", "_").lower()

def get_chart_data(columns):
	labels = [d.get("label") for d in columns[5:]]
	chart = {"data": {"labels": labels, "datasets": []}}
	chart["type"] = "line"

	return chart


def get_items(filters):
	"Get items based on item code, item group or brand."
	if item_code := filters.get("item_code"):
		return [item_code]
	else:
		item_filters = {"is_stock_item": 1}
		if item_group := filters.get("item_group"):
			children = get_descendants_of("Item Group", item_group, ignore_permissions=True)
			item_filters["item_group"] = ("in", children + [item_group])
		if brand := filters.get("brand"):
			item_filters["brand"] = brand

		return frappe.get_all("Item", filters=item_filters, pluck="name", order_by=None)


def get_stock_ledger_entries(filters, items):
    sle = frappe.qb.DocType("Stock Ledger Entry")

    query = (
        frappe.qb.from_(sle)
        .select(
            sle.item_code,
            sle.warehouse,
            sle.posting_date,
            sle.actual_qty,
            sle.valuation_rate,
            sle.company,
            sle.voucher_type,
            sle.qty_after_transaction,
            sle.stock_value_difference,
            sle.item_code.as_("name"),
            sle.voucher_no,
            sle.stock_value,
            sle.batch_no,
        )
        .where((sle.docstatus < 2) & (sle.is_cancelled == 0))
        .orderby(CombineDatetime(sle.posting_date, sle.posting_time))
        .orderby(sle.creation)
        .orderby(sle.actual_qty)
    )

    if items:
        query = query.where(sle.item_code.isin(items))

    query = apply_conditions(query, filters)
    return query.run(as_dict=True)



def apply_conditions(query, filters):
    sle = frappe.qb.DocType("Stock Ledger Entry")
    warehouse_table = frappe.qb.DocType("Warehouse")

    if not filters.get("from_date"):
        frappe.throw(_("'From Date' is required"))

    if to_date := filters.get("to_date"):
        query = query.where(sle.posting_date <= to_date)
    else:
        frappe.throw(_("'To Date' is required"))

    if company := filters.get("company"):
        query = query.where(sle.company == company)

    if filters.get("warehouse"):
        query = apply_warehouse_filter(query, sle, filters)
    elif warehouse_type := filters.get("warehouse_type"):
        query = (
            query.join(warehouse_table)
            .on(warehouse_table.name == sle.warehouse)
            .where(warehouse_table.warehouse_type == warehouse_type)
        )

    return query



def get_item_details(items, sle):
    item_details = {}
    if not items:
        items = list(set(d.item_code for d in sle))

    if not items:
        return item_details

    item_table = frappe.qb.DocType("Item")

    query = (
        frappe.qb.from_(item_table)
        .select(
            item_table.name,
            item_table.item_name,
            item_table.description,
            item_table.item_group,
            item_table.brand,
            item_table.stock_uom,
        )
        .where(item_table.name.isin(items))
    )

    result = query.run(as_dict=1)

    for item in result:
        item_details.setdefault(item.name, item)

    return item_details
