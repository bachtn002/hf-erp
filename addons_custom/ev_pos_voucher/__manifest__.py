# -*- coding: utf-8 -*-
{
    'name': "ERPVIET POS Voucher Management",
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'pos',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ev_product_release', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_method.xml',
        'views/pos_payment.xml',
        'views/voucher_cost_control_view.xml',
        # 'views/account_move.xml',
        'reports/report.xml',
    ],
}
