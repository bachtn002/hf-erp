# -*- coding: utf-8 -*-
{
    'name': 'Account Stock',
    'version': '1.0',
    'category': 'Stock',
    'summary': 'ERPViet',
    'description': """
""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'depends': ['stock','stock_account', 'account','ev_account_erpviet'],
    'data': [
        'views/stock_warehouse.xml',
        'views/inventory_valuation_group_view.xml',
        'views/run_create_account_move.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
