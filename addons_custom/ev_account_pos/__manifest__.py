# -*- coding: utf-8 -*-
{
    'name': 'Account Pos',
    'version': '1.0',
    'category': 'point_of_sale',
    'summary': 'ERPViet',
    'description': """
""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'depends': ['base','point_of_sale', 'account'],
    'data': [
        'views/product_category.xml',
        #'views/pos_payment_method_view.xml'
    ],
    'installable': True,
}
