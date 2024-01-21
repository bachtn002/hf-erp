# -*- coding: utf-8 -*-
{
    'name': "HR Account",
    'summary': """
        HR Account
    """,
    'description': """
        HR Account
    """,
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Account',
    'version': '0.1',
    'depends': ['base', 'account', 'account_accountant', 'ev_account_erpviet'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_personnel_expenses_views.xml'
    ],
}
