# -*- coding: utf-8 -*-
{
    'name': "FIX Data Webhook ZNS",
    'summary': """
        FIX Data Webhook ZNS Check Request many times""",

    'description': """
        FIX Data Webhook ZNS Check Request many times
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'ev_zalo_notification_service'],
    'data': [
        'views/data_webhook_zns_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
