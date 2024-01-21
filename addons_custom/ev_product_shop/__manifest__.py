# -*- coding: utf-8 -*-
{
    'name': "Pos Shop Product",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Pos Shop Product',
    'version': '0.1',
    'depends': ['base', 'ev_pos_shop', 'ev_stock_request', 'ev_sale_request', 'stock'],
    'data': [
        'views/assets.xml',
        'security/ir.model.access.csv',
        'views/sale_request.xml',
    ],
    'qweb': [
    ],
}
