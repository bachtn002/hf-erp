# -*- coding: utf-8 -*-
{
    'name': "Pos Session Queue",

    'summary': """
    Pos Session Queue
        """,

    'description': """
        Pos Session Queue
    """,

    'author': "ERPVIET",
    'website': "https://www.izisolution.vn",
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','queue_job'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/pos_config_views.xml',
    ],
}
