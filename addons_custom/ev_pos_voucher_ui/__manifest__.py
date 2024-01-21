# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Voucher UI",
    'description': """
        """,
    # DangNT
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['base', 'point_of_sale', 'ev_pos_voucher'],
    'data': [
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/Sale/*.xml',
        'static/src/xml/Payment/*.xml',
        'static/src/xml/back_payment.xml'
    ],
}
