# -*- coding: utf-8 -*-
{
    'name': "ev_zalo_sale_online",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ev_zalo_notification_service', 'ev_sale_online' , 'ev_delivery_management' , 'ev_zalo_template_zns'],

    # always loaded
    'data': [
        'data/ir_config_parameter.xml',
        'views/zns_template_views.xml',
    ],
}
