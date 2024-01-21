# -*- coding: utf-8 -*-
{
    'name': "ERPVIET POS LOYALTY",
    'summary': """
        Custom rank in Pos Loyalty.
        """,
    'description': """
        Custom rank in Pos Loyalty.
    """,
    'author': "ERPVIET",
    'website': "https://www.erpviet.vn",
    'category': 'point_of_sale',
    'version': '0.1',
    'depends': ['base', 'pos_loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_rank_view.xml',
        'views/pos_loyalty_views.xml',
        'views/res_partner_view.xml'
    ],
}