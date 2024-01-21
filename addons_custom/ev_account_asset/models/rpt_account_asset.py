# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from datetime import datetime
from ...izi_report.models import excel_style
import base64
import xlsxwriter
from io import BytesIO


class RPTAccountAsset(models.TransientModel):
    _name = 'rpt.account.asset'

    date_to = fields.Date('To date', default=fields.Date.today())
    asset_type = fields.Selection([('assets', 'Assets'), ('tools', 'Tools'), ('expense', 'Expense')], 'Asset Type',
                                  default='assets')
    account_asset_line = fields.One2many('rpt.account.asset.line', 'rpt_account_asset_id', 'Account Asset Line')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    name = fields.Char(default='Bảng tính phân bổ Tài sản, CCDC, Chi phí trả trước')
    branch_ids = fields.Many2many('res.branch', string="Branches")

    def action_report_excel(self):
        self.action_generate()
        self = self.sudo()
        file = BytesIO()
        wb = xlsxwriter.Workbook(file, {'in_memory': True})
        style_excel = excel_style.get_style(wb)
        wssheet = wb.add_worksheet('Bảng tính phân bổ Tài sản, CCDC, Chi phí trả trước')
        wssheet.fit_to_pages(1, 0)
        first_row = self.add_header_report(wssheet, style_excel)
        self.write_row(wssheet, style_excel, first_row)
        namefile = u'Bảng tính phân bổ Tài sản, CCDC, Chi phí trả trước.xlsx'
        wb.close()
        file.seek(0)
        out = base64.encodestring(file.getvalue())
        file.close()
        # Insert dữ liệu file vào bảng tạm
        code = 'BC_account_asset'
        self._cr.execute('''DELETE FROM report_file''')
        self.env['report.file'].create({
            'code': code,
            'name': namefile,
            'value': out
        })
        self.invalidate_cache()
        return self.env['report.file']._download_file(namefile, code)

    def add_header_report(self, wssheet, style_excel):
        if self.asset_type == 'assets':
            asset_type = 'Tài sản'
        elif self.asset_type == 'tools':
            asset_type = 'Công cụ dụng cụ'
        else:
            asset_type = 'Chi phí trả trước'
        date_to = self.date_to.strftime('%d/%m/%Y')
        branch_ids = ','.join([f'[{idd.display_name}]' for idd in self.branch_ids.ids]) if self.branch_ids else ''
        # tencongty
        wssheet.merge_range(0, 0, 0, 0 + 11, self.company_id.name,
                            style_excel['style_12_bold_left'])
        wssheet.merge_range(1, 0, 1, 0 + 11, self.company_id.partner_id.street,
                            style_excel['style_12_bold_left'])
        row = 2
        col = 0
        # ten bc
        wssheet.merge_range(row, col, row, col + 11, 'BẢNG TÍNH PHÂN BỔ TÀI SẢN, CCDC, CHI PHÍ TRẢ TRƯỚC',
                            style_excel['style_14_bold_center'])
        # từ ngày
        wssheet.write(row + 1, col + 6, 'Loại tài sản: ', style_excel['style_11_right'])
        wssheet.write(row + 1, col + 7, asset_type, style_excel['style_11_left'])
        # đến ngày
        wssheet.write(row + 2, col + 6, 'Đến ngày: ', style_excel['style_11_right'])
        wssheet.write(row + 2, col + 7, date_to, style_excel['style_11_left'])
        # chi nhánh
        wssheet.write(row + 3, col + 6, 'Chi nhánh: ', style_excel['style_11_right'])
        wssheet.write(row + 3, col + 7, branch_ids, style_excel['style_11_left'])
        # table
        wssheet.merge_range(row + 4, col, row + 5, col, 'STT', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 1, row + 5, col + 1, 'Tên CCDC', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 2, row + 5, col + 2, 'ĐVT', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 3, row + 5, col + 3, 'Số lượng còn lại',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 4, row + 5, col + 4, 'Số kỳ phân bổ',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 5, row + 5, col + 5, 'Số kỳ phân bổ còn lại',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 6, row + 4, col + 8, 'Phân bổ trong kỳ',
                            style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 6, 'Đối tượng phân bổ', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 7, 'TK Chi phí', style_excel['style_12_bold_center_border'])
        wssheet.write(row + 5, col + 8, 'Số tiền', style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 9, row + 5, col + 9, 'Lũy kế đã PB',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 10, row + 5, col + 10, 'Giá trị còn lại',
                            style_excel['style_12_bold_center_border'])
        wssheet.merge_range(row + 4, col + 11, row + 5, col + 11, 'TK chờ phân bổ',
                            style_excel['style_12_bold_center_border'])

        return row + 6

    def write_row(self, wssheet, style_excel, row):
        # data = self.account_asset_line
        col = 0
        # chinh do rong
        wssheet.set_column(0, 0, width=5)  # stt
        wssheet.set_column(1, 1, width=25)  # asset_name
        wssheet.set_column(2, 2, width=10)  # uom
        wssheet.set_column(3, 3, width=10)  # số lượng còn lại
        wssheet.set_column(4, 4, width=15)  # num_posted
        wssheet.set_column(5, 5, width=15)  # num_un_post
        wssheet.set_column(6, 6, width=15)  # account_depreciation
        wssheet.set_column(7, 7, width=14)  # account_depreciation_expense
        wssheet.set_column(8, 8, width=20)  # original_value
        wssheet.set_column(9, 9, width=14)  # lũy kế đã PB
        wssheet.set_column(10, 10, width=20)  # value_residual
        wssheet.set_column(11, 11, width=14)  # TK chờ PB
        # do du lieu
        stt = 1
        style_12_left = style_excel['style_12_left_data']
        style_12_center = style_excel['style_12_center_data']
        style_12_right_data_number_bold = style_excel['style_12_right_data_number_bold']
        style_12_right_number = style_excel['style_12_right_data_number']
        total_original_value = total_value_residual = 0
        for item in self.account_asset_line:
            total_original_value += item.original_value
            total_value_residual += item.value_residual
            wssheet.write(row, col, stt, style_12_center)
            wssheet.write(row, col + 1, item.account_asset_id.name, style_12_left)
            wssheet.write(row, col + 2, '', style_12_center)
            wssheet.write(row, col + 3, '', style_12_center)
            wssheet.write(row, col + 4, item.num_posted, style_12_center)
            wssheet.write(row, col + 5, item.num_un_post, style_12_center)
            wssheet.write(row, col + 6, item.account_depreciation, style_12_center)
            wssheet.write(row, col + 7, item.account_depreciation_expense, style_12_center)
            wssheet.write(row, col + 8, item.original_value, style_12_right_number)
            wssheet.write(row, col + 9, '', style_12_center)
            wssheet.write(row, col + 10, item.value_residual, style_12_right_number)
            wssheet.write(row, col + 11, '', style_12_center)
            row += 1
            stt += 1

        wssheet.write(row, col + 8, total_original_value, style_12_right_data_number_bold)
        wssheet.write(row, col + 10, total_value_residual, style_12_right_data_number_bold)

    # @api.onchange('date_from', 'date_to', 'asset_type', 'company_id')
    def action_generate(self):
        self.account_asset_line = None
        date_to = self.date_to.strftime('%d/%m/%Y')
        branch_ids = ','.join([str(idd) for idd in self.branch_ids.ids]) if self.branch_ids else ','.join(
            [str(idd) for idd in self.env.user.branch_ids.ids])
        condition = f"""WHERE aas.first_depreciation_date <= to_date('{date_to}','dd/mm/yyyy')
                    """
        x_asset_type = self.asset_type
        if x_asset_type == 'expense':
            asset_type = 'expense'
            condition += f"""AND aas.x_asset_type IS NULL """
        else:
            asset_type = 'purchase'
            condition += f"""AND aas.x_asset_type = '{x_asset_type}' """
        condition += f"""AND aas.asset_type = '{asset_type}' 
                        AND aas.branch_id = any(string_to_array('{branch_ids}', ',')::INTEGER[])"""

        query = f"""
                SELECT aas.id as account_asset_id, 
                    (SELECT COUNT(am.*) FROM account_move am 
                        WHERE am.asset_id = aas.id AND am.state = 'posted' 
                        AND am.date <= to_date('{date_to}','dd/mm/yyyy')) as num_posted, 
                    (SELECT COUNT(am.*) FROM account_move am 
                        WHERE am.asset_id = aas.id AND am.state != 'posted' 
                        AND am.date <= to_date('{date_to}','dd/mm/yyyy')) as num_un_post,			
                    aas.original_value, 
                    (SELECT code FROM account_account WHERE id = aas.account_depreciation_id) as account_depreciation,
                    (SELECT code FROM account_account WHERE id = aas.account_depreciation_expense_id) as account_depreciation_expense,
                    (SELECT am.asset_depreciated_value FROM account_move am 
                        WHERE am.asset_id = aas.id AND am.state = 'posted' 
                        AND am.date <= to_date('{date_to}','dd/mm/yyyy') 
                        ORDER BY date DESC LIMIT 1) as value_depreciated,
                    aas.original_value - (SELECT asset_depreciated_value FROM account_move 
                                            WHERE asset_id = aas.id AND state = 'posted' ORDER BY date DESC LIMIT 1) as value_residual
                FROM account_asset aas 
                {condition}
                """
        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()
        for item in data:
            val = (self.id, item['account_asset_id'], item['num_posted'], item['num_un_post'], item['original_value'],
                   item['account_depreciation'], item['account_depreciation_expense'], item['value_depreciated'],
                   item['value_residual'], self.company_id.id,)
            self.env.cr.execute("""INSERT INTO rpt_account_asset_line 
                                    (rpt_account_asset_id, account_asset_id, num_posted, num_un_post, original_value, 
                                    account_depreciation, account_depreciation_expense, value_depreciated, value_residual,
                                    company_id) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", val)

    @api.onchange('branch_ids')
    def _domain_branch_ids(self):
        branch_ids = self.env['res.branch'].search([('company_id', '=', self.env.company.id)])
        return {'domain': {'branch_ids': [('id', 'in', branch_ids.ids)]}}

class RPTAccountAssetLine(models.TransientModel):
    _name = 'rpt.account.asset.line'

    rpt_account_asset_id = fields.Many2one('rpt.account.asset', 'Account Asset')
    account_asset_id = fields.Many2one('account.asset', 'Account Asset')
    num_posted = fields.Integer('Number Posted')
    num_un_post = fields.Integer('Number UnPosted')
    original_value = fields.Float('Original Value', digits='Price Other')
    account_depreciation = fields.Char('Account Depreciation')
    account_depreciation_expense = fields.Char('Account Expense')
    value_depreciated = fields.Float('Depreciated Value', digits='Price Other')
    value_residual = fields.Float('Residual Value', digits='Price Other')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
