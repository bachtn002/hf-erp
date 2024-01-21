# -*- coding: utf-8 -*-
{
    'name': 'API FAST',
    'version': '1.0',
    'category': 'API FAST',
    'summary': """
        """,
    'description': """
    """,
    'author': "SangNT",
    'website': 'https://www.erpviet.vn',
    'depends': ['ev_config_connect_api', 'ev_promotion_phone_release'],
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/sync_game_turn_views.xml',
        'views/sync_update_phone_code_views.xml',
    ],

    'css': [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
