# -*- coding: utf-8 -*-
{
    'name': "Account Payment Erpviet",

    'summary': """
        Account Payment Erpviet
        """,

    'description': """
        Account Payment Erpviet
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_accountant', 'ev_account_erpviet', 'purchase'],

    # always loaded
    'data': [
        'views/account_payment_view.xml',
        'security/ir.model.access.csv',
        'views/cash_expense_view.xml',
        # 'views/report_payment_bills.xml',
        # 'views/report_payment_bills_receipts.xml',
        'views/cash_in_view.xml',
        'views/bank_expense_view.xml',
        'views/bank_in_view.xml',
        # 'views/product_expense_views.xml',
        # 'views/product_template_view.xml',
        'data/ir_sequence_data.xml',
        # 'views/res_currency_view.xml',
        # 'views/agribank_report.xml',
        # 'views/viettinbank_report.xml',
        # 'views/bidv_report.xml',
        # 'views/vib_report.xml',
        # 'views/MB_reports.xml',
        # 'views/eximbank_report.xml',
        # 'views/vietcombank_report.xml',
        # 'views/debit_report.xml',
        # 'views/credit_report.xml',
        # 'views/res_bank_view.xml',
        # 'views/res_partner_account_payment.xml',
        # 'views/deposit_management_supplier_view.xml',
        # 'views/res_config_settings_view.xml',
        # 'views/allocate_deposit_supplier.xml',
        # 'views/deposit_management_purchase_view.xml',
        # 'views/standing_order_general.xml',
        # wizard
        # 'wizard/standing_order_general_print_unc_wizard_view.xml',
        # 'wizard/account_payment_unc_view_wizard.xml',
        # 'reports/vietcombank_report_unc.xml',
        # 'reports/bidv_report_unc.xml',
        # 'reports/viettinbank_report_unc.xml',
        # 'reports/template_bidv_unc_vendor.xml',
        # 'reports/template_vcb_unc_vendor.xml',
        # 'reports/template_vtb_unc_vendor.xml',
    ],
}
