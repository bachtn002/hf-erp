# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
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

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if 'lot_name' in ui_paymentline:
            lot_id = self.env['stock.production.lot'].search([('name', '=', ui_paymentline['lot_name'])], limit=1)
            res.update({
                'x_lot_id': lot_id.id,
            })
        return res

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        process_line = partial(self.env['pos.order.line']._order_line_fields, session_id=ui_order['pos_session_id'])
        total_price = 0  ##tổng các tiền khuyếm mại chiết khấu
        total_price_promotion = 0
        check = 0
        check_after = 0
        total_price_promotion_after = 0
        for rc in ui_order['lines']:
            product = self.env['product.template'].search([('id', '=', rc[2].get('product_id'))])
            if rc[2].get('x_is_price_promotion'):
                price_subtotal_after_promotion = rc[2].get('price_subtotal') + int(
                    rc[2].get('x_is_price_promotion')) * product.taxes_id.amount / 100
                total_price += int(rc[2].get('x_is_price_promotion')) * product.taxes_id.amount / 100
                rc[2].update({'price_subtotal': price_subtotal_after_promotion})
        # tính tổng các sản phẩm KM
        for rc in ui_order['lines']:
            if rc[2].get('price_subtotal') < 0:
                total_price_promotion += rc[2].get('price_subtotal')
                check += 1
        # tính chiết khấu theo từng KM theo %
        for rc in ui_order['lines']:
            if rc[2].get('price_subtotal') < 0 and check_after == check:
                rc[2].update({'price_subtotal_incl': total_price - total_price_promotion_after})
                rc[2].update({'price_subtotal': total_price - total_price_promotion_after})
            elif rc[2].get('price_subtotal') < 0 and check_after < check:
                count = rc[2].get('price_subtotal') / total_price_promotion
                price_promotion = round(total_price) * round(count, 2)
                total_price_promotion_after += price_promotion
                check_after += 1
                rc[2].update({'price_subtotal_incl': rc[2].get('price_subtotal') - price_promotion})
                rc[2].update({'price_subtotal': rc[2].get('price_subtotal') - price_promotion})
        return res
        # return {
        #     'user_id': ui_order['user_id'] or False,
        #     'session_id': ui_order['pos_session_id'],
        #     'lines': [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
        #     'pos_reference': ui_order['name'],
        #     'sequence_number': ui_order['sequence_number'],
        #     'partner_id': ui_order['partner_id'] or False,
        #     'date_order': ui_order['creation_date'].replace('T', ' ')[:19],
        #     'fiscal_position_id': ui_order['fiscal_position_id'],
        #     'pricelist_id': ui_order['pricelist_id'],
        #     'amount_paid': ui_order['amount_paid'],
        #     'amount_total': ui_order['amount_total'],
        #     'amount_tax': ui_order['amount_tax'],
        #     'amount_return': ui_order['amount_return'],
        #     'company_id': self.env['pos.session'].browse(ui_order['pos_session_id']).company_id.id,
        #     'to_invoice': ui_order['to_invoice'] if "to_invoice" in ui_order else False,
        #     'is_tipped': ui_order.get('is_tipped', False),
        #     'tip_amount': ui_order.get('tip_amount', 0),
        # }

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
            # for rc in self._order_fields(order).get('lines'):
            #     print('type', (rc[2]))
            #     print('product_id', rc[2].get('product_id'))
            #     product = self.env['product.template'].search([('id', '=', rc[2].get('product_id'))])
            #     print('product', product.taxes_id.amount)
            #     # applied_taxes = self.env['account.tax'].search([('id', '=', rc[2].get('tax_ids')[0][2][0])])
            #     if rc[2].get('x_is_price_promotion'):
            #         price_subtotal_after_promotion = rc[2].get('price_subtotal') + int(rc[2].get('x_is_price_promotion'))*product.taxes_id.amount/100
            #         print('price_subtotal_after_promotion', price_subtotal_after_promotion)
            #         rc[2].update({'price_subtotal': price_subtotal_after_promotion})
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

    def _update_infor_voucher_sale(self):
        for line in self.lines:
            if line.product_id and line.product_id.tracking != 'none':
                if not len(line.pack_lot_ids):
                    raise UserError(_("Chưa có mã Lô/Seri cho sản phẩm %s." % line.product_id.name))
                for pack_lot_id in line.pack_lot_ids:
                    lot_name = pack_lot_id.lot_name
                    lot_id = self.env['stock.production.lot'].search([('name', '=', lot_name)], limit=1)
                    expiration_date = False
                    if lot_id.x_release_id.expired_type == 'flexible':
                        expiration_date = self.date_order + relativedelta(months=lot_id.x_release_id.validity)
                    lot_vals = {
                        'x_order_id': self.id,
                        'x_customer_id': self.partner_id.id if self.partner_id else False,
                        'x_state': 'available',
                    }
                    if expiration_date:
                        lot_vals.update({
                            'expiration_date': expiration_date
                        })
                    lot_id.update(lot_vals)

    def _update_infor_voucher_user(self):
        for line in self.payment_ids:
            if line.payment_method_id.x_is_voucher:
                if not line.x_lot_id:
                    raise UserError(_("Chưa có mã Voucher/Coupon cho thanh toán %s." % line.payment_method_id.name))
                line.x_lot_id.update({
                    'x_order_use_id': self.id,
                    'x_use_customer_id': self.partner_id.id if self.partner_id else False,
                    'x_state': 'used',
                })

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        self._update_infor_voucher_sale()
        self._update_infor_voucher_user()
        return res
