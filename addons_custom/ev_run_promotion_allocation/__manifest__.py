# -*- coding: utf-8 -*-
{
    'name': "Run Promotion Allocation",

    'summary': """
        Run Promotion Allocation""",

    'description': """
        Run Promotion Allocation
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
}
