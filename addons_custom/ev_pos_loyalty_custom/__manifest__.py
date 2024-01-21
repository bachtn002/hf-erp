# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Loyalty Custom HF",

    'summary': """
      Custom when use pos ERP Pos loyalty
    """,

    'description': """
      Custom pos ui when use pos ERP Pos loyalty
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.com",

    'category': 'Point Of Sale',
    'version': '0.1',

    'depends': ['base', 'point_of_sale', 'pos_loyalty'],

    'data': [
        'views/assets.xml',
        'views/LoyaltyRewardCustom.xml',
        'views/res_partner.xml',
        'views/menu_pos_loyalty_custom.xml'
    ],

    'qweb': [
        'static/src/xml/button/ButtonLoyaltyCustom.xml',
        'static/src/xml/button/PopupLoyaltyCustom.xml',
        'static/src/xml/edit_list_input_custom.xml',
    ],
}
