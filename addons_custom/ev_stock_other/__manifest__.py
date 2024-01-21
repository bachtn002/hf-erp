# -*- coding: utf-8 -*-
{
    'name': "ERPViet Stock Other",
    'summary': """
        All feature goods receipt and goods issues others in stock.
        """,
    'description': """
        The module is used to goods receipt and goods issues others.
    """,
    'author': "ERPViet",
    'website': "https://www.erpviet.vn",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['base', 'stock', 'account', 'stock_account', 'account_accountant', 'ev_stock_picking_cancel',
                'ev_stock_edit_date_done', 'ev_stock_picking','ev_stock_custom'],
    'data': [
        'data/data.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        'report/stock_other_report.xml'
    ],
}