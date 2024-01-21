# -*- coding: utf-8 -*-
{
    'name': "Import Asset",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Import Asset',
    'version': '0.1',
    'depends': ['base', 'ev_account_erpviet', 'account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_asset_line_imp.xml',
        'views/import_asset.xml',
    ],
    'qweb': [

    ],
}
