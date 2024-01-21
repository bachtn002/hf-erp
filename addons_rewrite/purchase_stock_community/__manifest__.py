# -*- coding: utf-8 -*-

{
    'name': "Purchase Stock Community",
    'version': "1.0",
    'category': "Inventory/Purchase",
    'summary': "Customized Dashboard for Purchase Stock",
    'description': "",
    'depends': ['purchase_community', 'purchase_stock'],
    'data': [
        'report/purchase_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
