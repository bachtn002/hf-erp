
# -*- coding: utf-8 -*-
{
    'name': "Supply Request",

    'summary': """
        Process purchase requests from stock""",

    'description': """
    """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'ev_stock_request', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/sequence.xml',
        # 'wizard/allotment_supply_imp.xml',
        # 'wizard/supply_product_group_imp.xml',
        # 'wizard/supply_warehouse_group_imp.xml',
        'views/supply_request_view.xml',
        # 'views/supply_product_group.xml',
        # 'views/supply_warehouse_group.xml',
        'views/report_xlsx.xml',
        'views/product_supplierinfo.xml',
        #'views/purchase_order_line.xml',
        'views/purchase_quotation_templates.xml',
        # 'views/allotment_supply.xml',
    ],
}
