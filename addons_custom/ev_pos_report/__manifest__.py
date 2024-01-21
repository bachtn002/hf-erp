# -*- coding: utf-8 -*-
{
    'name': "Pos report",

    'summary': """
        Point of sale report
        """,

    'description': """
        Point of sale report
    """,

    'author': "ERPVIET",
    'website': "https://erpviet.vn/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale', 'ev_pos_shop', 'ev_pos_channel'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/pos_order_report_security.xml',
        'views/views.xml',
        'views/rpt_pos_order_line_view.xml',
        'views/rpt_revenue_pos_payment_method_report_view.xml',
        'views/top_selling_products_view.xml',
        'views/report_pos_order.xml',
        'reports/report.xml',
    ],
}