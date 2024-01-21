# -*- coding: utf-8 -*-
{
    'name': "Connection Slave",

    'summary': """
        Connection Slave
        """,

    'description': """
        Connection Slave
    """,

    'author': "IZISolution",
    'website': "https://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
}
