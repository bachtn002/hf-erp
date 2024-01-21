from datetime import datetime
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import odoo.tools as tools
import os


class StockTransferReport(models.TransientModel):
    _name = 'stock.transfer.report'
    _description = 'Bao cao ton kho trung chuyen'

    name = fields.Char('Name')
    warehouse_id = fields.Char('Warehouse Id')
    warehouse_dest_id = fields.Char('Warehouse Dest Id')
    default_code = fields.Char('Default Code')
    product_name = fields.Char('Product Name')
    uom = fields.Char('Uom')
    out_quantity = fields.Char('Out Quantity')
    execution_time = fields.Char('Execution Time')
    name_partner = fields.Char('Name Partner')
    report_id = fields.Char('Report ID')


class StockTransferReportWizard(models.TransientModel):
    _name = 'report.stock.transfer.report.wizard'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Báo cáo tồn kho trung chuyển'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    user_id = fields.Many2one('res.user', string='user', default=lambda self: self.env.user)

    def open_table_report(self):
        self.ensure_one()
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = self.from_date
        if self.from_date > self.to_date:
            raise UserError(_('Start date must be less than end date'))
        warehouse_ids = ','.join([str(idd) for idd in self.warehouse_ids.ids]) if self.warehouse_ids else '0'
        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'

        sql = """
        delete from stock_transfer_report;
        insert into stock_transfer_report( name, warehouse_id, warehouse_dest_id, default_code, product_name, uom, out_quantity
                                 , execution_time
                                 , name_partner, report_id, create_date, write_date, create_uid, write_uid)

        select st.name                            name,
               swi.name                           warehouse_id,
               swdi.name                          warehouse_dest_id,
               pp.default_code,
               pt.name                            product_name,
               uom.name                           uom,
               stl.out_quantity,
               to_char(st.out_date, 'dd/mm/yyyy') date,
               rp.name                            name_partner,
               %s                                 report_id,
               now(),
               now(),
               %d, %d
        from stock_transfer st
                 left join stock_transfer_line stl on st.id = stl.stock_transfer_id
                 left join stock_warehouse swi on st.warehouse_id = swi.id
                 left join stock_warehouse swdi on st.warehouse_dest_id = swdi.id
                 left join uom_uom uom on stl.product_uom = uom.id
                 left join product_product pp on stl.product_id = pp.id
                 left join product_template pt on pp.product_tmpl_id = pt.id
                 left join res_users ru on st.create_uid = ru.id
                 left join res_partner rp on ru.partner_id = rp.id
        where st.state = 'transfer'
          AND stl.out_quantity > 0
          AND (swdi.id = ANY (string_to_array('%s', ',')::integer[]) OR '%s' = '0')
          AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd/mm/yyyy')
          AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd/mm/yyyy')
        order by st.out_date
        """
        self.env.cr.execute(
            sql % (report_id, self.env.user.id, self.env.user.id, warehouse_ids, warehouse_ids, from_date, to_date))
        self.env.cr.commit()
        return {
            'name': _('Stock Transfer Report Action'),
            'view_mode': 'tree',
            'res_model': 'stock.transfer.report',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }

    def action_print_excel(self):
        if self.from_date > self.to_date:
            raise UserError(_('Start date must be less than end date'))
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/xlsx/stock.transfer.report.wizard/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def generate_xlsx_report(self, workbook, data, record):
        ws = workbook.add_worksheet("Report")
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            'font': 'Arial',
            'num_format': 'dd/mm/yyyy'
        })
        cell_format = workbook.add_format({
            'bold': 0,
            'border': 1,
            'font_size': 12,
            'font': 'Arial',
            'valign': 'vcenter',
        })
        cell_format_stt = workbook.add_format({
            'bold': 0,
            'border': 1,
            'font_size': 12,
            'font': 'Arial',
            'align': 'center',
            'valign': 'vcenter',
        })
        cwd = os.getcwd()
        direct_logo = str(cwd) + '\\birt_erpviet\\logo.jpg'
        ws.merge_range('A1:C4', '', merge_format)
        ws.merge_range('D1:H1', 'Công ty Cổ phần Quốc tế Homefarm', merge_format)
        ws.merge_range('D3:H3', 'BÁO CÁO PHIẾU ĐIỀU CHUYỂN CHƯA XỬ LÝ', merge_format)
        ws.merge_range('D4:H4', 'Từ ngày:' + record.from_date.strftime("%d/%m/%Y") + ' Đến ngày: ' + record.to_date.strftime("%d/%m/%Y"), merge_format)
        ws.merge_range('I1:J4', 'Mã hiệu')
        ws.merge_range('D2:H2',
                       'Địa chỉ: Số 282 Phố Hoàng Văn Thái - Phường Khương Trung - Quận Thanh Xuân - TP Hà Nội - Việt Nam',
                       merge_format)
        ws.set_column(0, 0, 20)
        ws.set_column(1, 1, 20)
        ws.set_column(2, 2, 20)
        ws.set_column(3, 3, 30)
        ws.set_column(4, 4, 30)
        ws.set_column(5, 5, 30)
        ws.set_column(6, 6, 30)
        ws.set_column(7, 7, 30)
        ws.set_column(8, 8, 30)
        ws.set_column(9, 9, 30)
        ws.set_row(0, 30)
        ws.set_row(1, 30)
        ws.set_row(2, 30)
        ws.set_row(3, 30)
        ws.set_row(4, 30)
        ws.write(4, 0, u'STT', merge_format)
        ws.write(4, 1, u'Mã phiếu', merge_format)
        ws.write(4, 2, u'Kho nguồn', merge_format)
        ws.write(4, 3, u'Kho đích', merge_format)
        ws.write(4, 4, u'Mã hàng', merge_format)
        ws.write(4, 5, u'Tên hàng', merge_format)
        ws.write(4, 6, u'Đơn vị tính', merge_format)
        ws.write(4, 7, u'Số lượng', merge_format)
        ws.write(4, 8, u'Thời gian thực hiện', merge_format)
        ws.write(4, 9, u'Người tạo', merge_format)
        result = record.get_data()
        index = 5
        stt = 0
        for item in result:
            ws.write(index, 0, stt + 1, cell_format_stt)
            ws.write(index, 1, item.get('name'), cell_format)
            ws.write(index, 2, item.get('warehouse_id'), cell_format)
            ws.write(index, 3, item.get('warehouse_dest_id'), cell_format)
            ws.write(index, 4, item.get('default_code'), cell_format)
            ws.write(index, 5, item.get('product_name'), cell_format)
            ws.write(index, 6, item.get('uom'), cell_format)
            ws.write(index, 7, item.get('out_quantity'), cell_format)
            ws.write(index, 8, item.get('date'), cell_format)
            ws.write(index, 9, item.get('name_partner'), cell_format)

            index += 1
            stt += 1

    def get_data(self):
        self.ensure_one()
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = self.from_date
        if self.from_date > self.to_date:
            raise UserError(_('Start date must be less than end date'))
        warehouse_ids = ','.join([str(idd) for idd in self.warehouse_ids.ids]) if self.warehouse_ids else '0'
        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'
        sql = """
                select st.name                            name,
                       swi.name                           warehouse_id,
                       swdi.name                          warehouse_dest_id,
                       pp.default_code,
                       pt.name                            product_name,
                       uom.name                           uom,
                       stl.out_quantity,
                       to_char(st.out_date, 'dd/mm/yyyy') date,
                       rp.name                            name_partner,
                       %s                                 report_id,
                       now(),
                       now(),
                       %d, %d
                from stock_transfer st
                         left join stock_transfer_line stl on st.id = stl.stock_transfer_id
                         left join stock_warehouse swi on st.warehouse_id = swi.id
                         left join stock_warehouse swdi on st.warehouse_dest_id = swdi.id
                         left join uom_uom uom on stl.product_uom = uom.id
                         left join product_product pp on stl.product_id = pp.id
                         left join product_template pt on pp.product_tmpl_id = pt.id
                         left join res_users ru on st.create_uid = ru.id
                         left join res_partner rp on ru.partner_id = rp.id
                where st.state = 'transfer'
                  AND stl.out_quantity > 0
                  AND (swdi.id = ANY (string_to_array('%s', ',')::integer[]) OR '%s' = '0')
                  AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd/mm/yyyy')
                  AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd/mm/yyyy')
                order by st.out_date
                """
        self._cr.execute(
            sql % (report_id, self.env.user.id, self.env.user.id, warehouse_ids, warehouse_ids, from_date, to_date))
        query_res = self._cr.dictfetchall()
        return query_res
