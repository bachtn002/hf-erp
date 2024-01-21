# -*- coding: utf-8 -*-
{
    'name': 'Group Sale Requset',
    'version': '1.0',
    'sequence': 20,
    'summary': 'Odoo 14 Group Sale Request',
    'description': """""",
    'category': 'Tutorials',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/genaral_product_group_imp.xml',
        'wizard/general_warehouse_group_imp.xml',
        'wizard/supply_product_group_imp.xml',
        'wizard/supply_warehouse_group_imp.xml',
        'views/general_product_group.xml',
        'views/general_warehouse_group.xml',
        'views/supply_product_group.xml',
        'views/supply_warehouse_group.xml',
        'views/order_schedule_from_stock_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'images': [''],
    'installable': True,
    'auto_install': False,
}
