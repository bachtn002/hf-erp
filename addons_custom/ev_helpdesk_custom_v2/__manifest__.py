# -*- coding: utf-8 -*-
{
    'name': "Ev Helpdesk Custom V2",

    'summary': """
        """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'ev_helpdesk', 'helpdesk'],

    'data': [
        'security/ir.model.access.csv',
        'security/helpdesk_security.xml',
        'views/res_users.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_ticket_template_views.xml',
        'views/helpdesk_stage_views.xml',
        'views/ticket_templates.xml',
    ],
    'qweb': [
        'static/src/xml/helpdesk_team_templates.xml',
    ]
}
