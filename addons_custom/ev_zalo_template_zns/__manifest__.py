# -*- coding: utf-8 -*-
{
    'name': "Template ZNS Config",
    'summary': """
        Template ZNS Config""",

    'description': """
       Auto map parameters template zns send zns
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'ev_zalo_notification_service'],
    'data': [
        'security/ir.model.access.csv',
        'views/map_zns_config.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
