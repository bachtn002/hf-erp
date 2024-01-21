import base64

import xlrd

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
import datetime
import io

from odoo.osv import osv


class PromotionVoucher(models.Model):
    _name = 'promotion.voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Code'
    # name = fields.Char(
    #     'Lot/Serial Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
    #     required=True, help="Unique Lot/Serial Number", index=True)
    name = fields.Char('Name', default=lambda self: _('New'))
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('created', 'Created'),
        ('active', 'Active'),
        ('cancel', 'Cancel')
    ], string='Status', default='draft', required=True, tracking=True, copy=False, track_visibility='onchange')
    date = fields.Date('Date start', default=fields.Date.today(), track_visibility='onchange')
    expired_type = fields.Selection(string=_('Expired type selection'),
                                    selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')],
                                    default='fixed', track_visibility='onchange',
                                    help=_('Flexible : applies to the number of months entered from the activation date - Fixed : applies to the date entered from the activation date'))
    validity = fields.Integer('Month Validity', track_visibility='onchange')
    expired_date = fields.Date(_('Expired date'), track_visibility='onchange')
    # promotion_id = fields.Integer('Mã chương trình khuyến mãi')
    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion', required=True, track_visibility='onchange')
    quantity = fields.Integer('Quantity', required=True, track_visibility='onchange')
    production_lot_rule_id = fields.Many2one('stock.production.lot.rule', 'Code generation rules')
    promotion_use_code = fields.Integer('Promotion Use Code', required=True, track_visibility='onchange')
    promotion_voucher_line = fields.One2many(comodel_name='promotion.voucher.line', inverse_name='promotion_voucher_id',
                                             string='Promotion Voucher Lines')
    promotion_voucher_line_use = fields.One2many(comodel_name='promotion.voucher.line',
                                                 inverse_name='promotion_voucher_id',
                                                 string='Promotion Voucher Lines')
    promotion_voucher_status = fields.One2many(comodel_name='promotion.voucher.status',
                                               inverse_name='promotion_voucher_status_id',
                                               string='Promotion Voucher Lines')
    promotion_voucher_count = fields.One2many(comodel_name='promotion.voucher.count',
                                              inverse_name='promotion_voucher_count_id',
                                              string='Promotion Voucher Count')
    # apply_promotion = fields.Boolean('Apply together with promotion')
    # config_ids = fields.Many2many('pos.config', string='POS Apply')
    limit_voucher = fields.Boolean('Limit number of promotion voucher apply in the order', track_visibility='onchange')
    limit_qty = fields.Integer('Quantity', default=5, track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    _sql_constraints = [
        ('code_uniq', 'UNIQUE (name)', 'You can not have two users with the same code !')
    ]
    import_file = fields.Boolean('Import file')
    field_binary_import_promotion_code = fields.Binary(string="Field Binary Import")
    field_binary_name_promotion_code = fields.Char(string="Field Binary Name")
    pos_configs = fields.Many2many('pos.config',
                                   string=_('Pos config'),
                                   required=False,
                                   help='If not setting, apply promotion for all pos')

    def print_promotion_code(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/promotion.code.report/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def print_promotion_code_status(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/promotion.code.status.report/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def download_template_promotion_code(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_promotion_voucher/static/template/mẫu phiếu import promotion code.xls',
            "target": "_parent",
        }

    def action_import_line_promotion_code(self):
        try:
            if not self._check_format_excel(self.field_binary_name_promotion_code):
                raise ValidationError(_(
                    "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodebytes(self.field_binary_import_promotion_code)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            data_sheet = self._get_data_from_sheet(sheet)
            # Check mã code đã tồn tại
            # checked_promotion_code = self.check_promotion_code(data_sheet)
            # if not checked_promotion_code:
            #     raise ValidationError(
            #         _("Name code is existed. Please check those again.\n {}").format(checked_promotion_code))
            self._create_promotion_code(data_sheet=data_sheet)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_data_from_sheet(self, sheet):
        index = 1
        data = []
        while index < sheet.nrows:
            arr = []
            code = sheet.cell(index, 0).value
            number_used = sheet.cell(index, 1).value
            arr.append(code)
            arr.append(int(number_used))
            if arr not in data:
                data.append(arr)
            index = index + 1
        return data

    def check_promotion_code(self, datasheet):
        lots = []
        checks = []
        self._cr.execute(f"""SELECT name FROM promotion_voucher_line""")
        promotion_codes = self._cr.fetchall()
        for item in datasheet:
            if type(item[0]).__name__ in ['int', 'float']:
                item[0] = str(int(item[0]))
            else:
                item[0] = str(item[0])
            if len(item[0]) > 14:
                raise ValidationError(
                    _("Length of Voucher's code is different with allowable length : 14. Please check those again.\n"))

            lots.append(item[0])
        for promotion_code in promotion_codes:
            if str(promotion_code[0]) in lots:
                checks.append(promotion_code[0])
        if len(checks) > 0:
            return False
        return True

    def _create_promotion_code(self, data_sheet):
        use_code_promotion = []
        for data in data_sheet:
            if data[1] not in use_code_promotion:
                use_code_promotion.append(data[1])
            self._cr.execute(
                f"""INSERT INTO promotion_voucher_line(promotion_voucher_id,name,state_promotion_code,promotion_use_code,promotion_id) VALUES ('{self.id}','{data[0]}','active','{data[1]}','{self.promotion_id.id}')""")
        self.state = 'created'
        if len(use_code_promotion) == 1:
            # Cap nhật số lượng mã, số lần sử dụng trên master
            self.promotion_use_code = use_code_promotion[0]
            self.quantity = len(data_sheet)
        if len(use_code_promotion) > 1:
            raise ValidationError(
                _("Promotion code not same. Please check those again"))

    @api.model
    def create(self, vals):
        if vals.get('name', 'NEW') == 'NEW':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.release.promotion') or 'NEW'
        return super(PromotionVoucher, self).create(vals)

    def _check_rule_length(self, voucher_code):
        if len(voucher_code) != self.env.company.x_voucher_code_rule_length:
            raise ValidationError(_("Length of Voucher's code is different with allowable length : {}").format(
                self.env.company.x_voucher_code_rule_length))
    
    def _check_voucher_random(self, voucher):
        check = self.env['promotion.voucher.line'].search([('name','=',voucher)], limit = 1)
        if check:
            return True
        else: 
            return False
    
    def _factorial(self, n):
        factorial = 1
        if (n == 0 or n == 1):
            return factorial
        else:
            for i in range(2, n + 1):
                factorial = factorial * i
            return factorial
    
    def unlink(self):
        for rc in self:
            if rc.state == 'draft':
                return super(PromotionVoucher, rc).unlink()
            raise UserError(_('You can only delete when state is draft '))

    def action_generate_serial(self):
        if self.state != 'draft':
            return True
        # kiểm tra số lượng phát hành
        value = ''
        # Quy tắc sinh mã
        rule_ids = self.env['stock.production.lot.rule.line'].search([('rule_id', '=', self.production_lot_rule_id.id)], order='sequence')
        for rule in rule_ids:
            if rule.type == 'fix':
                value = rule.value
        max_num_of_rule = self._factorial(36) / self._factorial((36 - (14-len(value))))
        if self.quantity > int(max_num_of_rule):
            raise ValidationError(_('Quantity {} is greater than max number of rule {} can create').format(self.quantity, int(max_num_of_rule)))
        if self.quantity <= 0:
            raise ValidationError(_('Quantity must is greater 0'))
        if self.promotion_use_code <= 0:
            raise ValidationError(_('Promotion use must is greater 0'))
        # kiểm tra cấu hình độ dài mã voucher
        if self.env.company.x_voucher_code_rule_length <= 0:
            raise ValidationError(_('You did not config Voucher code rule length.'))
        code_lots = []
        # Gen mã và check trùng mã (random lại tối đa 7 lần nếu trùng)
        for i in range(0, int(self.quantity * 5) - len(code_lots)):
            if len(code_lots) == self.quantity:
                break
            count = 0
            while(count <= 7):
                voucher = self.production_lot_rule_id.action_generate_code(code_lots)
                self._check_rule_length(voucher)
                res_check = self._check_voucher_random(voucher)
                if res_check == True or voucher in code_lots:
                    count +=1
                else:
                    code_lots.append(voucher)
                    break
        self._create_product_lot(lot_names=code_lots)

    def _create_product_lot(self, lot_names):
        data_file = ''
        new = 'new'
        for row in lot_names:
            self.env['promotion.voucher.line'].sudo().create(
                {'name': row,
                 'promotion_use_code': self.promotion_use_code,
                 'promotion_voucher_id': self.id
                 })
            self.env.cr.commit()
        self._cr.execute(f"""UPDATE promotion_voucher_line
                                                SET state_promotion_code = 'active'
                                                WHERE promotion_voucher_id = {self.id}""")
        self.state = 'created'

    def action_cancel(self):
        self._cr.execute(f"""UPDATE promotion_voucher_line
                                        SET state_promotion_code = 'destroy'
                                        WHERE promotion_voucher_id = {self.id}""")
        self.write({'state': 'cancel'})

    def action_active(self):
        self._cr.execute(f"""UPDATE promotion_voucher_line
                                                SET state_promotion_code = 'available'
                                                WHERE promotion_voucher_id = {self.id}""")
        self.state = 'active'

    @api.onchange('expired_type', 'expired_date', 'validity')
    def _onchange_check(self):
        if self.expired_type == 'flexible':
            self.expired_date = False
        else:
            self.validity = 0
