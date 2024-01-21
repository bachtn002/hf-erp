# -*- coding: utf-8 -*-
{
    'name': 'Helpdesk',
    'version': '1.0',
    'sequence': 150,
    'summary': 'Helpdesk',
    'description': """""",
    'category': 'Helpdesk',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'helpdesk', 'rating', 'portal'],
    'data': [
        # data
        'data/email_template.xml',
        'data/helpdesk_data.xml',
        # security
        'security/helpdesk_groups.xml',
        'security/helpdesk_rules.xml',
        'security/ir.model.access.csv',
        # views
        'views/asset.xml',
        'views/helpdesk_department.xml',
        'views/helpdesk_stage_views.xml',
        'views/question_view.xml',
        'views/answer_views.xml',
        'views/app_support_view.xml',
        'views/helpdesk_view.xml',
        'views/res_users.xml',
        'views/res_config_settings_views.xml',
        'views/home_ticket_portal.xml',
        # Portal
        'views/ticket_templates.xml',
        'views/question_rating_template.xml',
        'views/ticket_submit_template.xml',
        # Wizard
        'wizard/wizard_download_template_view.xml'
    ],
    'demo': [],
    'qweb': [
        'static/src/xml/portal_chatter.xml',
    ],
    'images': [''],
    'installable': True,
    'auto_install': False,
}
