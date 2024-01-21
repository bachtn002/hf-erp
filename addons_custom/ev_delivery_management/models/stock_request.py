# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockRequest(models.Model):
    _inherit = 'stock.request'

    x_ship_type = fields.Selection([('no', 'No'), ('internal', 'Internal'), ('other', 'Other')], 'Ship type',
                                   default='no')
    x_driver = fields.Selection([('out', 'Out'), ('in', 'In')], 'Warehouse Ship', default='out')

    # @api.onchange('x_ship_type', 'warehouse_id', 'warehouse_dest_id')
    # def _onchange_x_ship_type(self):
    #     try:
    #         self.check_infor_warehouse()
    #
    #     except Exception as e:
    #         raise ValidationError(e)

    def action_send(self):
        try:
            res = super(StockRequest, self).action_send()
            if self.x_ship_type == 'other' and not self.company_id.x_call_ship:
                raise UserError(_('The system does not allow calling to ship outside'))
            self.check_infor_warehouse()
            return res
        except Exception as e:
            raise ValidationError(e)

    def action_transfer(self):
        try:
            res = super(StockRequest, self).action_transfer()
            self.stock_transfer_id.x_ship_type = self.x_ship_type
            self.stock_transfer_id.x_driver = self.x_driver
            return res
        except Exception as e:
            raise ValidationError(e)

    def action_transfer_return(self):
        try:
            res = super(StockRequest, self).action_transfer_return()
            self.stock_transfer_id.x_ship_type = self.x_ship_type
            self.stock_transfer_id.x_driver = self.x_driver
            return res
        except Exception as e:
            raise ValidationError(e)

    def check_infor_warehouse(self):
        try:
            if self.type == 'transfer' and self.x_ship_type != 'no':
                shop_sender = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.warehouse_id.id), ('active', '=', True)], limit=1)
                shop_recipient = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.warehouse_dest_id.id), ('active', '=', True)],
                    limit=1)
                if not shop_sender:
                    raise UserError(_('Do not create delivery with warehouse %s') % self.warehouse_id.name)
                if not shop_recipient:
                    raise UserError(_('Do not create delivery with warehouse %s') % self.warehouse_dest_id.name)
                if not shop_sender.address or not shop_sender.phone or not shop_sender.lat or not shop_sender.long:
                    raise UserError(_('The warehouse %s lack of information to call delivery') % self.warehouse_id.name)
                if not shop_recipient.address or not shop_recipient.phone or not shop_recipient.lat or not shop_recipient.long:
                    raise UserError(
                        _('The warehouse %s lack of information to call delivery') % self.warehouse_dest_id.name)
        except Exception as e:
            raise ValidationError(e)
