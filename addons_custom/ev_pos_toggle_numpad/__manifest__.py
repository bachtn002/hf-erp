# -*- coding: utf-8 -*-
{
        'name': "ERPVIET Toggle numpad 1",

    'summary': """
        Show button allow toogle numpad in pos ui
    """,

    'description': """# ERPVIET Toggle numpad

    This module allow you can add button to toogle numpad on pos ui
    And show configs allow you can hide any button of numpad on pos ui
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    'category': 'Tools',
    'version': '0.1',

    'depends': ['ev_pos_display'],

    'data': [
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/Widgets/ToggleNumpadButton.xml',
        'static/src/xml/Widgets/ToggleCategoryButton.xml',
        'static/src/xml/Widgets/ToggleControlButton.xml',
        'static/src/xml/Screens/ProductScreen.xml',
    ]
}
