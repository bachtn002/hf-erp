# -*- coding: utf-8 -*-
{
    'name': "Print Stamp Product",

    'summary': """
        Print Stamp Product
    """,

    'description': """
      Print Stamp Product
    """,
    # TuUH
    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    'category': 'Product Qweb',
    'version': '0.1',

    'depends': ['base', 'product','stock','point_of_sale','ev_pos_promotion_qty_price'],

    'data': [
        'security/ir.model.access.csv',
        'security/print_stamp_security.xml',
        'views/product_template.xml',
        'views/print_stamp_shelf_view.xml',
        'views/print_stamp_product_view.xml',
        'views/print_stamp_promotion_view.xml',
        'views/product_promotion_config_view.xml',
        'views/product_other_config_view.xml',
        'views/pos_promotion_qty_price_view.xml',
        'views/res_company_view.xml',
        'views/import_xls_other_config_view.xml',
        'report/report_print_stamp_shelf.xml',
        'report/report_print_stamp_product.xml',
        'report/report_print_stamp_promotion.xml',
        'report/report_print_stamp_shelf_product.xml',
    ],

    'qweb': [
    ]
}
