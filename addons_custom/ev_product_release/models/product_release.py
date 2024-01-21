from odoo import api, fields, models, _
import random
import string
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import datetime
import io
from odoo.osv import osv
import xlrd
import base64


class ProductRelease(models.Model):
    _name = 'product.release'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char('Name', default=lambda self: _('New'))
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('created', 'Created'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='State', default='draft', required=True, tracking=True, copy=False)
    card_id = fields.Many2one('product.product', string='Card', track_visibility='onchange')
    blank_card_id = fields.Many2one('product.product', string='Blank card', track_visibility='onchange')
    date = fields.Date('Date', default=lambda x: fields.Date.today(), track_visibility='onchange')
    expired_type = fields.Selection(string='Expired type', selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')],
                                    default='fixed', track_visibility='onchange')
    validity = fields.Integer('Validity', track_visibility='onchange')
    expired_date = fields.Date('Expired date', track_visibility='onchange')
    use_type = fields.Selection(string='Use type', selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')],
                                default='flexible', track_visibility='onchange',
                                help=_(
                                    "predefined method: when customer A buys a voucher, only customer A can use that voucher, Flexible method: when customer A buys a voucher, anyone who has that voucher can use it"))
    picking_type_id = fields.Many2one('stock.picking.type', string='Release warehouse')
    quantity = fields.Integer('Quantity', default=1, track_visibility='onchange')
    count_picking = fields.Integer(string='Transfers', readonly=True, store=True, compute='_compute_count_picking')
    picking_ids = fields.One2many('stock.picking', 'x_product_release_id', string='Stock Picking')
    stock_production_lot_ids = fields.One2many('stock.production.lot', 'x_release_id', 'Details')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    production_lot_rule_id = fields.Many2one('stock.production.lot.rule', 'Code', track_visibility='onchange')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    import_file = fields.Boolean('Import file')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', track_visibility='onchange')
    account_expense_item_id = fields.Many2one('account.expense.item', 'Account Expense Item', track_visibility='onchange')
    account_expense_id = fields.Many2one('account.account', 'Account Expense', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', 'NEW') == 'NEW':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.release') or 'NEW'
        return super(ProductRelease, self).create(vals)

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise ValidationError(_("Cannot delete record with state is not 'Draft'"))
        return super(ProductRelease, self).unlink()

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('product.release') or 'NEW'
        default['date'] = fields.Date.today()
        default['import_file'] = False
        default['picking_ids'] = False
        default['count_picking'] = 0
        default['stock_production_lot_ids'] = False
        return super(ProductRelease, self).copy(default)

    # Tính toán số dịch chuyển từ stock.picking
    @api.depends('picking_ids')
    def _compute_count_picking(self):
        for item in self:
            item.count_picking = len(item.picking_ids)

    # nếu phương thức hết hạn là linh hoạt thì ẩn ngày hết hạn, nếu ngược lại thì ẩn số tháng hiệu lực
    @api.onchange('expired_type', 'expired_date', 'validity')
    def _onchange_check(self):
        if self.expired_type == 'flexible':
            self.expired_date = False
        else:
            self.validity = 0

    # Kiểm tra số tháng hiệu lực của thẻ, phải lớn hơn 0
    @api.constrains('card_id', 'expired_type', 'validity')
    def _check_validity(self):
        if self.card_id.x_is_voucher:
            if self.expired_type == 'flexible' and (self.validity <= 0 or self.validity is False):
                raise ValidationError(_("Validity must be greater than 0 !!!"))

    # Tạo mã cho đợt phát hành
    def action_generate_serial(self):
        if self.state != 'draft':
            return True
        # kiểm tra số lượng phát hành
        if self.quantity <= 0:
            raise ValidationError(_('Quantity must be greater than 0.'))
        # kiểm tra cấu hình độ dài mã voucher
        if self.env.company.x_voucher_code_rule_length <= 0:
            raise ValidationError(_('You did not config Voucher code rule length.'))

        self.stock_production_lot_ids = False
        code_lots = []
        for i in range(0, self.quantity - len(code_lots)):
            voucher = self.production_lot_rule_id.action_generate_code(code_lots)
            self._check_rule_length(voucher)
            code_lots.append(voucher)
        self._create_product_lot(lot_names=code_lots)
        self.state = 'created'

    def action_active(self):
        if self.state != 'created':
            return True
        # Kiểm tra tồn kho của phôi
        if self.blank_card_id:
            self._onchange_quantity_blank_card()
            self.do_export_blank_card()
        query_condition = f"""WHERE x_release_id = {self.id}"""
        # Check voucher bán hay không bán
        if self.card_id.sale_ok:
            query_set = """SET x_state = 'activated'"""
        else:
            query_set = """SET x_state = 'available'"""
        # Check phương thức hết hạn
        if self.expired_type == 'fixed':
            query_set += f", expiration_date=('{self.expired_date + relativedelta(days=1)}'::timestamp - INTERVAL '7 hours')"
            query = f"""UPDATE stock_production_lot
                        {query_set}
                        {query_condition}"""
        else:
            if not self.card_id.sale_ok:
                query_set += f", expiration_date=('{self.date + relativedelta(days=1, months=self.validity)}'::timestamp - INTERVAL '7 hours')"
            query = f"""UPDATE stock_production_lot
                        {query_set}
                        {query_condition}"""

        self.env.cr.execute(query)
        self.state = 'done'

    def do_export_blank_card(self):
        move_obj = self.env['stock.move']
        move_line_obj = self.env['stock.move.line']
        Picking_obj = self.env['stock.picking']
        if self.blank_card_id:
            # Thực hiện xuất phôi từ kho phát hành về kho ảo tồn kho, kiểu giao nhận là giao hàng(out_type_id)
            # Kho ảo tồn kho được lấy từ trong sản phẩm
            # chính là địa điểm kiểm kê trong nhóm địa điểm đối ứng.
            # Thực hiện việc xuất phôi từ kho phát hành đến kho ảo của sản phẩm để kiểm kê số lượng và giá gốc của sản phẩm đó
            picking_out_vals = {
                'picking_type_id': self.picking_type_id.warehouse_id.out_type_id.id,
                'date': datetime.date.today(),
                'origin': self.name,
                'location_id': self.picking_type_id.default_location_dest_id.id,
                'location_dest_id': self.picking_type_id.default_location_src_id.id,
                'state': 'assigned',
                'x_product_release_id': self.id,
            }
            picking_out_id = Picking_obj.create(picking_out_vals)
            stock_move_out_vals = {
                'product_id': self.blank_card_id.id,
                'origin': self.name,
                'product_uom': self.blank_card_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.blank_card_id.standard_price,
                'location_id': self.picking_type_id.default_location_dest_id.id,
                'location_dest_id': self.picking_type_id.default_location_src_id.id,
                'name': self.blank_card_id.product_tmpl_id.name,
                'state': 'assigned',
                'picking_id': picking_out_id.id,
            }
            move_out = move_obj.create(stock_move_out_vals)
            stock_move_out_line_vals = {
                'product_id': self.blank_card_id.id,
                'origin': self.name,
                'product_uom_id': self.blank_card_id.product_tmpl_id.uom_id.id,
                'qty_done': self.quantity,
                'location_id': self.picking_type_id.default_location_dest_id.id,
                'location_dest_id': self.picking_type_id.default_location_src_id.id,
                'move_id': move_out.id,
                'state': 'assigned',
                'picking_id': picking_out_id.id,
            }
            move_line_obj.create(stock_move_out_line_vals)
            picking_out_id._action_done()
        # Nếu thẻ mua hàng là kiểu 'consu'
        # Thực hiện nhập thẻ từ kho ảo sản xuất vào kho phát hành
        # sau khi xuất phôi từ kho phát hành sang kho ảo,
        # bên kho ảo sẽ thực hiện kiểm kê và in thẻ
        # rồi sau đó lại xuất thẻ đã được in từ phôi sang kho phát hành
        if self.card_id.type in ('consu', 'product'):
            picking_in_vals = {
                'picking_type_id': self.picking_type_id.warehouse_id.in_type_id.id,
                'date': datetime.date.today(),
                'origin': self.name,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                'state': 'assigned',
                'x_product_release_id': self.id,
            }
            picking_in_id = Picking_obj.create(picking_in_vals)
            stock_move_in_vals = {
                'product_id': self.card_id.id,
                'origin': self.name,
                'product_uom': self.card_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.card_id.standard_price,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                'name': self.card_id.product_tmpl_id.name,
                'state': 'assigned',
                'picking_id': picking_in_id.id,
            }
            move_in = move_obj.create(stock_move_in_vals)

            ob_ids = []
            for ob in self.stock_production_lot_ids:
                ob_ids.append({
                    'lot_id': ob.id,
                    'lot_name': ob.name,
                })
            data_file = ''
            state = 'assigned'
            for row in ob_ids:
                if data_file:
                    data_file += '\n'
                line = ''
                for k, v in row.items():
                    if line:
                        line += ','
                    line += str(v)
                line += f',{self.card_id.id},{self.card_id.product_tmpl_id.uom_id.id},1,1,' \
                        f'{self.picking_type_id.default_location_src_id.id},{self.picking_type_id.default_location_dest_id.id},' \
                        f'{move_in.id},{state},{picking_in_id.id},{self.company_id.id},{datetime.datetime.now()},' \
                        f'{datetime.datetime.now()},{self.env.user.id},{self.env.user.id},{datetime.datetime.now()}'
                data_file += line
            fieldnames = ['lot_id', 'lot_name', 'product_id', 'product_uom_id', 'qty_done', 'product_uom_qty',
                          'location_id', 'location_dest_id', 'move_id', 'state', 'picking_id', 'company_id',
                          'date', 'create_date', 'create_uid', 'write_uid', 'write_date']
            self.env.cr.copy_from(io.StringIO(data_file),
                                  table='stock_move_line',
                                  sep=',',
                                  columns=fieldnames,
                                  )
            picking_in_id._action_done()

    def action_cancel(self):
        self._cr.execute(f"""UPDATE stock_production_lot
                                SET x_state = 'destroy'
                                WHERE x_release_id = {self.id}""")
        self.write({'state': 'cancel'})

    def action_view_picking(self):
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_origin': self.name,
                             'default_picking_type_id': self.picking_type_id.id}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result

    def _create_product_lot(self, lot_names):
        lot_names = self.check_code(lot_names)
        data_file = ''
        new = 'new'
        for row in lot_names:
            if data_file:
                data_file += '\n'
            line = f'{row},{self.card_id.id},{self.company_id.id},{self.id},{new},{self.card_id.uom_id.id},' \
                   f'{datetime.datetime.now()},{self.env.user.id},{self.env.user.id},{datetime.datetime.now()}'
            data_file += line

        fieldnames = ['name', 'product_id', 'company_id', 'x_release_id', 'x_state', 'product_uom_id', 'create_date',
                      'create_uid', 'write_uid', 'write_date']
        self.env.cr.copy_from(io.StringIO(data_file), table='stock_production_lot', sep=',', columns=fieldnames)

    def check_code(self, code_lots):
        lots = []
        self._cr.execute(f"""SELECT name FROM stock_production_lot where company_id = {self.env.company.id}""")
        production_lots = self._cr.fetchall()
        for item in production_lots:
            lots.append(item[0])
        checks = list(set(code_lots) - set(lots))
        if len(code_lots) - len(checks) != 0:
            if not self.import_file:
                for i in range(0, len(code_lots) - len(checks)):
                    voucher = self.production_lot_rule_id.action_generate_code(code_lots)
                    self._check_rule_length(voucher)
                    checks.append(voucher)
                return self.check_code(code_lots)
        return checks

    def _check_rule_length(self, voucher_code):
        if len(voucher_code) != self.env.company.x_voucher_code_rule_length:
            raise ValidationError(_("Length of Voucher's code is different with allowable length : {}").format(
                self.env.company.x_voucher_code_rule_length))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_product_release/static/template/Mẫu mã Phiếu mua hàng.xlsx',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise ValidationError(
                    _("File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            code_lots = self._get_code_from_sheet(sheet)
            checked_code = self.check_code(code_lots)
            same = list(set(code_lots) - set(checked_code))
            if same:
                raise ValidationError(
                    _("You added duplicate Voucher's code. Please check those again.\n {}").format(same))
            self._create_product_lot(lot_names=code_lots)
            self.state = 'created'
            self.field_binary_import = False
            self.field_binary_name = False
        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_code_from_sheet(self, sheet):
        index = 1
        code_lots = []
        while index < sheet.nrows:
            lot_name = sheet.cell(index, 0).value
            if type(lot_name).__name__ == 'str':
                lot_name = lot_name.upper()
            else:
                lot_name = str(int(lot_name)).upper()
            if lot_name not in code_lots:
                code_lots.append(lot_name)
            index = index + 1
        return code_lots

    # Kiểm tra tồn kho của phôi
    @api.onchange('blank_card_id', 'picking_type_id', 'quantity')
    def _onchange_quantity_blank_card(self):
        if self.blank_card_id and self.picking_type_id and self.quantity:
            list_check = ''
            products = []
            inventory_check = self.env['product.product']._generate_list_product_or_lot(
                product_ids=f'{self.blank_card_id.id}',
                lot_ids='',
                date_to=datetime.date.today().strftime('%d/%m/%Y'),
                location_id=self.picking_type_id.default_location_dest_id.id)
            if inventory_check:
                for line_id in inventory_check:
                    if line_id[2] is None:
                        products.append(line_id[0])
                        compare = line_id[4] - self.quantity
                        if compare < 0:
                            list_check = list_check + "Sản phẩm: %s không đủ tồn kho.\n" \
                                                      "Tồn kho: %s \n" % (line_id[1], line_id[4])
            # check nhập tồn của phôi
            if self.blank_card_id.tracking == 'none':
                if self.blank_card_id.id not in products:
                    list_check = list_check + "Sản phẩm: %s chưa nhập tồn.\n" % self.blank_card_id.name
            if list_check:
                raise ValidationError(f'{list_check}Vui lòng kiểm tra lại!')
