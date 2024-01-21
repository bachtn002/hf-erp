# -*- coding: utf-8 -*-
{
    'name': 'E-Learning Custom',
    'version': '1.0',
    'sequence': 200,
    'summary': 'E-Learning Custom',
    'description': """""",
    'category': 'eLearning',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'survey', 'website_slides'],
    'data': [
        # security
        'security/ir.model.access.csv',
        #data
        'data/check_expired_certificated_cron.xml',
        'data/mail_notify_exp_template.xml',
        # views
        'views/assets.xml',
        'views/survey_survey_views.xml',
        'views/survey_user_input_views.xml',
        'views/slide_channel_views.xml',
        'views/slide_slide_views.xml',
        # 'views/survey_question_views.xml',
        'wizard/survey_invite_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
