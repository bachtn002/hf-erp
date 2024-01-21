# -*- coding: utf-8 -*-

{
    'name': 'Snail Mail Follow-Up',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': """
    """,
    'depends': ['snailmail_account', 'account_followup'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_followup_data.xml',
        'views/account_followup_views.xml',
        'views/assets.xml',
        'wizard/followup_send_views.xml',
    ],
    'qweb': ['static/src/xml/account_followup_template.xml'],
    'auto_install': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
