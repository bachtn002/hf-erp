from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import osv
from odoo.exceptions import UserError, AccessError, except_orm
import xlrd
import base64


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sale_ok = fields.Boolean('Can be Sold', default=False)
    purchase_ok = fields.Boolean('Can be Purchased', default=False)
    x_is_voucher = fields.Boolean('Is voucher')
    x_is_blank_card = fields.Boolean('Is blank card', default=False)
    x_card_value = fields.Float('Card value')
    x_card_discount = fields.Float('Card discount')
    x_use_policy = fields.Text('Use policy')
    x_product_card_ids = fields.One2many('product.card.allow', 'product_id', string='Product card')
    x_product_category_card_ids = fields.One2many('product.category.card.allow', 'product_id',
                                                  string='Product category card')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    rule_apply_promotion = fields.Boolean(string=_('Rule apply promotion'))
    check_discount_price = fields.Selection([
        ('price', _('Price')),
        ('discount', _('Discount'))],
        string=_('State Choose'),
        default='price',
        required=True,
        tracking=True,
        copy=False)
    x_and_condition = fields.Boolean(_('And condition'), tracking=True)
    x_or_condition = fields.Boolean(_('Or condition'), tracking=True)
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id',
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')], default=False)
    type = fields.Selection([
        ('product', 'Storable Product'),
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default=False, required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.',
        tracking=True, ondelete={'product': 'set default'})
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=False, group_expand='_read_group_categ_id',
        required=True, help="Select category for the current product")
    list_price = fields.Float(
        'Sales Price', default=0.0,
        digits='Product Price',
        help="Price at which the product is sold to customers.")
    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=False, required=True,
        help="Default unit of measure used for all stock operations.")
    uom_po_id = fields.Many2one(
        'uom.uom', 'Purchase Unit of Measure',
        default=False, required=True,
        help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.")
    # @api.onchange('x_and_condition')
    # def on_change_x_and_condition(self):
    #     if self.x_and_condition:
    #         self.x_or_condition = False
    #     else:
    #         self.x_or_condition = True
    #
    # @api.onchange('x_or_condition')
    # def on_change_x_or_condition(self):
    #     if self.x_or_condition:
    #         self.x_and_condition = False
    #     else:
    #         self.x_and_condition = True
    #
    @api.constrains('x_or_condition', 'x_and_condition')
    def check_same_true_false(self):
        if self.x_or_condition and self.x_and_condition:
            raise UserError(_('And condition and or condition not true'))

    @api.constrains('x_card_value')
    def check_x_card_value(self):
        if self.x_card_value < 0:
            raise UserError(_('You can only create total price > 0'))

    @api.constrains('x_card_discount')
    def check_x_card_discount(self):
        if self.x_card_discount < 0:
            raise UserError(_('You can only create discount > 0'))
        elif self.x_card_discount > 100:
            raise UserError(_('You can only create discount < 100'))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_product_release/static/template/import_chinh_sach_ap_dung_voucher.xlsx',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_import_product_card(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            self.x_product_card_ids.unlink()
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 1).value
                if product_id:
                    move_vals = {
                        'product_id': self.id,
                        'maximum_quantity': qty,
                        'product_allow_id': product_id.id,
                    }
                    self.env['product.card.allow'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!", (e))

    def action_import_category_card(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            self.x_product_card_ids.unlink()
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 1).value
                if product_id:
                    move_vals = {
                        'product_id': self.id,
                        'maximum_quantity': qty,
                        'product_category_allow_id': product_id.id,
                    }
                    self.env['product.category.card.allow'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!", (e))

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        if res.x_is_voucher:
            if res.tracking != 'serial':
                raise ValidationError('Bạn chưa cấu hình truy vết sản phẩm theo serial')
        return res

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        for item in self:
            if item.x_is_voucher:
                if item.tracking != 'serial':
                    raise ValidationError('Bạn chưa cấu hình truy vết sản phẩm theo serial')
        return res

    @api.onchange('check_discount_price')
    def check_check_discount_price(self):
        if self.check_discount_price == 'price':
            self.x_card_discount = False
        elif self.check_discount_price == 'discount':
            self.x_card_value = False

    @api.onchange('x_is_blank_card')
    def _onchange_x_is_blank_card(self):
        if self.x_is_blank_card:
            self.tracking = 'serial'
            self.x_is_voucher = False
            self.type = 'product'
        else:
            self.tracking = 'none'

    @api.onchange('x_is_voucher')
    def _onchange_x_is_voucher(self):
        if self.x_is_voucher:
            self.tracking = 'serial'
            self.x_is_blank_card = False
        else:
            self.tracking = 'none'
            self.x_use_policy = False
            self.x_card_value = 0
            self.x_card_discount = 0
            self.x_product_card_ids = False
            self.x_product_category_card_ids = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_product_release/static/template/import_chinh_sach_ap_dung_voucher.xlsx',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_import_product_card(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            self.x_product_card_ids.unlink()
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 1).value
                if product_id:
                    move_vals = {
                        'product_id': self.id,
                        'maximum_quantity': qty,
                        'product_allow_id': product_id.id,
                    }
                    self.env['product.card.allow'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!", (e))

    def action_import_category_card(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            self.x_product_card_ids.unlink()
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 1).value
                if product_id:
                    move_vals = {
                        'product_id': self.id,
                        'maximum_quantity': qty,
                        'product_category_allow_id': product_id.id,
                    }
                    self.env['product.category.card.allow'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!", (e))
