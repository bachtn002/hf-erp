# -*- coding: utf-8 -*-
{
    'name': 'Helpdesk Custom v1',
    'version': '1.0',
    'sequence': 150,
    'summary': 'Helpdesk Custom v1',
    'description': """""",
    'category': 'Helpdesk',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'helpdesk', 'rating', 'portal', 'ev_helpdesk'],
    'data': [
        # security
        'security/ir.model.access.csv',
        # views
        'views/helpdesk_ticket_type_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/rating_template.xml',
        'views/ticket_template.xml',
        'views/question_rating_template.xml',
        'views/helpdesk_stage_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
