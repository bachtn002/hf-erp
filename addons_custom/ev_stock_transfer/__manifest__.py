# -*- coding: utf-8 -*-
{
    'name': "Stock transfer",

    'summary': """
        Stock transfer warehouse
        """,

    'description': """
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'ev_stock_access_right', 'stock_barcode', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/stock_transfer_from_view.xml',
        'views/stock_transfer_to_view.xml',
        'report/stock_report.xml',
        'views/confirm_date_tmp_view.xml',
        'views/stock_location_view.xml',
        'report/report.xml',
        'report/stock_transfer_report.xml',
        'report/stock_transfer_to_report.xml',
        'report/bill_transfer_in_report.xml',
        'report/bill_transfer_out_report.xml',
        'report/stock_transfer_from_report.xml',
    ],
}
