# -*- coding: utf-8 -*-


{
    'name': 'Mail Mobile',
    'version': '1.1',
    'category': 'Hidden/Tools',
    'summary': '',
    'description': """
    """,
    'depends': [
        'iap_mail',
        'mail_community',
        'web_mobile',
        'base_setup',
    ],
    'data': [
        'data/mail_mobile_data.xml',
        'views/ocn_assets.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': ['web_mobile', 'mail_community'],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
