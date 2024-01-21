# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
from datetime import datetime, timedelta
from odoo.osv import osv
from odoo.exceptions import except_orm
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
import base64
import xlwt
import xlrd
import sys
from collections import OrderedDict


class PosReport(models.TransientModel):
    _inherit = 'pos.order.report'
    
    def action_print(self):
        if len(self.order_line_lines) < 1:
            self.action_filter_all()
        wb = xlwt.Workbook(encoding="UTF-8")
        date_str = str(datetime.today().date())
        ws = wb.add_sheet(date_str)
        editable = xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin;")
        read_only = xlwt.easyxf("")
        header_style = xlwt.easyxf("pattern: pattern solid, fore_color black; align: HORZ CENTER, VERT CENTER;font: height 280,color white;\
                                                                                    borders: left thin, right thin, top thin,top_color white, bottom_color white, right_color white, left_color white; pattern: pattern solid;")
        ws.col(0).width = 10 * 500
        ws.col(1).width = 10 * 500
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 367
        ws.col(4).width = 10 * 367
        ws.col(5).width = 10 * 1000
        ws.col(6).width = 10 * 500
        ws.col(7).width = 10 * 250
        ws.col(8).width = 10 * 250
        ws.col(9).width = 10 * 367
        ws.col(10).width = 10 * 367
        ws.col(11).width = 10 * 367
        ws.col(12).width = 10 * 367
        ws.col(13).width = 10 * 367
        ws.col(14).width = 10 * 500
        ws.col(15).width = 10 * 500
        ws.write(0, 0, u'Đơn hàng')
        ws.write(0, 1, u'Ngày mua hàng')
        ws.write(0, 2, u'Khách hàng')
        ws.write(0, 3, u"SĐT")
        ws.write(0, 4, u"Mã SP")
        ws.write(0, 5, u"Sản Phẩm")
        ws.write(0, 6, u"SL")
        ws.write(0, 7, u"Đơn giá")
        ws.write(0, 8, u"Thành tiền")
        ws.write(0, 9, u"Tổng Chiết khấu)")
        ws.write(0, 10, u"Thực thu")
        ws.write(0, 11, u"Cửa hàng")
        ws.write(0, 12, u"Nhân viên")
        ws.write(0, 13, u"Ghi chú")
        style_content = xlwt.easyxf("align: horiz left, vert top")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        index = 1
        for line in self.order_line_lines:
            if line:
                ws.write(index, 0, line.order_id.name, editable)
                ws.write(index, 1,
                         datetime.strftime(datetime.strptime(line.order_id.date_order, "%Y-%m-%d %H:%M:%S").date(),
                                           '%d-%m-%Y %a'), editable)
                ws.write(index, 2, line.customer_id.name, editable)
                ws.write(index, 3, line.customer_id.phone, editable)
                ws.write(index, 4, line.product_id.default_code, editable)
                ws.write(index, 5, line.product_id.name, editable)
                ws.write(index, 6, line.quantity, editable)
                ws.write(index, 7, line.price_unit, style)
                ws.write(index, 8, abs(line.price_unit * line.quantity) if line.product_id.product_tmpl_id.type != 'service' else 0,style)
                ws.write(index, 9, line.discount, style)
                ws.write(index, 10, line.amount_total, style)
                ws.write(index, 11, line.order_id.session_id.config_id.name, editable)
                ws.write(index, 12, line.order_id.user_id.name, editable)
                ws.write(index, 13, line.order_id.note, editable)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': date_str + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'BC Ban Le ' + self.pos_config_id.name + date_str + '.xls',
            'type': 'binary',
            'res_model': 'pos.order.report',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

    def action_print_order(self):
        if len(self.order_line_lines) < 1:
            self.action_filter_all()
        wb = xlwt.Workbook(encoding="UTF-8")
        date_str = str(datetime.today().date())
        ws = wb.add_sheet(date_str)
        editable = xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin;")
        read_only = xlwt.easyxf("")
        header_style = xlwt.easyxf("pattern: pattern solid, fore_color black; align: HORZ CENTER, VERT CENTER;font: height 280,color white;\
                                                                            borders: left thin, right thin, top thin,top_color white, bottom_color white, right_color white, left_color white; pattern: pattern solid;")
        ws.col(0).width = 10 * 500
        ws.col(1).width = 10 * 500
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 367
        ws.col(4).width = 10 * 367
        ws.col(5).width = 10 * 500
        ws.col(6).width = 10 * 500
        ws.col(7).width = 10 * 367
        ws.col(8).width = 10 * 367
        ws.col(9).width = 10 * 367
        ws.write(0, 0, u'Đơn hàng')
        ws.write(0, 1, u'Ngày mua hàng')
        ws.write(0, 2, u'Khách hàng')
        ws.write(0, 3, u"SĐT")
        ws.write(0, 4, u"Tổng tiền")
        ws.write(0, 5, u"Cửa hàng")
        ws.write(0, 6, u"Nhân viên")
        ws.write(0, 7, u"Ghi chú")
        ws.write(0, 8, u"Phương thức thanh toán")
        ws.write(0, 9, u"Số tiền")
        style_content = xlwt.easyxf("align: horiz left, vert top")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        index = 1
        for line in self.order_lines:
            if line:
                ws.write(index, 0, line.order_id.name, editable)
                ws.write(index, 1,
                         datetime.strftime(datetime.strptime(line.order_id.date_order, "%Y-%m-%d %H:%M:%S").date(),
                                           '%d-%m-%Y %a'), editable)
                ws.write(index, 2, line.customer_id.name, editable)
                ws.write(index, 3, line.customer_id.phone, editable)
                ws.write(index, 4, line.amount_total, style)
                ws.write(index, 5, line.order_id.session_id.config_id.name, editable)
                ws.write(index, 6, line.order_id.user_id.name, editable)
                ws.write(index, 7, line.order_id.note, editable)
                ws.write(index, 8, line.journal_id.name, editable)
                ws.write(index, 9, line.amount_payment, style)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': date_str + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'BC Ban Le ' + self.pos_config_id.name + date_str + '.xls',
            'type': 'binary',
            'res_model': 'pos.order.report',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

    def action_print_product(self):
        if len(self.order_line_lines) < 1:
            self.action_filter_all()
        wb = xlwt.Workbook(encoding="UTF-8")
        date_str = str(datetime.today().date())
        ws = wb.add_sheet(date_str)
        editable = xlwt.easyxf("borders: left thin, right thin, top thin, bottom thin;")
        read_only = xlwt.easyxf("")
        header_style = xlwt.easyxf("pattern: pattern solid, fore_color black; align: HORZ CENTER, VERT CENTER;font: height 280,color white;\
                                                                                borders: left thin, right thin, top thin,top_color white, bottom_color white, right_color white, left_color white; pattern: pattern solid;")
        ws.col(0).width = 10 * 500
        ws.col(1).width = 10 * 500
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 367
        ws.col(4).width = 10 * 367
        ws.col(5).width = 10 * 500
        ws.col(6).width = 10 * 500
        ws.write(0, 0, u'Nhóm SP')
        ws.write(0, 1, u'Sản Phẩm')
        ws.write(0, 2, u'Số lượng')
        ws.write(0, 3, u'Đơn giá')
        ws.write(0, 4, u"Tổng tiền")
        ws.write(0, 5, u"Cửa hàng")
        ws.write(0, 6, u"Cửa hàng")
        style_content = xlwt.easyxf("align: horiz left, vert top")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        index = 1
        for line in self.product_lines:
            if line:
                ws.write(index, 0, line.category_id.name, editable)
                ws.write(index, 1, line.product_id, editable)
                ws.write(index, 2, line.quantity, editable)
                ws.write(index, 3, line.price_unit, editable)
                ws.write(index, 4, line.amount_total, style)
                ws.write(index, 5, line.sale_staff.name, editable)
                ws.write(index, 6, line.order_id.session_id.config_id.name, editable)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': date_str + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'BC Ban Le ' + self.pos_config_id.name + date_str + '.xls',
            'type': 'binary',
            'res_model': 'pos.order.report',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }