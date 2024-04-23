// Copyright (c) 2024, Erpdata and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Payment Entry', {
	// refresh: function(frm) {

	// }
});



frappe.ui.form.on('Bulk Payment Entry', {
	setup: function (frm, cdt, cdn) {
		frm.fields_dict['bulk_payment_entry_details'].grid.get_field('party_type').get_query = function (doc, cdt, cdn) {
			return {
				filters: [
					['DocType', 'name', 'in', ['Customer', 'Supplier', 'Shareholder', 'Employee']]
				]
			};
		};
	}
});


frappe.ui.form.on('Bulk Payment Entry', {
	setup: function (frm) {
		frm.set_query("party_type", function (doc) {
			return {
				filters: [
					['DocType', 'name', 'in', ['Customer', 'Supplier', 'Shareholder', 'Employee']]
				]
			};
		});
	}
});

frappe.ui.form.on('Bulk Payment Entry Details', {
	check: function(frm) {
        frm.clear_table("payment_reference");
		frm.refresh_field('payment_reference');
		frm.call({
			method:'call_two_in_one',
			doc:frm.doc
		})
	}
});

frappe.ui.form.on('Bulk Payment Entry Details', {
	check2: function(frm) {
        frm.clear_table("payment_reference");
		frm.refresh_field('payment_reference');
		frm.call({
			method:'call_two_in_one',
			doc:frm.doc
		})
	}
});




frappe.ui.form.on('Bulk Payment Entry', {
	invoices: function(frm) {
        frm.clear_table("payment_reference");
		frm.refresh_field('payment_reference');
		frm.call({
			method:'invoices',
			doc:frm.doc
		})
	}
});

frappe.ui.form.on('Bulk Payment Entry', {
	orders: function(frm) {
        frm.clear_table("payment_reference");
		frm.refresh_field('payment_reference');
		frm.call({
			method:'orders',
			doc:frm.doc
		})
	}
});



frappe.ui.form.on('Bulk Payment Entry Details', {
	party: function (frm) {
		frm.call({
			method: 'get_accounts',
			doc: frm.doc
		})
	}
});

frappe.ui.form.on('Bulk Payment Entry Details', {
	bulk_payment_entry_details_add: function (frm, cdt, cdn) {
		frm.refresh_field("bulk_payment_entry_details")
		frm.call({
			method: 'set_party_type',
			doc: frm.doc
		})
		frm.clear_table("bulk_payment_entry_details");
	}
});


frappe.ui.form.on('Bulk Payment Entry Details', {
    bulk_payment_entry_details_remove: function(frm, cdt, cdn) {
        frm.clear_table("payment_reference");
        frm.refresh_field("payment_reference");
        frm.call({
            method: 'call_two_in_one',
            doc: frm.doc
        });
        frm.call({
            method: 'get_outstanding',
            doc: frm.doc
        });
    }
});

frappe.ui.form.on('Bulk Payment Entry Details', {
	party: function (frm, cdt, cdn) {
		frm.call({
			method: 'set_pn',
			doc: frm.doc
		})
	}
});

frappe.ui.form.on('Bulk Payment Reference', {
	allocated_amount: function (frm, cdt, cdn) {
		frm.call({
			method: 'get_allocatedsum',
			doc: frm.doc
		});
	}
});


frappe.ui.form.on('Bulk Payment Entry', {
	gate_pass: function (frm) {	
		frm.clear_table("bulk_payment_entry_details");
		frm.clear_table("payment_reference");
		frm.call({
			method: 'gate_pass_cll',
			doc: frm.doc
		});
		frm.refresh_table("bulk_payment_entry_details");
		
		frm.refresh_table("payment_reference");	
			
		
		
	},

});



frappe.ui.form.on("Bulk Payment Entry", {
	get_filter: function (frm) {
		frappe.call({
			method: 'gate',
			doc: frm.doc,
			callback: function (r) {
				if (r.message) {
					var k = r.message;
					frm.fields_dict.gate_pass.get_query = function (doc, cdt, cdn) {
						return {
							
							filters: [
								['Gate Pass', 'name', 'in', k],
							]
						};
					};
				}
			}
		});
	}
});



