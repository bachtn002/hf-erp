# -*- coding: utf-8 -*-


{
    'name': 'Import CSV Bank Statement',
    'category': 'Accounting/Accounting',
    'version': '1.0',
    'description': '''
''',
    'depends': ['account_bank_statement_import', 'base_import'],
    'data': [
        'wizard/account_bank_statement_import_views.xml',
        'views/account_bank_statement_import_templates.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
