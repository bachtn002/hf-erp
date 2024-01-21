# -*- coding: utf-8 -*-

{
    'name': 'Helpdesk',
    'version': '1.3',
    'category': 'Services/Helpdesk',
    'sequence': 110,
    'summary': '',
    'depends': [
        'base_setup',
        'mail',
        'utm',
        'rating',
        'web_tour',
        'resource',
        'portal',
        'digest',
    ],
    'description': """
    """,
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/digest_data.xml',
        'data/mail_data.xml',
        'data/helpdesk_data.xml',
        'views/helpdesk_views.xml',
        'views/helpdesk_team_views.xml',
        'views/assets.xml',
        'views/digest_views.xml',
        'views/helpdesk_portal_templates.xml',
        'views/res_partner_views.xml',
        'views/mail_activity_views.xml',
        'report/helpdesk_sla_report_analysis_views.xml',
    ],
    'qweb': [
        "static/src/xml/helpdesk_team_templates.xml",
    ],
    'application': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
