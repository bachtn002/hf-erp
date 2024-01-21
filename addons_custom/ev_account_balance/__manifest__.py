# -*- coding: utf-8 -*-
{
    'name': "Account balance",

    'summary': """
        Account balance
        """,

    'description': """
        Account balance
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','base','account_accountant', 'ev_account_erpviet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_balance_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_company_view.xml',
        'views/account_balance_analytic_view.xml',
    ],
}