# -*- coding: utf-8 -*-
{
    'name': "Merge Partner",
    'summary': """
        Hợp nhất khách hàng
        """,
    'description': """
        Hợp nhất khách hàng
    """,
    'author': "ERPVIET",
    'website': "http://www.erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/merge_partner.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
