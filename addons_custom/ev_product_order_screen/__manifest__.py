# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Product Order Screen",

    'summary': """
        Customize Product Screen in Order View
    """,

    'description': """
      Customize Product Screen in Order View
    """,
    # TuUH
    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['point_of_sale'],

    'data': [
        'views/assets.xml'
    ],

    'qweb': [
        'static/src/xml/Screens/ProductScreen/OrderLine.xml',
    ]
}
