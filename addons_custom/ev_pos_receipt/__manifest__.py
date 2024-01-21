# -*- coding: utf-8 -*-
{
    'name': "POS receipt",

    'summary': """
        Custom receipt in POS""",

    'description': """
        inherit 'XmlReceipt' and add some content and field
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'POS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale', 'base', 'ev_pos_shop'],

    # always loaded
    'data': [
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
        'static/src/xml/receipt.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
