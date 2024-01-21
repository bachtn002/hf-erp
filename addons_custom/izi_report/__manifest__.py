# -*- coding: utf-8 -*-
{
    'name': "Report Config",
    'summary': """
            - Export excel configuration!
            """,
    # Tiendz
    'author': "ERPViet",
    'website': "http://www.izisolution.vn",
    'category': 'report',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/decimal_precision.xml',
        # 'views/report_sql.xml',
    ],
}