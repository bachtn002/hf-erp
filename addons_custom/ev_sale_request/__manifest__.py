# -*- coding: utf-8 -*-
{
    'name': 'Sale Request ',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Odoo 14 yêu cầu hàng bán',
    'description': """""",
    'category': 'Tutorials',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'stock',
        'report_xlsx',
        'ev_general_request'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule_sale_request.xml',
        'data/sequence.xml',
        'views/sale_request.xml',
        'views/import_xls_stock.xml',
        'report/sale_request_report.xml',
        'views/product_inherit_add_supply.xml',
        'views/resconfig_inherit.xml',
        'views/suppy_adjustment.xml',
        'views/menu_view.xml',
        # 'views/warehouse_supply.xml',

    ],
    'demo': [],
    'qweb': [],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': True,
}
