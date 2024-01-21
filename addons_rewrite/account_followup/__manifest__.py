# -*- coding: utf-8 -*-


{
    'name': 'Payment Follow-up Management',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'description': """
""",
    'depends': ['account', 'mail', 'sms', 'account_reports'],
    'data': [
        'security/account_followup_security.xml',
        'security/ir.model.access.csv',
        'security/sms_security.xml',
        'data/account_followup_data.xml',
        'data/cron.xml',
        'views/account_followup_views.xml',
        'views/partner_view.xml',
        'views/report_followup.xml',
        'views/account_journal_dashboard_view.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/account_followup_template.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
