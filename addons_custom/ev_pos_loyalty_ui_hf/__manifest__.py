# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Loyalty For PosUI Homefarm",

    'summary': """
      Custom pos ui when use pos ERP Pos loyalty
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
    ],

    'qweb': [
        'static/src/xml/PointsCounter.xml',
        'static/src/xml/Loyalty.xml',
        'static/src/xml/Screens/ProductScreen.xml',
    ],
}
