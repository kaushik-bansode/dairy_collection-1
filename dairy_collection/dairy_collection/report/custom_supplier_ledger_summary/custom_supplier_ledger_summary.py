# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe 
from quantdairy.quantdairy.report.customer_ledger_summary_report.customer_ledger_summary_report import (
	PartyLedgerSummaryReport,
)


def execute(filters=None):
	args = {
		"party_type": "Supplier",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	frappe.throw(str(PartyLedgerSummaryReport))
	return PartyLedgerSummaryReport(filters).run(args)

