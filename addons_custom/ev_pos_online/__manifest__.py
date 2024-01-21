# -*- coding: utf-8 -*-
{
    'name': "POS Online",
    'summary': """
        Module limits customer data when downloading and allows loading data online
        """,
    'description': """
        Module limits customer data when downloading and allows loading data online
    """,
    'author': "IZISolution",
    'website': "http://www.izisolution.vn",
    'category': 'Point of Sale',
    'version': '0.1',
    'depends': ['point_of_sale'],
    'qweb': [
        'static/src/xml/*.xml',
    ],

    # always loaded
    'data': [
        'views/views.xml',
        'views/pos_assets.xml',
    ],
}
