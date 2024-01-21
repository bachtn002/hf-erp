# -*- coding: utf-8 -*-
{
    'name': "Stock Card",

    'summary': """
        Stock Card""",

    'description': """
        Stock Card
    """,
    # tuuh
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_card_view.xml',
        'report/report_template.xml',
        'report/report_stock_card_xls.xml',
    ],

}
