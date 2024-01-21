# -*- coding: utf-8 -*-
{
    'name': "Data Warehouse",

    'summary': """
        Adjust warehouse data""",

    'description': """
        Adjust warehouse data
    """,

    'author': "ERPVIET",
    'website': "https://erpviet.vn/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'views/data_warehouse_view.xml',
        'views/check_data_daily.xml',
        'security/ir.model.access.csv'
    ]
}