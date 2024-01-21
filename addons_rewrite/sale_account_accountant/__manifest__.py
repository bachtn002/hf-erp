# -*- coding: utf-8 -*-


{
    'name': "Sale Accounting",
    'version': "1.0",
    'category': "Sales/Sales",
    'summary': "",
    'description': """
    """,
    'depends': ['sale', 'account_accountant'],
    'data': [
        'views/sale_account_accountant_templates.xml',
    ],
    'qweb': [
        "static/src/xml/account_reconciliation.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
