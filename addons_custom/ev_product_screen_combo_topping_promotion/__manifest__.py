# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Product Order Screen Combo-Topping-Promotions",

    'summary': """
        Customize Product Screen in Order View For Combo Topping Promotions
    """,

    'description': """
      Customize Product Screen in Order View For Combo Topping Promotions
    """,
    # TuUH
    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['point_of_sale', 'ev_pos_promotion', 'ev_pos_combo', 'ev_product_order_screen'],

    'data': [
    ],

    'qweb': [
        'static/src/xml/Screens/ProductScreen/*.xml',
    ]
}
