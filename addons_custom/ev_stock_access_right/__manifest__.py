# -*- coding: utf-8 -*-
{
    'name': "Warehouse access right",

    'summary': """
        Allow to set warehouse access right with user.
        """,

    'description': """
        Allow to set warehouse access right with user.
    """,

    'author': "ERPVIET",
    'category': 'Warehouse',
    'version': '14.0.1',
    'depends': ['stock'],
    # always loaded
    'data': [
        'data/data_rule.xml',
        'security/stock_security.xml',
        'views/res_users_view.xml',
        'views/stock_warehouse_view.xml'
    ],
}