# -*- coding: utf-8 -*-

{
    'name': "Zalo Notification Service OA V2",
    'summary': """
        Zalo Notification Service OA V2""",

    'description': """
        Zalo Notification Service OA V2
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'point_of_sale', 'ev_pos_shop', 'ev_zalo_notification_service'],
    'data': [
        'views/pos_shop.xml',
        'views/zalo_official_account_view.xml',
        'views/zalo_token_view.xml',
        'views/zns_template_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
