# -*- coding: utf-8 -*-
{
    'name': "Ev Payment QRCode",

    'summary': """Ev Payment QRCode""",

    'description': """
        Module tích hợp thanh toán QRCode
    """,

    'author': "ERPVIET",
    'website': "www.erpviet.vn",
    'category': 'Point of Sale',
    'version': '0.1',

    'depends': ['ev_pos_shop', 'ev_config_connect_api', 'pos_loyalty'],

    'data': [
        'security/ir.model.access.csv',
        'security/view_transaction_security.xml',
        'views/assets.xml',
        'views/pos_payment_method_views.xml',
        'views/callback_payment_log_views.xml',
        # 'views/payment_qrcode_transaction_views.xml',
        'views/pos_shop_views.xml',
        'views/payment_qrcode_transaction_new_views.xml',
        'views/pos_order_views.xml',
        'views/payment_create_order_qrcode_res_views.xml',
        'data/ir_config_parameter.xml',
    ],
    'qweb': [
        'static/src/xml/qrcode_popup.xml',
    ]
}
