# -*- coding: utf-8 -*-
{
    'name': "Account Asset Custom",
    'summary': """
        - Account Asset Custom
        """,
    'description': """
        """,
    # tuuh
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['base', 'account_asset', 'account_reports'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/account_asset.xml',
        # 'views/rpt_account_asset.xml',
        'views/account_asset_inventory_view.xml',
        'views/account_asset_report.xml',
    ],
}
