# -*- coding: utf-8 -*-
{
    'name': "Stock Request",

    'summary': """
        Requirements and coordination of goods""",

    'description': """
    """,
    # TuUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'ev_stock_transfer', 'ev_stock_other', 'ev_pos_shop'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/ir_sequence_data.xml',
        'security/ir_rule.xml',
        'views/stock_request_go.xml',
        'views/stock_request_come.xml',
        'views/stock_request_coordinator.xml',
        'views/res_config_settings_view.xml',
        'views/stock_location.xml',
        'views/import_stock_request.xml',
        'views/stock_warehouse.xml'
        # 'report/internal_template.xml',
        # 'report/stock_outgoing_request_inherit.xml',
        # 'report/rpt_outgoing_request.xml',
    ],
}
