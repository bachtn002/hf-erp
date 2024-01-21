# -*- coding: utf-8 -*-
{
    'name': "Stock picking cancel",

    'summary': """
        Stock picking cancel module is used for cancel the picking or move and set it to draft stage.
        """,

    'description': """
        Stock picking cancel module is used for cancel the picking or move and set it to draft stage.
    """,
    'author': "ERPVIET",
    'category': 'Warehouse',
    'version': '13.0.1',
    'depends': ['stock','stock_account'],
    'data': [
        'security/stock_security.xml',
        'views/stock_picking_view.xml',
    ],
}