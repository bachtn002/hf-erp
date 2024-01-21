# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, exceptions, _
from datetime import datetime
from ...izi_report.models import excel_style
import base64
import xlsxwriter
from io import BytesIO


class RPTStockProductDetail(models.TransientModel):
    _name = 'rpt.stock.product.detail'

    def _default_from_date(self):
        todayDate = datetime.now()
        return todayDate.replace(day=1)

    name = fields.Char(string='Report Stock Product Detail', default='Sổ chi tiết Vật tư hàng hóa')
    product_ids = fields.Many2many('product.product', string='Product')
    branch_id = fields.Many2one('res.branch', string='Branch')
    from_date = fields.Date('From date', default=_default_from_date)
    to_date = fields.Date('To date', default=fields.Date.today())
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    detail_line = fields.One2many('rpt.stock.product.detail.line', 'rpt_detail_id', string='Details')

    def action_generate(self):
        self.env.cr.execute(
            f"""UPDATE rpt_stock_product_detail_line SET rpt_detail_id = NULL WHERE rpt_detail_id = {self.id}""")
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        query = f"""SELECT seq_num, product_id, move_id, date_accounting, date_document, 
                            move_note, price_unit, in_quantity, in_value, out_quantity, out_value, 
                            stock_quantity, stock_value, account_code, contra_account_code, partner_name
                    FROM (
                    -- 	sản phẩm
                        SELECT 2 seq_num, pp.id product_id, NULL move_id, NULL date_accounting, NULL date_document, 
                                NULL move_note, NULL price_unit,NULL partner_name,
                                SUM (CASE 
                                    WHEN aml.debit > 0 THEN ABS(ROUND(aml.quantity / uu.factor, 2))
                                    ELSE 0
                                    END) in_quantity, 
                                SUM(aml.debit) in_value, 
                                SUM (CASE 
                                    WHEN aml.credit > 0 THEN ABS(ROUND(aml.quantity / uu.factor, 2))
                                    ELSE 0
                                    END) out_quantity, 
                                SUM(aml.credit) out_value,
                                NULL stock_quantity,
                                NULL stock_value,
                                NULL account_code, NULL contra_account_code 
                        FROM product_product pp
                        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                        LEFT JOIN account_move_line aml ON pp.id = aml.product_id
                        LEFT JOIN uom_uom uu ON uu.id = aml.product_uom_id
                        WHERE aml.branch_id = {self.branch_id.id}
                        AND (aml.product_id = ANY(string_to_array('{product_ids}', ',')::integer[]) OR '{product_ids}' = '0')
                        AND aml.account_id IN (SELECT SPLIT_PART(value_reference, ',', 2)::INTEGER 
                                                FROM ir_property WHERE res_id = 'product.category,'||pc.id::TEXT 
                                                AND name = 'property_stock_valuation_account_id')
                        AND aml.date >= '{self.from_date}'
                        AND aml.date <= '{self.to_date}'
                        AND aml.company_id = {self.company_id.id}
                        GROUP BY pp.id
                        
                        UNION ALL
                    -- 	chi tiết
                        SELECT 3 seq_num, pp.id product_id, am.id move_id, aml.date date_accounting, 
                                aml.date date_document, aml.name move_note, 
                                ROUND(aml.balance * uu.factor / aml.quantity, 2) price_unit, rp.name partner_name,
                                (CASE
                                    WHEN aml.debit > 0 THEN ABS(ROUND(aml.quantity / uu.factor, 2))
                                    ELSE 0
                                    END) in_quantity, 
                                aml.debit in_value,
                                (CASE 
                                    WHEN aml.credit > 0 THEN ABS(ROUND(aml.quantity / uu.factor, 2))
                                    ELSE 0
                                    END) out_quantity, 
                                aml.credit out_value,
                                NULL stock_quantity,
                                NULL stock_value,
                                aa1.code account_code, aa2.code contra_account_code
                        FROM product_product pp
                        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                        LEFT JOIN account_move_line aml ON pp.id = aml.product_id
                        LEFT JOIN account_move am ON aml.move_id = am.id
                        LEFT JOIN account_account aa1 ON aa1.id = aml.account_id
                        LEFT JOIN account_account aa2 ON aa2.id = aml.contra_account_id
                        LEFT JOIN uom_uom uu ON uu.id = aml.product_uom_id
                        LEFT JOIN res_partner rp ON rp.id = aml.partner_id
                        WHERE aml.branch_id = {self.branch_id.id}
                        AND (aml.product_id = ANY(string_to_array('{product_ids}', ',')::integer[]) OR '{product_ids}' = '0')
                        AND aml.account_id IN (SELECT SPLIT_PART(value_reference, ',', 2)::INTEGER
                                                FROM ir_property 
                                                WHERE res_id = 'product.category,'||pc.id::TEXT 
                                                AND name = 'property_stock_valuation_account_id')
                        AND aml.date >= '{self.from_date}'
                        AND aml.date <= '{self.to_date}'
                        AND aml.company_id = {self.company_id.id}
                    ) as data
                    ORDER BY product_id, seq_num, date_accounting"""
        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()
        for item in data:
            product_tmpl_id = self.env['product.product'].sudo().browse(item['product_id']).product_tmpl_id
            if item['seq_num'] == 2:
                # tính toán đầu kỳ
                stock_quant, stock_value = self._cal_product_quant(date=self.from_date.strftime('%d/%m/%Y'),
                                                                   product_id=item['product_id'])
            else:
                # tính toán dư theo từng hóa đơn
                in_quantity = item['in_quantity'] if item['in_quantity'] else 0
                out_quantity = item['out_quantity'] if item['out_quantity'] else 0
                in_value = item['in_value'] if item['in_value'] else 0
                out_value = item['out_value'] if item['out_value'] else 0
                stock_quant = stock_quant + in_quantity - out_quantity
                stock_value = stock_value + in_value - out_value
            # Lấy ra tên đơn hàng
            order_name = ''
            if item['move_id']:
                order_name = self._generate_order_name(move_id=item['move_id'])
            val = (self.id, item['seq_num'], item['product_id'], item['move_id'], item['date_accounting'],
                   item['date_document'], item['move_note'], product_tmpl_id.uom_id.id, item['price_unit'],
                   item['in_quantity'], item['in_value'], item['out_quantity'], item['out_value'],
                   stock_quant, stock_value, item['account_code'], item['contra_account_code'], order_name,
                   item['partner_name'])
            self.env.cr.execute("""INSERT INTO rpt_stock_product_detail_line 
                                            (rpt_detail_id, seq_num, product_id, move_id, date_accounting, 
                                            date_document, move_note, uom_id, price_unit, in_quantity, 
                                            in_value, out_quantity, out_value, stock_quantity, stock_value, 
                                            account_code, contra_account_code, order_name, partner_name) 
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                val)

    def _cal_product_quant(self, date, product_id):
        """
            Calculate quant, value of product first period (with date)
        """
        query = f"""SELECT branch_id, SUM(xuatkho_standard_price) sum_export_value, SUM(xuatkho) sum_export, 
                            SUM(nhapkho_standard_price) sum_import_value, SUM(nhapkho) sum_import
                    FROM (
                        SELECT rb.id branch_id, sl.id location_id, pt.id product_id, 
                                SUM(abs(sml.x_value)) xuatkho_standard_price, SUM(sml.qty_done) xuatkho, 
                                0 nhapkho_standard_price, 0 nhapkho
                        FROM stock_move_line sml
                        LEFT JOIN stock_move sm ON sm.id = sml.move_id
                        LEFT JOIN product_product pp ON pp.id = sml.product_id
                        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        LEFT JOIN stock_location sl ON sl.id = sml.location_id
                        LEFT JOIN res_branch rb ON sl.branch_id = rb.id 
                        WHERE rb.id = {self.branch_id.id}
                        AND sml.company_id = {self.company_id.id}
                        AND sl.usage = 'internal'
                        AND sm.product_id = {product_id}
                        AND sm.state = 'done'
                        AND to_date(to_char(sml.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date('{date}','dd/mm/yyyy')
                        GROUP BY rb.id, sl.id, pt.id

                        UNION ALL

                        SELECT rb.id branch_id, sl.id location_id, pt.id product_id, 
                                0 xuatkho_standard_price, 0 xuatkho, SUM(abs(sml.x_value)) nhapkho_standard_price, 
                                SUM(sml.qty_done) nhapkho
                        FROM stock_move_line sml
                        LEFT JOIN stock_move sm ON sm.id = sml.move_id
                        LEFT JOIN product_product pp ON pp.id = sml.product_id
                        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        LEFT JOIN stock_location sl ON sl.id = sml.location_dest_id
                        LEFT JOIN res_branch rb ON sl.branch_id = rb.id 
                        WHERE rb.id = {self.branch_id.id}
                        AND sml.company_id = {self.company_id.id}
                        AND sl.usage = 'internal'
                        AND sm.product_id = {product_id}
                        AND sm.state = 'done'
                        AND to_date(to_char(sml.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date('{date}','dd/mm/yyyy')
                        GROUP BY rb.id, sl.id, pt.id
                    ) as data
                    GROUP BY branch_id"""
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        sum_export = sum_import = sum_export_value = sum_import_value = 0
        for item in data:
            sum_export = item['sum_export']
            sum_import = item['sum_import']
            sum_export_value = item['sum_export_value']
            sum_import_value = item['sum_import_value']
            break
        return sum_import - sum_export, sum_import_value - sum_export_value

    def _generate_order_name(self, move_id):
        self._cr.execute(f'''-- PO
                            SELECT a.name, d.id
                            FROM purchase_order a
                            LEFT JOIN purchase_order_line b on b.order_id = a.id
                            LEFT JOIN account_move_line c on c.purchase_line_id = b.id
                            LEFT JOIN account_move d on d.id = c.move_id
                            WHERE d.id = {move_id}
                            -- SO
                            UNION ALL
                            SELECT a.name, e.id
                            from sale_order a
                            LEFT JOIN sale_order_line b ON b.order_id = a.id
                            LEFT JOIN sale_order_line_invoice_rel c ON c.order_line_id = b.id
                            LEFT JOIN account_move_line d on d.id = c.invoice_line_id
                            LEFT JOIN account_move e on e.id = d.move_id
                            WHERE e.id = {move_id}
                            -- Bút toán kho
                            UNION ALL
                            SELECT a.name, d.id
                            FROM sale_order a
                            LEFT JOIN sale_order_line b ON b.order_id = a.id
                            LEFT JOIN stock_move c on c.sale_line_id = b.id
                            LEFT JOIN account_move d on d.stock_move_id = c.id
                            WHERE d.id = {move_id};''')
        data = self._cr.fetchall()
        if data:
            return data[0][0]
        return ''

    def action_export_excel(self):
        self.action_generate()
        self = self.sudo()
        file = BytesIO()
        wb = xlsxwriter.Workbook(file, {'in_memory': True})
        style_excel = excel_style.get_style(wb)
        wssheet = wb.add_worksheet('Sổ chi tiết Vật tư, Hàng hóa')
        wssheet.fit_to_pages(1, 0)
        first_row = self.add_header_report(wssheet, style_excel)
        self.write_row(wssheet, style_excel, first_row)
        namefile = u'Sổ chi tiết Vật tư, Hàng hóa.xlsx'
        wb.close()
        file.seek(0)
        out = base64.encodestring(file.getvalue())
        file.close()
        # Insert dữ liệu file vào bảng tạm
        code = 'BC_stock_product_detail'
        self._cr.execute('''DELETE FROM report_file''')
        self.env['report.file'].create({
            'code': code,
            'name': namefile,
            'value': out
        })
        self.invalidate_cache()
        return self.env['report.file']._download_file(namefile, code)

    def add_header_report(self, wssheet, style_excel):
        date_from = self.from_date.strftime('%d/%m/%Y')
        date_to = self.to_date.strftime('%d/%m/%Y')
        branch_name = self.branch_id.display_name
        # tencongty
        wssheet.merge_range(0, 0, 0, 0 + 18, self.company_id.name,
                            style_excel['style_12_bold_left'])
        wssheet.merge_range(1, 0, 1, 0 + 18, self.company_id.partner_id.street,
                            style_excel['style_12_bold_left'])
        row = 2
        col = 0
        # ten bc
        wssheet.merge_range(row, col, row, col + 18, 'SỔ CHI TIẾT VẬT TƯ HÀNG HÓA', style_excel['style_14_bold_center'])
        # từ ngày
        wssheet.write(row + 1, col + 8, 'Từ ngày: ', style_excel['style_11_right'])
        wssheet.merge_range(row + 1, col + 9, row + 1, col + 11, date_from, style_excel['style_11_left'])
        # đến ngày
        wssheet.write(row + 2, col + 8, 'Đến ngày: ', style_excel['style_11_right'])
        wssheet.merge_range(row + 2, col + 9, row + 2, col + 11, date_to, style_excel['style_11_left'])
        wssheet.write(row + 3, col + 8, 'Bộ phận', style_excel['style_11_right'])
        wssheet.merge_range(row + 3, col + 9, row + 3, col + 11, branch_name, style_excel['style_11_left'])

        # table
        wssheet.merge_range(row + 4, col, row + 5, col, 'Mã cũ', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 1, row + 5, col + 1, 'Mã mới', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 2, row + 5, col + 2, 'Sản phẩm', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 3, row + 5, col + 3, 'Đơn hàng', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 4, row + 5, col + 4, 'Đối tác', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 5, row + 5, col + 5, 'Ngày hoạch toán',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 6, row + 5, col + 6, 'Ngày chứng từ',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 7, row + 5, col + 7, 'Số chứng từ',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 8, row + 5, col + 8, 'Diễn giải', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 9, row + 5, col + 9, 'ĐVT', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 10, row + 5, col + 10, 'Đơn giá', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 11, row + 4, col + 12, 'Nhập', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 13, row + 4, col + 14, 'Xuất', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 15, row + 4, col + 16, 'Tồn', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 17, row + 5, col + 17, 'TK Kho', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 18, row + 5, col + 18, 'TK Đối ứng',
                            style_excel['style_12_bold_center_border'])

        wssheet.write(row + 5, col + 11, 'Số lượng', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 12, 'Giá trị', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 13, 'Số lượng', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 14, 'Giá trị', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 15, 'Số lượng', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 16, 'Giá trị', style_excel['style_12_bold_center_border'])

        return row + 6

    def write_row(self, wssheet, style_excel, row):
        data = self._get_data_report()
        col = 0
        # chinh do rong
        wssheet.set_column(0, 0, width=15)  # old_code
        wssheet.set_column(1, 1, width=10)  # default_code
        wssheet.set_column(2, 2, width=15)  # product
        wssheet.set_column(3, 3, width=15)  # order
        wssheet.set_column(4, 4, width=20)  # partner
        wssheet.set_column(5, 5, width=10)  # date_accounting
        wssheet.set_column(6, 6, width=10)  # date_document
        wssheet.set_column(7, 7, width=15)  # mote_id
        wssheet.set_column(8, 8, width=15)  # move_note
        wssheet.set_column(9, 9, width=10)  # uom
        wssheet.set_column(10, 10, width=10)  # price_unit
        wssheet.set_column(11, 11, width=14)  # in_quant
        wssheet.set_column(12, 12, width=14)  # in_value
        wssheet.set_column(13, 13, width=14)  # out_quant
        wssheet.set_column(14, 14, width=14)  # out_value
        wssheet.set_column(15, 15, width=10)  # stock_quant
        wssheet.set_column(16, 16, width=10)  # stock_value
        wssheet.set_column(17, 17, width=10)  # account
        wssheet.set_column(18, 18, width=10)  # contra_account
        # do du lieu
        stt = 1
        style_12_left = style_excel['style_12_left_data']
        style_12_left_data_red = style_excel['style_12_left_data_red']
        style_12_center = style_excel['style_12_center_data']
        style_12_center_data_red = style_excel['style_12_center_data_red']
        style_12_right_data_number_bold = style_excel['style_12_right_data_number_bold']
        style_12_right_number = style_excel['style_12_right_data_number']
        for item in data:
            wssheet.write(row, col + 3, item['order_name'], style_12_left)
            wssheet.write(row, col + 4, item['partner_name'], style_12_left)
            wssheet.write(row, col + 5, item['date_accounting'].strftime('%d/%m/%Y') if item['date_accounting'] else '',
                          style_12_center)
            wssheet.write(row, col + 6, item['date_document'].strftime('%d/%m/%Y') if item['date_document'] else '',
                          style_12_center)
            wssheet.write(row, col + 7, item['move_name'], style_12_left)
            wssheet.write(row, col + 8, item['move_note'], style_12_left)
            wssheet.write(row, col + 9, item['uom_name'], style_12_left)
            wssheet.write(row, col + 10, item['price_unit'], style_12_right_number)
            if item['seq_num'] == 2:
                wssheet.write(row, col, item['x_old_code'], style_12_left_data_red)
                wssheet.write(row, col + 1, item['default_code'], style_12_center_data_red)
                wssheet.write(row, col + 2, item['product_name'], style_12_left_data_red)
                wssheet.write(row, col + 11, item['in_quantity'], style_12_right_data_number_bold)
                wssheet.write(row, col + 12, item['in_value'], style_12_right_data_number_bold)
                wssheet.write(row, col + 13, item['out_quantity'], style_12_right_data_number_bold)
                wssheet.write(row, col + 14, item['out_value'], style_12_right_data_number_bold)
                wssheet.write(row, col + 15, item['stock_quantity'], style_12_right_data_number_bold)
                wssheet.write(row, col + 16, item['stock_value'], style_12_right_data_number_bold)
            else:
                wssheet.write(row, col, item['x_old_code'], style_12_left)
                wssheet.write(row, col + 1, item['default_code'], style_12_center)
                wssheet.write(row, col + 2, item['product_name'], style_12_left)
                wssheet.write(row, col + 11, item['in_quantity'], style_12_right_number)
                wssheet.write(row, col + 12, item['in_value'], style_12_right_number)
                wssheet.write(row, col + 13, item['out_quantity'], style_12_right_number)
                wssheet.write(row, col + 14, item['out_value'], style_12_right_number)
                wssheet.write(row, col + 15, item['stock_quantity'], style_12_right_number)
                wssheet.write(row, col + 16, item['stock_value'], style_12_right_number)
            wssheet.write(row, col + 17, item['account_code'], style_12_center)
            wssheet.write(row, col + 18, item['contra_account_code'], style_12_center)

            row += 1
            stt += 1

    def _get_data_report(self):
        self.env.cr.execute(f'''SELECT rspdl.*, pt.x_old_code, pt.default_code, uu.name uom_name, am.name move_name,
                                        pt.name product_name, order_name, partner_name
                                FROM rpt_stock_product_detail_line rspdl
                                LEFT JOIN rpt_stock_product_detail rspd on rspd.id = rspdl.rpt_detail_id
                                LEFT JOIN res_branch rb on rb.id = rspd.branch_id
                                LEFT JOIN product_product pp on pp.id = rspdl.product_id
                                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                                LEFT JOIN uom_uom uu on uu.id = rspdl.uom_id
                                LEFT JOIN account_move am ON am.id = rspdl.move_id
                                WHERE rspd.id = {self.id}
                                ORDER BY id, product_id, seq_num, date_accounting''')
        return self.env.cr.dictfetchall()


class RPTStockProductDetailLine(models.TransientModel):
    _name = 'rpt.stock.product.detail.line'

    seq_num = fields.Integer(string='Sequence Number')
    product_id = fields.Many2one('product.product', string='Product')
    move_id = fields.Many2one('account.move', string='Move')
    date_accounting = fields.Date(string='Date Accounting')
    date_document = fields.Date(string='Date Document')
    move_note = fields.Char(string='Move Note')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    price_unit = fields.Float(string='Price Unit', digits='Price Other')
    in_quantity = fields.Float(string='In Quantity', digits='Product Unit of Measure')
    in_value = fields.Float(string='In Value', digits='Price Other')
    out_quantity = fields.Float(string='Out Quantity', digits='Product Unit of Measure')
    out_value = fields.Float(string='Out Value', digits='Price Other')
    stock_quantity = fields.Float(string='Stock Quantity', digits='Product Unit of Measure')
    stock_value = fields.Float(string='Stock Value', digits='Price Other')
    account_code = fields.Char(string='Account Code')
    contra_account_code = fields.Char(string='Contra Account Code')
    rpt_detail_id = fields.Many2one(string='Report Id')
    order_name = fields.Char('Name Order')
    partner_name = fields.Char('Partner Name')
