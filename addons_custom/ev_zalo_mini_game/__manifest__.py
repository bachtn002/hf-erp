# -*- coding: utf-8 -*-

{
    'name': "Zalo Mini Game",
    'summary': """
        Zalo Mini Game""",

    'description': """
        Zalo Mini Game
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'ev_zalo_notification_service', 'ev_zalo_promotion', 'ev_pos_promotion_game_total_amount'],
    'data': [
        'data/ir_config_parameter.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
