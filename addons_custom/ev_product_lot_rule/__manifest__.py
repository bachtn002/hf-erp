# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Product Lot Rule",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product'],

    # always loaded
    'data': [
        'security/product_lot_rule_security.xml',
        'security/ir.model.access.csv',
        'views/product_lot_rule_view.xml',
        # 'views/product_template_view.xml',
    ],
}
