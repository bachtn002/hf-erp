# -*- coding: utf-8 -*-
{
    'name': "Pos Promotion Gift Code",

    'summary': """
      Tặng promotion code theo tổng giá trị đơn hàng
    """,

    'description': """
      Tặng promotion code theo tổng giá trị đơn hàng
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.com",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['base', 'web', 'ev_pos_promotion', 'ev_promotion_voucher', 'ev_pos_ConfirmPaymentPopup'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_promotion_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'qweb': [
        'static/src/xml/pos_gift_code_detail.xml',
        'static/src/xml/pos_order.xml',
        'static/src/xml/receipt.xml',
    ],
}
