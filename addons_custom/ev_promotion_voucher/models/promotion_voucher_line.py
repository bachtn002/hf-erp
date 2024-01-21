from datetime import date

from odoo import models, fields, api,_


class PromotionVoucherLine(models.Model):
    _name = 'promotion.voucher.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Code Line'
    promotion_voucher_id = fields.Many2one(comodel_name='promotion.voucher', string='Promotion Voucher Reference',
                                           ondelete='cascade')
    promotion_voucher_name = fields.Char('Promotion Voucher Name', related='promotion_voucher_id.name', store=True)
    name = fields.Char(
        _('promotion code'), default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Lot/Serial Number Promotion Code")
    state_promotion_code = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroy', 'Destroy')
    ], default='new', string='Status', )
    promotion_use_code = fields.Integer('Promotion use')
    customer_id = fields.Many2one('res.partner', 'Customer')
    use_customer_id = fields.Many2one('res.partner', 'Use Customer')
    expired_date = fields.Date('Expired Date', related='promotion_voucher_id.expired_date')
    pos_order = fields.Many2many('pos.order', string='Pos Order')
    date = fields.Date('Start Date', related='promotion_voucher_id.date')
    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion')

    # @api.depends('promotion_voucher_id', 'promotion_voucher_name')
    # def _compute_check_add(self):
    #     print('test', self.promotion_voucher_id.name)
    #     self.promotion_voucher_name = self.promotion_voucher_id.name

    _sql_constraints = [
        ('promotion_code_name_uniq', 'unique (name)',
         'The promotion code name must be unique!')
    ]

    @api.constrains('promotion_voucher_id')
    def add_promotion(self):
        self.promotion_id = self.promotion_voucher_id.promotion_id

    def check_promotion(self, name, customerID):
        data = {}
        promotion_voucher_lines = self.search([])
        lot_id = self.search([('name', '=', name)], limit=1)
        if not lot_id:
            data['type'] = 'existed'
            data['message'] = 'Code "%s" not exist in database. Please check!' % name
            return data
        if lot_id.state_promotion_code != 'available':
            data['type'] = 'not_activated'
            data[
                'message'] = 'Code "%s" not use promotion. Please check!' % name
            return data
        if lot_id.expired_date and lot_id.expired_date < date.today():
            data['type'] = 'not_exp'
            data['message'] = 'Code "%s" expired date.' % name
            return data
        data = {
            'type': 'valid',
            'promotion_id': lot_id.promotion_voucher_id.promotion_id.type,
            'lot_id': lot_id.id,
            'get_promotion_id': lot_id.promotion_voucher_id.promotion_id.id,
            'code_promotion': lot_id.name
        }
        # return lot_id.state_promotion_code
        return data

    def update_promotion_used(self, code_promotion):
        lot_id = self.search([('name', '=', code_promotion)], limit=1)
        if lot_id.promotion_use_code == 1:
            lot_id.state_promotion_code = 'used'
            lot_id.promotion_use_code = 0
        else:
            lot_id.promotion_use_code = lot_id.promotion_use_code - 1

    def update_promotion_used_return(self, code_promotion):
        lot_id = self.search([('name', '=', code_promotion)], limit=1)
        if lot_id.promotion_use_code == 0:
            lot_id.state_promotion_code = 'available'
            lot_id.promotion_use_code = 1
        else:
            lot_id.promotion_use_code = lot_id.promotion_use_code + 1

    def update_status_use(self, pos_reference):
        pos_order = self.env['pos.order'].search([('pos_reference', '=', pos_reference)])
