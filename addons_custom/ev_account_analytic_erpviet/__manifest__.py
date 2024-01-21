# -*- coding: utf-8 -*-
{
    'name': "Account Analytic ERPViet",

    'summary': """
        Account Analytic ERPViet
        """,

    'description': """
        Account Analytic ERPViet
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'category': 'Account',
    'version': '0.1',

    'depends': ['account','ev_cash_statement','stock_account','analytic','ev_pos_shop'],

    # always loaded
    'data': [
        'views/pos_shop_view.xml'
    ],
}