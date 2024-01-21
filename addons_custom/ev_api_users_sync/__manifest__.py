# -*- coding: utf-8 -*-
{
    'name': 'Api Users Sync',
    'version': '1.0',
    'sequence': 150,
    'summary': 'Api Users Sync',
    'description': """""",
    'category': 'Api Users Sync',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/ir_cron_data.xml',
        'data/ir_config_parameter.xml',
        # views
        'views/log_user_api_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': [''],
    'installable': True,
    'auto_install': False,
}
