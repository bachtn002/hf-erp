# -*- coding: utf-8 -*-
{
    'name': "Stock General Data Monthly",

    'summary': """
        Stock General Data Monthly and Turning Stock Report""",

    'description': """
        Stock General Data Monthly and Turning Stock Report Inventory, Stock Report In Out
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'Stock',
    'version': '0.1',

    'depends': ['base', 'mail', 'stock', 'report_xlsx', 'ev_inventory_check'],

    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'security/stock_sync_monthly_security.xml',
        'views/stock_general_monthly.xml',
        'views/stock_sync_monthly.xml',
        'wizard/stock_inventory_report_view.xml',
        'reports/stock_in_out_report_view.xml',
        'reports/stock_inventory_detail_report_view.xml',
        'reports/reports.xml',
        'views/menu_views.xml',

    ],
}
