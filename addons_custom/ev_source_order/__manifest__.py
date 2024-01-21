# -*- coding: utf-8 -*-
{
    'name': 'Source Order',
    'version': '1.0',
    'sequence': 1,
    'summary': '',
    'description': """""",
    'category': 'POS',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base', 'ev_sale_online'],
    'data': [
        'security/ir.model.access.csv',
        'views/source_order_view.xml',
        'views/sale_online_view.xml',
        'views/pos_order_view.xml',
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/pos_custom.xml'],
}
