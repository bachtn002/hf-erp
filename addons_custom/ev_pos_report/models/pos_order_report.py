# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    x_pos_shop_id = fields.Many2one('pos.shop', string='Shop', readonly=True)
    x_security_user_no_shop = fields.Boolean(related='x_pos_shop_id.security_user_no_shop')
    x_margin = fields.Float('Margin', readonly=True)

    def _where(self):
        return """
            WHERE s.state not in ('draft','cancel')
        """

    def _select(self):
        return super(PosOrderReport,
                     self)._select() + ', ps.x_pos_shop_id AS x_pos_shop_id, SUM(l.x_margin) as x_margin'

    def _group_by(self):
        return super(PosOrderReport, self)._group_by() + ',ps.x_pos_shop_id'

    def init(self):
        super(PosOrderReport, self).init()
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where(), self._group_by())
                         )
