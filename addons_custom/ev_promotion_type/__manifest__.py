# -*- coding: utf-8 -*-
{
    'name': "Promotion Type",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['ev_pos_promotion'],

    'data': [
        'security/ir.model.access.csv',
        'views/promotion_type_view.xml',
        'views/pos_promotion_view.xml',
 
    ],
}
