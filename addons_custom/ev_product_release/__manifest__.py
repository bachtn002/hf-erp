# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Product Release",
    'description': """
        """,
    # DangNT
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['base', 'product', 'product_expiry', 'sale', 'account', 'purchase','ev_pos_erpviet', 'ev_account_erpviet'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'wizard/update_product_release.xml',
        'views/res_company.xml',
        'views/product_release.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/stock_picking_type.xml',
        'views/stock_production_lot_rule.xml',
    ],
}
