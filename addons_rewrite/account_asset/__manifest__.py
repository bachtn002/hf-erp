# -*- coding: utf-8 -*-

{
    'name': 'Assets Management',
    'description': """
    """,
    'category': 'Accounting/Accounting',
    'sequence': 32,
    'depends': ['account_reports'],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/asset_modify_views.xml',
        'wizard/asset_pause_views.xml',
        'wizard/asset_sell_views.xml',
        'views/account_account_views.xml',
        'views/account_asset_views.xml',
        'views/account_deferred_revenue.xml',
        'views/account_deferred_expense.xml',
        'views/account_move_views.xml',
        'views/account_asset_templates.xml',
        'report/account_assets_report_views.xml',
    ],
    'qweb': [
        "static/src/xml/account_asset_template.xml",
    ],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
    'auto_install': True,
}
