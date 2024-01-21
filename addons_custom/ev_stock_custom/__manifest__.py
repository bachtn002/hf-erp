# -*- coding: utf-8 -*-
{
    'name': "Stock Custom",

    'summary': """Stock Custom""",

    'description': """
    """,
    # TuUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_menu.xml',
        'views/stock_region.xml',
        'views/stock_location.xml',
        'views/stock_warehouse.xml',
        'views/res_company.xml',
        'views/stock_rule_form.xml',
    ],
}
