# -*- coding: utf-8 -*-


{
    'name': "Stock Package Custom",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ERPViet",
    'website': "https://www.erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'stock_barcode', 'ev_stock_transfer', 'ev_multi_barcode'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/barcode_package_data.xml',
        # security
        'security/stock_package_security.xml',
        'security/ir.model.access.csv',
        # views
        'views/stock_barcode_views.xml',
        'views/product_template.xml',
        'views/assets.xml',
        'views/stock_package_transfer_view.xml',
        'views/stock_package_report_view.xml',
        'report/stamp_package_report.xml',
        'report/bill_transfer_in_out_report.xml',
        'views/stock_transfer.xml',
        'views/stock_package_transfer_line_view.xml',
        #wizard
        'wizard/stock_transfer_wizard_view.xml'
    ],
    'qweb': [
        'static/src/xml/package_transfer_barcode_template.xml',
        'static/src/xml/scan_package_template.xml',
        'static/src/xml/scan_stock_transfer.xml',
        'static/src/xml/stock_barcode.xml',
        'static/src/xml/popup_templates.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    # 'application': True,
}
