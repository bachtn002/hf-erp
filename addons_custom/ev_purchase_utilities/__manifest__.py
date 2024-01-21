# -*- coding: utf-8 -*-
{
    'name': "Purchase utilities",

    'summary': """
        Purchase utilities
        """,

    'description': """
        Purchase utilities
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','smarterp_read_excel','purchase_stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'wizard/view/wizard_import_purchase_order_line_view.xml',
        'views/stock_picking_type_view.xml'
    ],
}