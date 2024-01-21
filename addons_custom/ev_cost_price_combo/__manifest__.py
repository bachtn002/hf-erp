# -*- coding: utf-8 -*-
{
    'name': "Cost Price Combo",
    'summary': """
        Tính giá vốn combo
        """,
    'description': """
        Tính giá vốn combo
    """,
    'author': "ERPVIET",
    'website': "http://www.erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base', 'mail'],
    'data': [
        'data/cost_price_combo_sequence.xml',
        'security/ir.model.access.csv',
        'views/cost_price_combo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
