# -*- coding: utf-8 -*-
{
    'name': "Delivery Management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'point_of_sale', 'stock',
                'ev_pos_shop', 'ev_stock_transfer',
                'ev_stock_request', 'ev_return_product_warehouse'],

    # always loaded
    'data': [
        'data/ir_config_parameter.xml',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'security/ir_security.xml',
        'views/assets.xml',
        'views/delivery_management_view.xml',
        'views/stock_transfer.xml',
        'views/stock_request.xml',
        'views/res_config_setting.xml',
        'views/delivery_partner.xml',
        'views/webhook_grab.xml',
        'views/webhook_aha.xml',
    ],
    'qweb': [
        'static/src/xml/button_get_delivery.xml',
        'static/src/xml/delivery_package_popup.xml',
        'static/src/xml/edlit_list_input_package.xml',
    ],

}
