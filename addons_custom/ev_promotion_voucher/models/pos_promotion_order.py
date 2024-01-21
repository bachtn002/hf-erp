import logging
from datetime import timedelta, datetime
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # x_promotion_voucher_id = fields.Many2one('promotion.voucher.line', string='Promotion Voucher')

    @api.model
    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param bool draft: Indicate that the pos_order is not validated yet.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        if not draft:
            try:
                pos_order.action_pos_order_paid()
                # tiennq edit
                pos_order._create_order_picking()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order or Picking process: %s', tools.ustr(e))
        if pos_order.to_invoice and pos_order.state == 'paid':
            pos_order.action_pos_order_invoice()
        return pos_order.id

    def update_promotion_used(self, promotion_id, code_promotion):
        promotion_voucher = self.env['promotion.voucher'].search([('promotion_id', '=', promotion_id)])
        lot_id = promotion_voucher.search([('name', '=', code_promotion)], limit=1)

        if lot_id.promotion_use_code == 1:
            lot_id.state_promotion_code = 'used'
            lot_id.promotion_use_code = 0
        else:
            lot_id.promotion_use_code = lot_id.promotion_use_code - 1

    def update_status(self, pos_reference, promotion_code):
        order = self.env['pos.order'].search([('pos_reference', '=', pos_reference)])
        promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', promotion_code)])
        promotion_voucher = promotion_voucher_line.promotion_voucher_id
        self.env['promotion.voucher.status'].sudo().create(
            {'promotion_code': promotion_code,
             'promotion_voucher_status_id': promotion_voucher.id,
             'pos_order': order.id,
             'date': str(datetime.today().date())
             })
        self.env.cr.commit()

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        return res


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    promotion_code = fields.Char('Promotion Code')