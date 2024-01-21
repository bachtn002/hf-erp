# -*- coding: utf-8 -*-
{
    'name': "Pos Shop Product Config",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Pos Shop Product Config',
    'version': '0.1',
    'depends': ['base', 'ev_pos_shop'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_shop.xml',
        'views/product_template.xml',
        'views/import_file_product.xml',
    ],
    'qweb': [
    ],
}
