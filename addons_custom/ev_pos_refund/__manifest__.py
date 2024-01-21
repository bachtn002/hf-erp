# -*- coding: utf-8 -*-
{
    'name': "Pos Refund",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Pos Refund',
    'version': '0.1',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'security/point_of_sale_security.xml',
        'wizard/write_reason_refuse.xml',
        'views/pos_order_refund.xml',
        'reports/print_order_pdf.xml',
        'views/res_company_views.xml',
    ],
}
