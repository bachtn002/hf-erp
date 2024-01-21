# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Next Screen After Print",
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'pos',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        'views/assets.xml',
        # 'views/required_phone_res_partner_views.xml',
        'views/set_price_with_payment_method_view.xml',
        'views/date_of_birth_res_partner_view.xml'
    ],
    'qweb': [
        'static/src/xml/remove_edit.xml'
    ],
}
