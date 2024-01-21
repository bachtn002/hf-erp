from odoo import fields, models, api, _
from datetime import datetime

from odoo.exceptions import UserError, _logger, ValidationError
from dateutil.relativedelta import relativedelta


class GeneralRequest(models.Model):
    _name = 'general.request'
    _description = 'General Request'
    _inherit = [
        'mail.thread'
    ]
    name = fields.Char('Name request', readonly=True, select=True, copy=True, default='New')
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.user.company_id,
                                 readonly='1')
    warehouse_id = fields.Many2one('stock.warehouse', string='Kho')
    date = fields.Date(string='Request Date', default=lambda x: datetime.today(), required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('done', 'Done'),
        ('cancel', 'Cancel'), ],
        string='Status', default='draft', track_visibility='always')
    general_request_line = fields.One2many(comodel_name='general.request.line', inverse_name='general_request_id',
                                           string='General Request Lines')

    general_warehouse_group_ids = fields.Many2many('general.warehouse.group', 'general_warehouse_group_table',
                                                   'general_id', 'group_id', string='Warehouse Group')

    general_product_group_ids = fields.Many2many('general.product.group', 'general_product_group_table', 'general_id',
                                                 'group_id',
                                                 string='Product Group')

    @api.onchange('warehouse_id')
    def _onchange_domain_group_warehouse(self):
        try:
            if self.warehouse_id:
                return {'domain': {'general_warehouse_group_ids': [('warehouse_id.id', '=', self.warehouse_id.id)]}}
            else:
                return {'domain': {'general_warehouse_group_ids': [('warehouse_id.id', '=', self.warehouse_id.id)]}}
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('general.request.seq') or '/'
        d_to = datetime.today()
        name = 'GR.' + str(d_to.year) + str(d_to.strftime('%m'))
        vals['name'] = name + '.' + seq
        return super(GeneralRequest, self).create(vals)

    def unlink(self):
        for rc in self:
            if rc.state == 'draft':
                return super(GeneralRequest, rc).unlink()
            raise UserError(_('You can only delete when state is draft '))

    def general_request_function(self):
        self.ensure_one()
        today = fields.Date.today()
        if self.date > today:
            raise UserError(
                _('You cannot choose a date in the future'))
        # lấy obj các kho cửa hàng
        # warehouse_supply_lines = self.env['warehouse.supply'].search(
        #     [('warehoue_source_id', '=', self.warehouse_id.id)])
        warehouse_ids = []
        for warehouse in self.general_warehouse_group_ids.warehouse_ids:
            warehouse_ids.append(warehouse.id)
        product_ids = []
        for product in self.general_product_group_ids.product_ids:
            product_ids.append(product.id)
        sale_requests = self.env['sale.request'].sudo().search(
            [('warehouse_id', 'in', warehouse_ids), ('state', '=', 'sent'),
             ('date_request', '=', self.date), ('warehouse_process', '=', False)])
        sale_request_lines = self.env['sale.request.line'].sudo().search(
            [('sale_request_id.warehouse_id', 'in', warehouse_ids),
             ('sale_request_id.date_request', '=', self.date + relativedelta(hours=7)),
             ('sale_request_id.state', '=', 'sent'), ('supply_type', '=', 'warehouse'),
             ('check_general', '=', False), ('product_id.id', 'in', product_ids)], order='create_date asc')
        general_request_lines = []
        if sale_request_lines:
            for line in sale_request_lines:
                vals = {
                    'request_line_id': line.id,
                    'general_request_id': self.id,
                    'product_id': line.product_id.id,
                    'qty': line.qty,
                    'qty_apply': line.qty_apply,
                    'note': line.note,
                    'warehoue_des_id': line.sale_request_id.warehouse_id.id
                }
                general_request_lines.append((0, 0, vals))
                line.check_general = True
                line.sale_request_id.count_general += 1
                if line.sale_request_id.count_general == len(line.sale_request_id.sale_request_line):
                    line.sale_request_id.state = 'processed'

        self.general_request_line = general_request_lines
        self.state = 'received'

    def import_general_request_function(self):
        return {
            'name': 'Import file',
            'type': 'ir.actions.act_window',
            'res_model': 'import.xls.wizard.general.request',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'current_id': self.id},
        }

    def confirm_import_general_request_function(self):
        # tạo phiếu chuyển kho theo kho
        self.ensure_one()
        if self.state == 'done':
            return True
        for line in self.general_request_line:
            if line.qty_apply > 0:
                transfer_line_obj = self.env['stock.transfer.line']
                general_request_line = self.env['general.request.line'].search(
                    [('general_request_id', '=', self.id), ('warehoue_des_id', '=', line.warehoue_des_id.id),
                     ('stock_transfer_id', '!=', False)], limit=1)
                if general_request_line:
                    vals_line = {
                        'stock_transfer_id': general_request_line.stock_transfer_id.id,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'quantity': line.qty_apply
                    }
                    transfer_line_obj.create(vals_line)
                    line.stock_transfer_id = general_request_line.stock_transfer_id.id
                else:
                    # se    lf.create_stock_transfer(self.warehouse_id, line.warehoue_des_id, line)
                    self.create_stock_transfer(line.warehoue_des_id, self.warehouse_id, line)

        self.state = 'done'

    def create_stock_transfer(self, warehouse_id, warehouse_dest_id, line):
        transfer_obj = self.env['stock.transfer']
        transfer_line_obj = self.env['stock.transfer.line']
        vals = {
            'warehouse_id': warehouse_dest_id.id,
            'warehouse_dest_id': warehouse_id.id,
            'origin': self.name,
            'state': 'draft'
        }
        transfer_id = transfer_obj.create(vals)
        if line.qty_apply > 0:
            vals_line = {
                'stock_transfer_id': transfer_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'quantity': line.qty_apply
            }
            transfer_line_obj.create(vals_line)
        line.stock_transfer_id = transfer_id.id

    def cancel_import_general_request_function(self):
        try:
            request_line_ids = []
            for rc in self.general_request_line:
                if rc.request_line_id:
                    request_line_ids.append(int(rc.request_line_id))
            print(request_line_ids)
            request_line = self.env['sale.request.line'].search([('id', 'in', request_line_ids)])
            print(request_line)
            if request_line:
                for line in request_line:
                    print(line)
                    line.check_general = False
                    line.sale_request_id.count_general -= 1
                    if line.sale_request_id.count_general < len(
                            line.sale_request_id.sale_request_line) and line.sale_request_id.state == 'processed':
                        line.sale_request_id.state = 'sent'
            self.state = 'cancel'
        except Exception as e:
            raise ValidationError(e)

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/general.request.report/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def print_pick_products_templates(self):
        # print multiple templates at once
        if self.state != 'done':
            raise UserError(_("You can not print template when request state is not done"))
        transfers_to_print = []
        ids_path = ''
        for line in self.general_request_line:
            if line.stock_transfer_id:
                if line.stock_transfer_id.id not in transfers_to_print and line.stock_transfer_id.state in ['draft',
                                                                                                            'confirmed']:
                    transfers_to_print.append(line.stock_transfer_id.id)
                    ids_path += str(line.stock_transfer_id.id) + ','

        ids_path = '/' + ids_path[:-1]
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_transfer.report_template_stock_transfer_from/%s' % ids_path,
            'target': 'new',
        }

    def action_create_stock_transfer_failed(self):
        try:
            self.ensure_one()
            general_request_lines = self.env['general.request.line'].search(
                [('general_request_id', '=', self.id), ('stock_transfer_id', '=', False)])
            for line in general_request_lines:
                if line.qty_apply > 0:
                    transfer_line_obj = self.env['stock.transfer.line']
                    general_request_line = self.env['general.request.line'].search(
                        [('general_request_id', '=', self.id), ('warehoue_des_id', '=', line.warehoue_des_id.id),
                         ('stock_transfer_id', '!=', False)], limit=1)
                    if general_request_line:
                        vals_line = {
                            'stock_transfer_id': general_request_line.stock_transfer_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'quantity': line.qty_apply
                        }
                        transfer_line_obj.create(vals_line)
                        line.stock_transfer_id = general_request_line.stock_transfer_id.id
                    else:
                        # se    lf.create_stock_transfer(self.warehouse_id, line.warehoue_des_id, line)
                        self.create_stock_transfer(line.warehoue_des_id, self.warehouse_id, line)

            self.state = 'done'
        except Exception as e:
            raise ValidationError(e)


class GeneralRequestLine(models.Model):
    _name = 'general.request.line'
    _description = 'General resquest line'

    general_request_id = fields.Many2one(comodel_name='general.request', string='General Request Reference',
                                         ondelete='cascade')
    # request_line_id = fields.Char(related='sale_request_id.name', string='Mã yêu cầu')
    # request_line_id map với sale_request_line_id
    request_line_id = fields.Char(string='Request Line ID')
    product_id = fields.Many2one('product.product', string='Product', change_default=True)
    product_uom = fields.Many2one('uom.uom', string='Uom', related='product_id.uom_id')
    # warehoue_des_id = fields.Many2one('stock.warehouse', string='Kho nhận hàng',
    #                                   related='general_request_id.warehouse_id')
    warehoue_des_id = fields.Many2one('stock.warehouse', string='Destination Stock')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    qty_apply = fields.Float(string='Apply quantity', digits='Product Unit of Measure', default=0)
    stock_transfer_id = fields.Many2one('stock.transfer', string='Stock transfer name', readonly=1)
    note = fields.Text('Note')
