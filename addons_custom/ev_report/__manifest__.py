# -*- coding: utf-8 -*-
{
    'name': "EV Report",
    'summary': """Module báo cáo base""",
    'description': """Module báo cáo base""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Reports',
    'version': '6.0.0.8',
    'license': 'AGPL-3',
    'depends': ['ev_file_download'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_style_data.xml',
        'views/menus.xml',
        'views/assets.xml',
        'views/report_style_views.xml',
        'views/report_template_views.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ]
}
