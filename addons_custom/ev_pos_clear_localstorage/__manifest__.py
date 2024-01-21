# -*- coding: utf-8 -*-
{
    'name': "Clear LocalStorage",

    'summary': """
        Clear LocalStorage for POS""",

    'description': """
        Since Pos using localstorage to store all data in browse, It's won't be deleted when browse is close,
        So we need to clear all cache before new pos session is started
    """,

    'author': "SangNT",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['point_of_sale'],

    'data': [
        'views/templates.xml',

    ],
}
