# -*- coding: utf-8 -*-
{
    'name': "Account Bill",
    'author': "ERPVIET",
    'website': "https://www.erpviet.vn",

    # for the full list
    'category': 'ERPViet',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'ev_account_erpviet'],

    # always loaded
    'data': [
        'view/accountant_bill_view.xml',
        'data/ir_sequence_data.xml',
        'wizard/wizard_import_accountant_bill_line_view.xml',
        'report/print_accountant_bill.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
}
