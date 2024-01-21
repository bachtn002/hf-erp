# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'
    x_address_shop = fields.Char('Address Shop')
    x_name_shop = fields.Char('Name Shop')
    x_code_shop = fields.Char('Code Shop')

    @api.constrains('receipt_header')
    def onchange_receipt_header(self):
        try:
            address_pos_shop = self.env['pos.shop'].search(
                [('id', '=', self.x_pos_shop_id.id)]).address if self.x_pos_shop_id else False
            if self.receipt_header:
                if len(self.receipt_header.strip(' ')) != 0:
                    self.x_address_shop = self.receipt_header
                else:
                    self.x_address_shop = address_pos_shop
            else:
                self.x_address_shop = address_pos_shop
        except Exception as e:
            raise ValidationError(e)

    def get_address_shop_call(self, id_pos):
        pos_config = self.env['pos.config'].search([('id', '=', id_pos)])
        address_pos_shop = self.env['pos.shop'].search([('id', '=', pos_config.x_pos_shop_id.id)]).address
        if self.receipt_header:
            self.x_address_shop = self.receipt_header
        else:
            self.x_address_shop = address_pos_shop

    def get_name_shop_call(self, id_pos):
        pos_config = self.env['pos.config'].search([('id', '=', id_pos)])
        name_pos_shop = self.env['pos.shop'].search([('id', '=', pos_config.x_pos_shop_id.id)]).name
        if not self.x_name_shop:
            self.x_name_shop = name_pos_shop
        elif len(self.x_name_shop) != len(name_pos_shop):
            self.x_name_shop = name_pos_shop

    def get_code_shop_call(self, id_pos):
        pos_config = self.env['pos.config'].search([('id', '=', id_pos)])
        code_pos_shop = self.env['pos.shop'].search([('id', '=', pos_config.x_pos_shop_id.id)]).code
        if not self.x_code_shop:
            self.x_code_shop = code_pos_shop
        elif len(self.x_code_shop) != len(code_pos_shop):
            self.x_code_shop = code_pos_shop
