# -*- coding: utf-8 -*-
{
    'name': "Pos Promotion Gift Code Product Qty",

    'summary': """
      Tặng promotion code theo điều kiện sản phẩm và số lượng mua
    """,

    'description': """
      Tặng promotion code theo điều kiện sản phẩm và số lượng mua
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.com",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['ev_pos_promotion_gift_code'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_promotion_views.xml',
    ],
    'qweb': [],
}
