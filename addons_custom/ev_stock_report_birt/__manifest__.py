# -*- coding: utf-8 -*-
{
    'name': "Stock Report Birt",

    'summary': """
        Stock Report Birt""",
    'description': """
    """,
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'stock',
    'version': '0.1',
    'depends': ['base', 'stock', 'stock_enterprise', 'account_reports', 'izi_report', 'widget_enter', 'account'],
    'data': [
        # 'views/stock_config.xml',
        'security/ir.model.access.csv',
        'report/report.xml',
        'views/menu_stock_report.xml',
        'views/rpt_stock_move.xml',
        'views/rpt_stock_document.xml',
        # 'views/rpt_stock_move_multi_location.xml',
        # 'views/rpt_stock_product_detail.xml',
        'views/stock_inventory_by_product_view.xml',
        'views/rpt_stock_transfer.xml',
        'views/rpt_cash_statement.xml',
        'views/stock_quant_current.xml',
    ],
}
