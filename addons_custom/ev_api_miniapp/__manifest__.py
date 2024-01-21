# -*- coding: utf-8 -*-
{
    'name': "Ev Api MiniApp",

    'summary': """
        Ev Api MiniApp""",

    'description': """
        - API trả thông tin danh mục DVT
        - API trả thông tin CTKM
        - API tạo đơn online
        - API hủy đơn online
        - API Trả thông tin điểm loyalty (API truy vấn từng khách)
        - API Trả thông tin lịch sử điểm (API truy vấn theo từng khách và phân trang dữ liệu)
        - API Trả thông tin code ưu đãi cho từng khách (Voucher, Promotion Code)
        - API Trả thông tin tồn kho theo kho, theo sản phẩm có phân trang dữ liệu
        - Cập nhập trạng thái vận đơn - [PROCESSING, COMPLETED, REFUNDED]
    """,

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'ev_delivery_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/sync_state_miniapp_views.xml',
    ],
}
