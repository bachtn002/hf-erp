# -*- coding: utf-8 -*-

{
    'name': 'Account Invoice Extract',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': '',
    'depends': ['account', 'iap', 'mail_community'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_invoice_extract_data.xml',
        'data/config_parameter_endpoint.xml',
        'data/extraction_status.xml',
        'data/res_config_settings_views.xml',
        'data/update_status_cron.xml',
    ],
    'auto_install': True,
    'qweb': [
        'static/src/bugfix/bugfix.xml',
        'static/src/xml/invoice_extract_box.xml',
        'static/src/xml/invoice_extract_button.xml',
    ],
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}
