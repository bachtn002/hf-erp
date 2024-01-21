# -*- coding: utf-8 -*-
{
    'name': "Stock Picking Custom",

    'summary': """Stock Picking Custom""",

    'description': """
    """,
    #TuUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'product', 'stock_account', 'ev_account_erpviet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_in.xml',
        'views/stock_picking_int.xml',
        'views/stock_picking_out.xml',
        'report/picking_in_report.xml',
        'report/picking_out_report.xml',
        'views/product.xml',
        'views/printing_stamp.xml',
        'views/stock_production_lot.xml',
        'views/stock_move.xml',
        'wizard/wizard_stock_print_stamp.xml',
        'wizard/wizard_print_stamp_product.xml',
        'views/stock_picking_action_custom.xml',
        'views/res_config_setting_view.xml',
        'report/bill_picking.xml',
        'report/picking_in_user_report.xml',
        'report/bill_transfer_report.xml',
        'report/bill_return_picking_report.xml',
    ],
}
