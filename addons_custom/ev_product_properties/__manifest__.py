# -*- coding: utf-8 -*-
{
    'name': "Product Properties",

    'summary': """Product Properties""",

    'description': """
    Add Properties in Product
    """,
    # TuUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        'views/product_product_view.xml',
        # 'views/product_template.xml'
    ],
}
