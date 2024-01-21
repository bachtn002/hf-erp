# -*- coding: utf-8 -*-
{
    'name': "Ev Pos Channel",

    'summary': """Ev Pos Channel""",

    'description': """
        Module kênh bán hàng trên POS
    """,

    'author': "ERPVIET",
    'website': "www.erpviet.vn",
    'category': 'Point of Sale',
    'version': '0.1',

    'depends': ['base', 'point_of_sale', 'ev_promotion_voucher_custom', 'ev_pos_display', 'ev_pos_promotion', 'ev_google_maps'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pos_channel_assets_common.xml',
        'views/pos_channel_views.xml',
        'views/pos_payment_method_views.xml',
        'views/pos_order_views.xml',
        'views/pos_promotion_views.xml',
        'views/sale_online_views.xml',
    ],
    'qweb': [
        'static/src/xml/PaymentScreen.xml',
        'static/src/xml/ActionPadWidget.xml',
    ]
}
