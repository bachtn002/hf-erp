# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Product Screen List",

    'summary': """
        Customize Product Screen in List View
    """,

    'description': """
      Customize Product Screen in List View
    """,
    # TuUH
    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['point_of_sale'],

    'data': [
        'views/assets.xml',
        'views/pos_config.xml',
    ],

    'qweb': [
        'static/src/xml/Screens/ProductScreen/*.xml'
    ]
}
