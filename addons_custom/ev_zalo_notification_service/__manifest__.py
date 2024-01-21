# -*- coding: utf-8 -*-
{
    'name': "Zalo Notification Service OA",
    'summary': """
        Zalo Notification Service OA""",

    'description': """
        Zalo Notification Service OA
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Integration Zalo',
    'version': '0.1',
    'depends': ['base', 'point_of_sale', 'ev_pos_shop'],
    'data': [
        'data/ir_config_parameter.xml',
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'wizard/param_get_template.xml',
        'views/zalo_official_account_view.xml',
        'views/zalo_token_view.xml',
        'views/zns_template_view.xml',
        # 'views/zns_template_line_view.xml',
        'views/zns_information_view.xml',
        'views/type_send_zns.xml',
        'views/ip_send_zns.xml',
        'views/data_webhook_zns.xml',
        'views/zalo_email_template.xml',
        'views/delete_data_webhook_job.xml',
        # 'views/pos_shop.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
