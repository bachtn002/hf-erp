# -*- coding: utf-8 -*-
{
    'name': "Return Goods Warehouse",

    'summary': """
        Return goods to the warehouse""",

    'description': """
        Return goods to the warehouse
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['base', 'stock', 'ev_stock_request'],
    'data': [
        'views/stock_return_product_warehouse.xml',
    ],
}
