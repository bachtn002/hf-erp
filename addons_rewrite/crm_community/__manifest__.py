# -*- coding: utf-8 -*-
{
    'name': "CRM Community",
    'version': "1.0",
    'category': "Sales/CRM",
    'summary': "Advanced features for CRM",
    'description': """
Contains advanced features for CRM such as new views
    """,
    'depends': ['crm', 'web_dashboard', 'web_cohort', 'web_map'],
    'data': [
        'views/crm_lead_views.xml',
        'views/assets.xml',
        'report/crm_activity_report_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': ['crm'],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
