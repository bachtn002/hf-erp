# -*- coding: utf-8 -*-
{
    'name': "Connection API",

    'summary': """
        Connection API
        """,

    'description': """
        Connection API
    """,

    'author': "IZISolution",
    'website': "https://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/config_connection.xml',
        'views/config_api.xml',
        'views/log_api.xml',
        'views/ip_connection.xml',
    ],
}