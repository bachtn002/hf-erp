# -*- coding: utf-8 -*-
{
    'name': "account_online_sync",
    'summary': """""",

    'description': """
    """,

    'category': 'Accounting/Accounting',
    'version': '2.0',
    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'security/account_online_sync_security.xml',
        'views/online_sync_views.xml',
    ],
    'qweb': [
        'views/online_sync_templates.xml',
    ],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
    'auto_install': True,
}
