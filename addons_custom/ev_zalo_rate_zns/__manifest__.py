# -*- coding: utf-8 -*-

{
    'name': "Rate zns",
    'summary': """
        Rate zns management""",

    'description': """
        Rate zns management
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'ev_zalo_notification_service'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/param_rate_zns.xml',
        'views/ir_cron.xml',
        'views/rate_zns.xml',
        'views/zns_template.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
