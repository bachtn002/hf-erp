# -*- coding: utf-8 -*-
{
    'name': "Account SInvoice",

    'summary': """""",

    'description': """""",

    'author': "ERPVIET",
    'website': "https:/erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['point_of_sale', 'base', 'ev_pos_session_queue', 'ev_pos_refund', 'ev_payment_qrcode'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'views/pos_order_views.xml',
        'views/res_company_views.xml',
        'views/create_sinvoice_lot_views.xml',
        'views/account_sinvoice_views.xml',
        'views/pos_order_line_views.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/receipt.xml',
    ],
}
