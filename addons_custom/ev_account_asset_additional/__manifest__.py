# -*- coding: utf-8 -*-
{
    'name': "Account Asset Additional Custom",
    'summary': """
        - Account Asset Additional Custom
        """,
    'description': """
        """,
    
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['base','ev_account_asset','report_xlsx'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_asset_inventory_view.xml',
        'report/report_xlsx.xml',
        # 'views/account_asset_inventory_add_line_view.xml',
        
    ],

}
