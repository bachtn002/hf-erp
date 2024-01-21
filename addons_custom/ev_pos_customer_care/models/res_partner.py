# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pos_order_count_care = fields.Integer(
        compute='_compute_pos_order_care',
        help="The number of point of sales orders related to this customer",
    )

    def _compute_pos_order_care(self):
        partners_data = self.env['pos.order'].read_group([('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        mapped_data = dict([(partner['partner_id'][0], partner['partner_id_count']) for partner in partners_data])
        for partner in self:
            partner.pos_order_count_care = mapped_data.get(partner.id, 0)
