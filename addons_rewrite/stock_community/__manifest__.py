# -*- coding: utf-8 -*-
{
    'name': "Stock Community",
    'version': "1.0",
    'category': 'Inventory/Inventory',
    'summary': "Advanced features for Stock",
    'description': """
    """,
    'depends': ['stock', 'web_dashboard', 'web_cohort', 'web_map', 'web_grid'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'views/stock_picking_map_views.xml',
        'views/stock_enterprise_templates.xml',
        'report/stock_report_views.xml',
        'report/report_stock_quantity.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': ['stock'],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
