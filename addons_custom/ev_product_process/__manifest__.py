# -*- coding: utf-8 -*-
{
    'name': "Process Product",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'product',
    'version': '0.1',
    'depends': ['base','stock','ev_stock_custom'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/product_process_rule.xml',
        'views/product_process.xml',
        'views/product.xml',
        'views/stock_warehouse.xml',
        'security/security.xml'
    ],
}