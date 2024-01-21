# -*- coding: utf-8 -*-
{
    'name': "account_ponto",

    'summary': """
    """,

    'category': 'Accounting/Accounting',
    'version': '1.0',

    'depends': ['account_online_sync'],

    'data': [
        'views/ponto_views.xml',
    ],
    'qweb': [
        'views/ponto_template.xml',
    ],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
    'auto_install': True,
}
