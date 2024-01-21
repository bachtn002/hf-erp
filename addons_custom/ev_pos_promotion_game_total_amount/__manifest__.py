# -*- coding: utf-8 -*-
{
    'name': "Pos Promotion Discount Condition",

    'summary': """
      Tích lượt chơi dựa trên tổng giá trị đơn hàng
    """,

    'description': """
      Tích lượt chơi dựa trên tổng giá trị đơn hàng
    """,

    'author': "SangNT",
    'website': "http://www.izisolution.com",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['ev_pos_promotion', 'ev_pos_refund'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/res_partner_views.xml',
        'views/pos_order_views.xml',
        'views/pos_promotion_views.xml',
    ],
    'qweb': [
        'static/src/xml/pos_game_detail.xml',
        'static/src/xml/pos_order.xml',
    ],
}
