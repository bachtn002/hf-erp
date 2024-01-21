# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Loyalty Point",

    'summary': """
      CTKM tặng điểm tích lũy thành viên
    """,

    'description': """
      Quản lý các chương trình khuyến mãi type=loyalty_point
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.com",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['ev_pos_promotion', 'ev_promotion_phone_release', 'ev_pos_loyalty_ui_hf', 'ev_pos_loyalty_channel'],

    'data': [
        'data/api_check_barcode_partner_data.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_promotion.xml',
        'views/pos_order_views.xml',
    ],

    'qweb': [
        'static/src/xml/PointsCounter.xml',
        'static/src/xml/ProductScreenCustomer.xml',
    ],
}