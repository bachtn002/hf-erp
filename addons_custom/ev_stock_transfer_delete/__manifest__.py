# -*- coding: utf-8 -*-
{
    'name': "Stock transfer Delete",

    'summary': """
        Stock transfer warehouse Delete
        """,

    'description': """
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'stock',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['ev_stock_transfer'],

    # always loaded
    'data': [
        'security/stock_inventory.xml',
    ],
}
