# -*- coding: utf-8 -*-
{
    'name': "Res Notify",

    'summary': """
    """,
    # TuUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_notification_viber.xml',
        'views/res_notification_web.xml',
    ],
}
