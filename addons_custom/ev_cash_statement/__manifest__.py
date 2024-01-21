# -*- coding: utf-8 -*-
{
    'name': 'Cash statement',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Odoo 14 cash statement',
    'description': """""",
    'category': 'Tutorials',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale', 'report_xlsx','ev_pos_shop'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cash_statement_input.xml',
        'views/pos_session.xml',
        'views/cash_statement.xml',
        'reports/reports.xml',
        'reports/print_cash_statement_pdf.xml',
        'views/pos_shop_view.xml'
    ],
    'demo': [],
    'qweb': [],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': False,
}
