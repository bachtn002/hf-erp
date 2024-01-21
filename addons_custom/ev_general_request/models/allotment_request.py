from odoo import fields, models, api, _
from datetime import datetime

from odoo.exceptions import UserError, _logger, ValidationError
from dateutil.relativedelta import relativedelta


class AllotmentRequest(models.Model):
    _name = 'allotment.request'
    _description = 'Allotment Request'
    _inherit = [
        'mail.thread'
    ]
    _order = 'create_date desc'

    name = fields.Char('Name request', readonly=True, select=True, copy=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id,
                                 readonly='1')
    general_request_id = fields.Many2one('general.request', string='General Request Name', required=True,
                                         domain=[('state', '=', 'received'), ('general_request_line', '!=', False)])
    date = fields.Date(string='Allotment Date', default=lambda x: datetime.today(), required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel')],
        string='Status', default='draft', track_visibility='always')
    allotment_request_lines = fields.One2many(comodel_name='allotment.request.line',
                                              inverse_name='allotment_request_id',
                                              string='Allotment Request Lines')

    def get_general_request(self):
        try:
            if self.allotment_request_lines:
                for line in self.allotment_request_lines:
                    line.unlink()
            vals = []
            for line in self.general_request_id.general_request_line:
                val = {
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'qty': line.qty,
                    'warehoue_des_id': line.warehoue_des_id.id,
                    'allotment_request_id': self.id,
                }
                vals.append((0, 0, val))
            self.allotment_request_lines = vals
        except Exception as e:
            raise ValidationError(e)

    def confirm_import_allotment_request(self):
        try:
            self.ensure_one()
            if self.state == 'done':
                return True
            if not self.allotment_request_lines:
                raise UserError(_('Detail none not confirm'))
            else:
                check = False
                for line in self.allotment_request_lines:
                    if line.qty_apply > 0:
                        check = True
                        break
            if check == False:
                raise UserError(_('You have not allocated'))
            for line in self.allotment_request_lines:
                if line.qty_apply > 0:
                    transfer_line_obj = self.env['stock.transfer.line']
                    allotment_request_line = self.env['allotment.request.line'].search(
                        [('allotment_request_id', '=', self.id), ('warehoue_des_id', '=', line.warehoue_des_id.id),
                         ('stock_transfer_id', '!=', False)], limit=1)
                    if allotment_request_line:
                        vals_line = {
                            'stock_transfer_id': allotment_request_line.stock_transfer_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'quantity': line.qty_apply
                        }
                        transfer_line_obj.create(vals_line)
                        line.stock_transfer_id = allotment_request_line.stock_transfer_id.id
                    else:
                        # se    lf.create_stock_transfer(self.warehouse_id, line.warehoue_des_id, line)
                        self.create_stock_transfer(line.warehoue_des_id, self.general_request_id.warehouse_id, line)
            self.date = datetime.today()
            self.state = 'done'
            self.general_request_id.state = 'done'

        except Exception as e:
            raise ValidationError(e)

    def create_stock_transfer(self, warehouse_id, warehouse_dest_id, line):
        try:
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

        except Exception as e:
            raise ValidationError(e)

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/ev_general_request.allotment_request_report/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def action_cancel(self):
        if self.state != 'cancel':
            self.state = 'cancel'

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('allotment.request') or '/'
        d_to = datetime.today()
        name = 'AR.' + str(d_to.year) + str(d_to.strftime('%m'))+ str(d_to.day)
        vals['name'] = name + '.' + seq
        return super(AllotmentRequest, self).create(vals)
