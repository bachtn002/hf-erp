# -*- coding: utf-8 -*-
{
    'name': "Pos Session Entries",

    'summary': """
        The module allows you to replay the entire session closing entry
        """,

    'description': """
        The module allows you to replay the entire session closing entry
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
}
