# -*- coding: utf-8 -*-
{
    'name': "ERPVIET POS LOYALTY History",
    'summary': """
        Pos Loyalty History.
        """,
    'description': """
        Pos Loyalty History.
    """,
    'author': "ERPVIET",
    'website': "https://www.erpviet.vn",
    'category': 'point_of_sale',
    'version': '0.1',
    'depends': ['base', 'pos_loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml'
    ],
}