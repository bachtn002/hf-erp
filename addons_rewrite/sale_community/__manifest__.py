# -*- coding: utf-8 -*-
{
    'name': "Sale Community",
    'version': "1.0",
    'category': "Sales/Sales",
    'summary': "Advanced Features for Sale Management",
    'description': """
Contains advanced features for sale management
    """,
    'depends': ['sale', 'web_dashboard'],
    'data': [
        'report/sale_report_views.xml',
        'views/sale_enterprise_templates.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': ['sale'],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
