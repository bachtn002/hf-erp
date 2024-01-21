# -*- coding: utf-8 -*-
{
    'name': "Multi barcode",

    'summary': """Scan Multi Barcodes for the same Product""",

    'description': """""",

    'author': "SANGNT",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'point_of_sale'],

    # always loaded
    'data': [
        'views/assets.xml',

        'security/ir.model.access.csv',

        'views/product_barcode_views.xml',
        'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
