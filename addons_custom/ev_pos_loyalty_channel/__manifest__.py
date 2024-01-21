# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Loyalty Channel",

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

    'depends': ['base', 'ev_pos_channel', 'ev_pos_loyalty_custom'],

    'data': [
        'views/assets.xml',
        'views/loyalty_program.xml',
    ],

    'qweb': [],
}
