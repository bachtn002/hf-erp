# -*- coding: utf-8 -*-
{
    'name': "Ev Helpdesk Api",

    'summary': """Ev Helpdesk Api""",

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'helpdesk', 'ev_config_connect_api'],

    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_ticket_log_views.xml',
    ],
}
