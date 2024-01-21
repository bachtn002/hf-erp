# -*- coding: utf-8 -*-
{
    'name': "EV Pos Refund Job Approve",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Pos Refund',
    'version': '0.1',
    'depends': ['base', 'ev_pos_refund'],
    'data': [
        'views/pos_order_refund.xml',
        'data/auto_approve_refund_job.xml',
    ],
}
