# -*- coding: utf-8 -*-
{
    'name': 'Check Inventory',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Stock Inventory Custom',
    'description': """Stock Inventory add state, add account analytic""",
    'category': 'Stock',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'stock','analytic','stock_account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_check.xml',
        'views/inventory_group.xml',
        'reports/print_inventory_pdf.xml',
        'reports/print_inventory_draft_pdf.xml',
        'views/report_xlsx.xml'
    ],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': True,
}
