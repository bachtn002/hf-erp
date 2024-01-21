# -*- coding: utf-8 -*-
{
    'name': "Asset Transfer",

    'summary': """
    Asset Transfer
        """,

    'description': """
        Asset Transfer
    """,

    'author': "IZISolution",
    'website': "https://www.izisolution.vn",
    'category': 'Assets',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/asset_transfer_views.xml',
        'data/ir_sequence_data.xml',
    ],
}
