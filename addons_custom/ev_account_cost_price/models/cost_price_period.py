# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.osv import osv
import datetime
import logging
from datetime import date as d, datetime as dt
import xlrd
import base64
from odoo.tools.misc import formatLang, format_date, get_lang

_logger = logging.getLogger(__name__)


class CostPricePeriod(models.Model):
    _name = 'cost.price.period'
    _order = 'create_date desc'
    _inherit = 'mail.thread'

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Name", default="New", track_visibility='always')
    activity = fields.Char(string="Activity", track_visibility='always')
    date = fields.Date(string='Date', track_visibility='always', default=fields.Date.today())
    date_from = fields.Date(string='Date From', track_visibility='always', default=fields.Date.today())
    date_to = fields.Date(string="Date To", track_visibility='always', default=fields.Date.today())
    category_ids = fields.Many2many('product.category', string="Categories", track_visibility='always')
    state = fields.Selection(
        [('draft', 'Draft'), ('calculate', 'Calculate'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Cancel')], string="State",
        default='draft', track_visibility='always')
    period_lines = fields.One2many('cost.price.period.line', 'period_id', string="Periods", track_visibility='always')
    company_id = fields.Many2one('res.company', string="Company", default=_default_company, track_visibility='always')
    account_fiscal_month_id = fields.Many2one('account.fiscal.month', 'Accounting Period')
    type = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')], string="Type", track_visibility='always')
    inventory_valuation_group_id = fields.Many2one('inventory.valuation.group', 'Inventory Valuation Group')
    account_id = fields.Many2one('account.account', 'Account Calculate')
    #product_ids = fields.Many2many('product.product', 'cost_price_period_product', 'period_id', 'product_id', string='Product')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    note1 = fields.Char('Note1',
                        default='* Trạng thái "tính toán" để tính toán và cập nhật giá trị của các đơn xuất NVL chế biến...')
    note2 = fields.Char('Note2', default='* Trạng thái "xác nhận" đã tính toán giá vốn đầy đủ cho tất cả sản phẩm có giao dịch trong kỳ')

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    _('You cannot delete record state != Draft.'))
            sql = """
                DELETE FROM product_price_history a
                USING cost_price_period_line b
                WHERE a.cost_price_period_line_id = b.id
                AND b.period_id = %d;
            """
            self._cr.execute(sql % (record.id))
        return super(CostPricePeriod, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cost.price.period')
        return super(CostPricePeriod, self).create(vals)

    def action_calculate(self):
        self.ensure_one()
        sql1 = """
            DELETE FROM cost_price_period_detail a
            USING cost_price_period_line b
            WHERE b.period_id = %d AND a.period_line_id = b.id;
            DELETE FROM cost_price_period_line WHERE period_id = %d;
            """
        self._cr.execute(sql1 % (self.id, self.id))
        self._cr.commit()
        if self.type == 'auto':
            self.ensure_one()
            self._check_fiscalyear_lock_date()
            date_from = self.account_fiscal_month_id.date_from
            date_to = self.account_fiscal_month_id.date_to
            self.date_from = date_from
            self.date_to = date_to
            company_id = self.company_id.id
            if date_from > date_to:
                raise UserError(
                    _('Date from cannot later date to'))
            lang = self.env['res.lang'].search([('code', '=', self.env.lang)], limit=1)
            if lang:
                date_format = lang.date_format
            period_calculate = self.env['cost.price.period'].search(
                [('date_to', '<', date_from), ('company_id', '=', company_id), ('state', '=', 'done')],
                order='date_to desc', limit=1)
            if period_calculate:
                if (date_from - period_calculate.date_to).days > 1:
                    raise UserError(
                        _('The last period you counted was ' + period_calculate.date_from.strftime(
                            date_format) + ' to ' + period_calculate.date_to.strftime(date_format)))
            data_sequence = self.env['product.template'].read_group(
                [('x_sequence_calculate', '!=', False)],
                ['x_sequence_calculate'],
                ['x_sequence_calculate'],
                ['x_sequence_calculate'])
            for sequences in data_sequence:
                self._get_product_by_inventory_valuation_group(date_from, date_to, sequences['x_sequence_calculate'])
                for period_line in self.period_lines:
                    qty = period_line.qty_initial + period_line.qty_in
                    value = period_line.value_initial + period_line.value_in
                    cost_price = value / (qty or 1)
                    if qty == 0:
                        cost_price = period_line.product_id.standard_price
                    period_line.write({'standard_price': cost_price})
                self.update_account_move_inventory_valuation(date_from, date_to, sequences['x_sequence_calculate'])
                self.update_account_move_inventory_valuation_process(date_from, date_to, sequences['x_sequence_calculate'])
        self.write({'state': 'calculate'})

    def _action_done(self, calculate):
        """
        :return:
        """
        for record in self:
            company_id = record.env.user.company_id.id
            date_from = record.account_fiscal_month_id.date_from
            date_to = record.account_fiscal_month_id.date_to
            for period_line in record.period_lines:
                if period_line.standard_price < 0:
                    raise UserError(
                        _('Giá vốn của SP ' + period_line.product_id.name + ' nhỏ hơn 0'))
            if calculate != 'calculate':
                for period_line in record.period_lines:
                    period_line.date_from = date_from
                    period_line.date_to = date_to
                    period_line.date = record.date
                    cost_history = self.env['product.price.history'].search([('product_id', '=', period_line.product_id.id),
                                                                             ('datetime', '=', period_line.date_to), (
                                                                                 'inventory_valuation_group_id', '=',
                                                                                 record.inventory_valuation_group_id.id)], limit=1)
                    if cost_history:
                        cost_history.cost_price_period_line_id = period_line.id
                        cost_history.cost = period_line.standard_price
                    else:
                        self.env['product.price.history'].create({
                            'product_id': period_line.product_id.id,
                            'product_tmpl_id': period_line.product_id.product_tmpl_id.id,
                            'cost': period_line.standard_price,
                            'datetime': period_line.date_to,
                            'cost_price_period_line_id': period_line.id,
                            'company_id': company_id,
                            'inventory_valuation_group_id': record.inventory_valuation_group_id.id
                        })
                record.update_standard_price()
                record.update_account_move_inventory_valuation_transfer(date_from, date_to)
                record.update_pos_order_line(date_from, date_to)
                record.update_account_move_inventory_valuation_refund_pos(date_from, date_to)
                record.update_account_move_inventory_valuation_total(date_from, date_to)
                record.update_account_asset(date_from, date_to)

    def action_done(self):
        self._action_done('done')
        self.write({'state': 'done'})

    def action_back(self):
        """
        :return:
        """
        for record in self:
            if record.state in ('calculate', 'confirm'):
                record.write({'state': 'draft'})
                record.write({'activity': ''})
            else:
                lang = self.env['res.lang'].search([('code', '=', record.env.lang)], limit=1)
                if lang:
                    date_format = lang.date_format
                if record.company_id.period_lock_date:
                    if record.company_id.period_lock_date >= record.date_from:
                        raise UserError(
                            _('Bạn đã khóa kỳ vào ngày ' + record.company_id.period_lock_date.strftime(date_format)))
                record.write({'state': 'draft'})
                record.write({'activity': ''})
        return True

    def _get_detail(self, account_id, sequence):
        sql = """
            INSERT INTO cost_price_period_detail(period_line_id, account_move_name, description, qty, 
            value,create_date,create_uid,write_uid,write_date)
            SELECT a.id, c.name , c.ref, sum(b.quantity/f.factor) sl, sum(b.balance) gt,
            now() as create_date,
            (%s) as create_uid,
            (%s) as write_uid,
            now() as write_date 
            FROM cost_price_period_line a, account_move_line b, account_move c, cost_price_period d, uom_uom f, product_product g, product_template h
            WHERE a.period_id = %s
            AND a.product_id = b.product_id AND a.period_id = d.id AND b.product_uom_id = f.id
            AND b.date >= d.date_from AND b.date <= d.date_to
            AND b.move_id = c.id AND c.state = 'posted'
            AND b.account_id = %s AND b.x_type_transfer = 'in'
            and c.move_type != 'in_refund'
            and a.product_id = g.id 
            and g.product_tmpl_id = h.id 
            and h.x_sequence_calculate = %s
            GROUP BY a.id, c.name, c.ref
            
            UNION ALL 
            SELECT a.id, c.name , c.ref, -sum(b.quantity/f.factor) sl, sum(b.balance) gt,
            now() as create_date,
            (%s) as create_uid,
            (%s) as write_uid,
            now() as write_date 
            FROM cost_price_period_line a, account_move_line b, account_move c, cost_price_period d, uom_uom f, product_product g, product_template h
            WHERE a.period_id = %s
            AND a.product_id = b.product_id AND a.period_id = d.id AND b.product_uom_id = f.id
            AND b.date >= d.date_from AND b.date <= d.date_to
            AND b.move_id = c.id AND c.state = 'posted'
            AND b.account_id = %s AND b.x_type_transfer = 'in'
            and c.move_type = 'in_refund'
            and a.product_id = g.id 
            and g.product_tmpl_id = h.id 
            and h.x_sequence_calculate = %s
            GROUP BY a.id, c.name, c.ref;
            """
        self._cr.execute(sql, (
            self.env.user.id, self.env.user.id, self.id, str(account_id), sequence, str(self.env.user.id),
            str(self.env.user.id), str(self.id), str(account_id), sequence))
        self._cr.commit()

    def _get_product_by_inventory_valuation_group(self, date_from, date_to, sequence):
        product_categ_ids = self.env['product.category'].search(
            [('property_stock_valuation_account_id', '!=', False)])
        list_account = []
        if self.account_id:
            list_account.append(self.account_id.id)
        else:
            for categ_id in product_categ_ids:
                if categ_id.property_stock_valuation_account_id.id not in list_account:
                    list_account.append(categ_id.property_stock_valuation_account_id.id)

        for account in list_account:
            sql = """
                INSERT INTO cost_price_period_line(period_id, product_id, uom_id, method_add, 
                qty_in, value_in, qty_initial, value_initial, standard_price, create_date,create_uid,write_uid,write_date)
                 SELECT 
                (%s) period_id,	a.prdid, a.uomid, 'auto' method_add,
                sum(sl_nhap), sum(gt_nhap), sum(sl_dauky), sum(gt_dauky),
                CASE WHEN (sum(sl_nhap) + sum(sl_dauky)) = 0 
                            THEN 0
                            ELSE round((sum(gt_nhap)+sum(gt_dauky))/(sum(sl_nhap) +sum(sl_dauky))) END as standard_price,
                now() as create_date, (%s) as create_uid, (%s) as write_uid, now() as write_date 
                FROM 
                    (SELECT prdid, uomid, sum(sl_dauky) as sl_dauky, sum (gt_dauky) as gt_dauky,0 as sl_nhap ,0 as gt_nhap 
                    FROM 
                        (SELECT a.product_id prdid, c.uom_id uomid,
                        CASE WHEN d.move_type != 'in_refund' THEN (a.quantity/coalesce(f.factor,1))
                        ELSE -abs(a.quantity/coalesce(f.factor,1)) END as sl_dauky, a.balance gt_dauky
                    FROM account_move_line a, product_product b, product_template c, account_move d, uom_uom f
                    WHERE a.account_id = %s
                    AND a.date < %s
                    AND a.move_id = d.id AND a.product_id = b.id
                    AND b.product_tmpl_id = c.id AND a.product_uom_id = f.id
                    and c.x_sequence_calculate = %s
                    AND d.state = 'posted') as dk
                    GROUP BY prdid, uomid
               UNION All
                   SELECT prdid, uomid, 0 as sl_dauky, 0 as gt_dauky, sum(sl_nhap) as sl_nhap, sum (gt_nhap) as gt_nhap
                    FROM 
                    (SELECT a.product_id prdid, c.uom_id uomid, sum(abs(a.quantity/coalesce(f.factor,1))) sl_nhap, sum(a.balance) gt_nhap
                    FROM account_move_line a, product_product b, product_template c, account_move d, uom_uom f
                    WHERE a.date >= %s
                    AND a.date <= %s
                    AND a.account_id = %s
                    AND a.x_type_transfer = 'in' AND a.move_id = d.id
                    AND a.product_id = b.id AND b.product_tmpl_id = c.id
                    AND a.product_uom_id = f.id AND d.state = 'posted'
                    and d.move_type != 'in_refund'
                    and c.x_sequence_calculate = %s
                    GROUP BY a.product_id, c.uom_id
                    UNION ALL 
                    SELECT a.product_id prdid, c.uom_id uomid, -sum(abs(a.quantity/coalesce(f.factor,1))) sl_nhap, sum(a.balance) gt_nhap
                    FROM account_move_line a, product_product b, product_template c, account_move d, uom_uom f
                    WHERE a.date >= %s
                    AND a.date <= %s
                    and a.account_id = %s
                    AND a.x_type_transfer = 'in' AND a.move_id = d.id
                    AND a.product_id = b.id AND b.product_tmpl_id = c.id
                    AND a.product_uom_id = f.id AND d.state = 'posted'
                    and d.move_type = 'in_refund'
                    and c.x_sequence_calculate = %s
                    GROUP BY a.product_id, c.uom_id) b 
                    GROUP BY b.prdid, b.uomid) a
                    GROUP BY a.prdid,  a.uomid
            """
            self._cr.execute(sql, (
                self.id, self.env.user.id, self.env.user.id, str(account), str(date_from), sequence,
                str(date_from), str(date_to), str(account), sequence, str(date_from), str(date_to), str(account), sequence))
            self._cr.commit()
            self._get_detail(account, sequence)

    def update_pos_order_line(self, date_from, date_to):
        self.ensure_one()
        self.activity = 'Updated Pos Order Line'
        self._check_fiscalyear_lock_date()
        sql="""
            Update pos_order_line a
            set x_cost_price = c.standard_price, x_margin = (a.price_subtotal - (a.qty*c.standard_price) - a.x_is_price_promotion- a.amount_promotion_loyalty- a.amount_promotion_total)
            FROM pos_order b, cost_price_period_line c 
            WHERE
            a.order_id = b.id 
            and a.product_id = c.product_id 
            and b.x_pos_order_refund_id is NULL 
            AND (b.date_order + INTERVAL '7 hours')::date >= '%s' AND (b.date_order + INTERVAL '7 hours')::date <= '%s'
            and c.period_id = %s;
        """
        self._cr.execute(sql % (str(date_from), str(date_to), str(self.id)))

    def update_account_move_inventory_valuation(self, date_from, date_to, sequence):
        self.ensure_one()
        self.activity = 'Updated account move'
        self._check_fiscalyear_lock_date()
        sql = """
                UPDATE stock_valuation_layer a
                SET unit_cost = e.standard_price, value = round((-1) * c.product_qty * e.standard_price)
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and c.purchase_line_id is NULL
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s;

                UPDATE stock_move a
                SET x_unit_cost = e.standard_price, x_value = (-1) * round(a.product_qty * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.product_id = e.product_id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.purchase_line_id is NULL
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s;

                UPDATE stock_move_line a
                SET x_unit_cost = e.standard_price, x_value = (-1) * round(a.qty_done * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, stock_move b, product_product pp, product_template pt
                WHERE a.product_id = e.product_id
                and a.move_id = b.id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and b.purchase_line_id is NULL 
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s;

                UPDATE account_move_line a
                SET credit = round(abs(c.product_qty * e.standard_price)), balance = (-1) * round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = (-1) * round(abs(c.product_qty * e.standard_price)), debit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.move_id = b.id 
                and c.purchase_line_id is NULL
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s
                AND a.account_id = (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move_line a
                SET debit = round(abs(c.product_qty * e.standard_price)), balance = round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = round(abs(c.product_qty * e.standard_price)), credit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.move_id = b.id 
                and c.purchase_line_id is NULL
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s
                AND a.account_id != (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move a
                SET amount_total = round(c.product_qty * e.standard_price), amount_total_signed = round(c.product_qty * e.standard_price), x_note_update = '%s'
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.stock_move_id = c.id 
                and c.purchase_line_id is NULL
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                and pt.x_sequence_calculate = %s
                AND e.period_id = %s;
            """
        self._cr.execute(
            sql % (str(date_from), str(date_to),sequence, str(self.id),
                   str(date_from), str(date_to),sequence, str(self.id),
                   str(date_from), str(date_to),sequence, str(self.id),self.name,
                   str(date_from), str(date_to),sequence, str(self.id),self.name,
                   str(date_from), str(date_to),sequence, str(self.id),self.name,
                   str(date_from), str(date_to),sequence, str(self.id)))
        self._cr.commit()

    def update_account_move_inventory_valuation_total(self, date_from, date_to):
        self.ensure_one()
        self.activity = 'Updated account move out'
        self._check_fiscalyear_lock_date()
        sql = """
                UPDATE stock_valuation_layer a
                SET unit_cost = e.standard_price, value = round((-1) * c.product_qty * e.standard_price)
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and c.purchase_line_id is NULL
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE stock_move a
                SET x_unit_cost = e.standard_price, x_value = (-1) * round(a.product_qty * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.product_id = e.product_id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.purchase_line_id is NULL
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE stock_move_line a
                SET x_unit_cost = e.standard_price, x_value = (-1) * round(a.qty_done * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, stock_move b, product_product pp, product_template pt
                WHERE a.product_id = e.product_id
                and a.move_id = b.id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and b.purchase_line_id is NULL 
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE account_move_line a
                SET credit = round(abs(c.product_qty * e.standard_price)), balance = (-1) * round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = (-1) * round(abs(c.product_qty * e.standard_price)), debit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.move_id = b.id 
                and c.purchase_line_id is NULL
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s
                AND a.account_id = (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move_line a
                SET debit = round(abs(c.product_qty * e.standard_price)), balance = round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = round(abs(c.product_qty * e.standard_price)), credit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.move_id = b.id 
                and c.purchase_line_id is NULL
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s
                AND a.account_id != (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move a
                SET amount_total = round(c.product_qty * e.standard_price), amount_total_signed = round(c.product_qty * e.standard_price), x_note_update = '%s'
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt
                WHERE a.stock_move_id = c.id 
                and c.purchase_line_id is NULL
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage = 'internal' AND kn.usage != 'internal'
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;
            """
        self._cr.execute(
            sql % (str(date_from), str(date_to), str(self.id),
                   str(date_from), str(date_to), str(self.id),
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id)))
        self._cr.commit()

    def update_account_move_inventory_valuation_refund_pos(self, date_from, date_to):
        self.ensure_one()
        self.activity = 'Updated account move'
        self._check_fiscalyear_lock_date()
        sql = """
                UPDATE stock_valuation_layer a
                SET unit_cost = e.standard_price, value = round(c.product_qty * e.standard_price)
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt, stock_picking f
                WHERE a.stock_move_id = c.id 
                AND c.product_id = e.product_id
                and c.picking_id = f.id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and f.pos_session_id is NOT NULL
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE stock_move a
                SET x_unit_cost = e.standard_price, x_value = round(a.product_qty * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt, stock_picking f
                WHERE a.product_id = e.product_id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                and a.picking_id = f.id
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and f.pos_session_id is NOT NULL
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE stock_move_line a
                SET x_unit_cost = e.standard_price, x_value = round(a.qty_done * e.standard_price)
                FROM cost_price_period_line e, stock_location kx, stock_location kn, stock_move b, product_product pp, product_template pt, stock_picking f
                WHERE a.product_id = e.product_id
                and a.move_id = b.id
                AND a.location_id = kx.id AND a.location_dest_id = kn.id
                and b.picking_id = f.id 
                and f.pos_session_id is not null
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;

                UPDATE account_move_line a
                SET credit = round(abs(c.product_qty * e.standard_price)), balance = (-1) * round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = (-1) * round(abs(c.product_qty * e.standard_price)), debit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt, stock_picking f
                WHERE a.move_id = b.id 
                and c.picking_id = f.id 
                and f.pos_session_id is not null 
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s
                AND a.account_id != (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move_line a
                SET debit = round(abs(c.product_qty * e.standard_price)), balance = round(abs(c.product_qty * e.standard_price)), 
                            amount_currency = round(abs(c.product_qty * e.standard_price)), credit = 0, x_note_update = '%s'
                FROM account_move b, stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt, stock_picking f
                WHERE a.move_id = b.id 
                and c.picking_id = f.id 
                and f.pos_session_id is not null 
                AND b.state = 'posted' AND b.stock_move_id = c.id 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and a.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s
                AND a.account_id = (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property WHERE name='property_stock_valuation_account_id' 
                                        AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                        WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT);

                UPDATE account_move a
                SET amount_total = round(c.product_qty * e.standard_price), amount_total_signed = round(c.product_qty * e.standard_price), x_note_update = '%s'
                FROM stock_move c, cost_price_period_line e, stock_location kx, stock_location kn, product_product pp, product_template pt, stock_picking f
                WHERE a.stock_move_id = c.id 
                and c.picking_id = f.id 
                and f.pos_session_id is not null 
                AND c.product_id = e.product_id
                AND c.location_id = kx.id AND c.location_dest_id = kn.id
                AND (c.date + INTERVAL '7 hours')::date >= '%s' AND (c.date + INTERVAL '7 hours')::date <= '%s'
                AND c.state = 'done' AND kx.usage != 'internal' AND kn.usage = 'internal'
                and c.product_id = pp.id 
                and pp.product_tmpl_id = pt.id
                AND e.period_id = %s;
            """
        self._cr.execute(
            sql % (str(date_from), str(date_to), str(self.id),
                   str(date_from), str(date_to), str(self.id),
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id), self.name,
                   str(date_from), str(date_to), str(self.id)))
        self._cr.commit()

    def _get_account_asset(self, date_from, date_to):
        try:
            query = """
                    SELECT DISTINCT d.asset_id
                    FROM account_move_line a, account_move b, stock_move c, asset_move_line_rel d, cost_price_period_line e
                    WHERE 
                    a.move_id = b.id 
                    and b.stock_move_id = c.id 
                    and c.state = 'done' 
                    and a.id = d.line_id
                    and (c.date + INTERVAL '7 hours')::date >= '%s'
                    and (c.date + INTERVAL '7 hours')::date <= '%s'
                    and a.product_id = e.product_id 
                    and e.period_id = %s;
            """ % (date_from, date_to, self.id)
            self._cr.execute(query)
            values = self._cr.fetchall()
            return values
        except Exception as e:
            raise ValidationError(e)

    def update_account_asset(self, date_from, date_to):
        self.ensure_one()
        self.activity = 'Updated account assets'
        self._check_fiscalyear_lock_date()
        asset_ids = self._get_account_asset(date_from, date_to)
        if not asset_ids:
            return
        if asset_ids:
            for asset in asset_ids:
                asset_id = self.env['account.asset'].sudo().search([('id', '=', asset[0])])
                if asset_id:
                    if asset_id.state == 'open':
                        asset_id.set_to_draft()
                        asset_id._compute_value()
                        asset_id.validate()

    def _get_product_process(self, date_from, date_to, sequence):
        try:
            query = """
                    SELECT DISTINCT c.id
                    FROM product_process_detail a, product_process_line b, product_process c, product_product d, product_template e
                    WHERE 
                    a.from_process_id = b.id 
                    and b.process_id = c.id 
                    and a.product_id = d.id 
                    and d.product_tmpl_id = e.id 
                    and c.state = 'done'
                    and (c.date + INTERVAL '7 hours')::date >= '%s' and (c.date + INTERVAL '7 hours')::date <= '%s'
                    and e.x_sequence_calculate = %s;
            """ % (date_from, date_to, sequence)
            self._cr.execute(query)
            values = self._cr.fetchall()
            return values
        except Exception as e:
            raise ValidationError(e)

    # update cacs but toan nhap kho che bien
    def update_account_move_inventory_valuation_process(self, date_from, date_to, sequence):
        self.ensure_one()
        self.activity = 'Updated account move process'
        self._check_fiscalyear_lock_date()
        product_process_ids = self._get_product_process(date_from, date_to, sequence)
        if not product_process_ids:
            return
        move_list = []
        if product_process_ids:
            for record in product_process_ids:
                process_id = self.env['product.process'].sudo().search([('id', '=', record[0])])
                move_vals = process_id._action_compare_cost()
                if move_vals:
                    move_list += move_vals
        if not move_list:
            return
        move_list = ','.join([str(idd) for idd in move_list])
        sql = f'''
            UPDATE stock_valuation_layer a
            SET unit_cost = c.x_unit_cost, value = c.x_value
            FROM stock_move c
            WHERE a.stock_move_id = c.id 
            AND c.id = any(string_to_array('{move_list}', ',')::INTEGER[]);

            UPDATE stock_move_line a
            SET x_unit_cost = c.x_unit_cost, x_value = c.x_value/c.product_uom_qty * qty_done
            FROM stock_move c
            WHERE a.move_id = c.id 
            AND c.id = any(string_to_array('{move_list}', ',')::INTEGER[]);
            --nhap
            UPDATE account_move_line a
            SET debit = abs(c.x_value), balance = abs(c.x_value), 
                                    amount_currency = abs(c.x_value), credit = 0
            FROM account_move b, stock_move c
            WHERE a.move_id = b.id 
            AND b.stock_move_id = c.id 
            AND a.account_id = (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property 
                                WHERE name='property_stock_valuation_account_id' 
                                AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT)
            AND c.id = any(string_to_array('{move_list}', ',')::INTEGER[]);

            UPDATE account_move_line a
            SET credit = abs(c.x_value), balance = (-1) * abs(c.x_value), 
                                    amount_currency = (-1) * abs(c.x_value), debit = 0
            FROM account_move b, stock_move c
            WHERE a.move_id = b.id 
            AND b.stock_move_id = c.id 
            AND a.account_id != (SELECT split_part(value_reference, ',',2)::INTEGER FROM ir_property 
                                 WHERE name='property_stock_valuation_account_id' 
                                 AND company_id = c.company_id AND res_id = 'product.category,'||(SELECT pt.categ_id FROM product_product p, product_template pt
                                 WHERE p.product_tmpl_id = pt.id AND p.id = c.product_id)::TEXT)
            AND c.id = any(string_to_array('{move_list}', ',')::INTEGER[]);

            UPDATE account_move a
            SET amount_total = c.x_value, amount_total_signed = c.x_value
            FROM stock_move c
            WHERE a.stock_move_id = c.id
            AND c.id = any(string_to_array('{move_list}', ',')::INTEGER[]);
        '''
        self._cr.execute(sql)
        self._cr.commit()

    # update cac but toan nhap kho khi chuyen kho no bo
    def update_account_move_inventory_valuation_transfer(self, date_from, date_to):
        self.ensure_one()
        self.activity = 'Updated account move transfer'
        self._check_fiscalyear_lock_date()
        sql = """
                UPDATE stock_move a
                SET x_unit_cost = e.standard_price, x_value = abs(e.standard_price*a.product_qty)
                FROM cost_price_period_line e, stock_transfer b
                WHERE a.picking_id = b.out_picking_id
                AND a.product_id = e.product_id
                and e.period_id = %s
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done';
                
                UPDATE stock_move a
                SET x_unit_cost = e.standard_price, x_value = abs(e.standard_price*a.product_qty)
                FROM cost_price_period_line e, stock_transfer b
                WHERE a.picking_id = b.in_picking_id
                AND a.product_id = e.product_id
                and e.period_id = %s
                AND (a.date + INTERVAL '7 hours')::date >= '%s' AND (a.date + INTERVAL '7 hours')::date <= '%s'
                AND a.state = 'done';

                UPDATE stock_move_line aa
                SET x_unit_cost = e.standard_price, x_value = abs(aa.qty_done * e.standard_price)
                FROM stock_move a, cost_price_period_line e, stock_transfer b
                WHERE aa.move_id = a.id
                AND a.picking_id = b.out_picking_id
                AND a.product_id = e.product_id
                and e.period_id = %s
                AND (aa.date + INTERVAL '7 hours')::date >= '%s' AND (aa.date + INTERVAL '7 hours')::date <= '%s'
                AND aa.state = 'done';
                
                UPDATE stock_move_line aa
                SET x_unit_cost = e.standard_price, x_value = abs(aa.qty_done * e.standard_price)
                FROM stock_move a, cost_price_period_line e, stock_transfer b
                WHERE aa.move_id = a.id
                AND a.picking_id = b.in_picking_id
                AND a.product_id = e.product_id
                and e.period_id = %s
                AND (aa.date + INTERVAL '7 hours')::date >= '%s' AND (aa.date + INTERVAL '7 hours')::date <= '%s'
                AND aa.state = 'done';
            """
        self._cr.execute(
            sql % (self.id, str(date_from), str(date_to), self.id, str(date_from), str(date_to), self.id, str(date_from), str(date_to),
                   self.id, str(date_from), str(date_to)))

    def _check_fiscalyear_lock_date(self):
        for move in self:
            lock_date = move.company_id._get_user_fiscal_lock_date()
            if move.date_to <= lock_date:
                if self.user_has_groups('account.group_account_manager'):
                    message = _("You cannot add/modify entries prior to and inclusive of the lock date %s.", format_date(self.env, lock_date))
                else:
                    message = _("You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role", format_date(self.env, lock_date))
                raise UserError(message)
        return True

    def update_standard_price(self):
        self.ensure_one()
        self.activity = 'Updated standard price'
        for line in self.period_lines:
            line.product_id.standard_price = line.standard_price

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def _is_number(self, name):
        try:
            float(name)
            return True
        except ValueError:
            return False

    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0','')
                #product_code = str(product_code).split('.')[0]
                if self._is_number(product_code):
                    product_code = str(int(product_code)).upper()
                else:
                    product_code = str(product_code).upper()
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                standard_price = sheet.cell(index, 2).value
                if product_id:
                    line_obj = self.env['cost.price.period.line'].search(
                        [('period_id', '=', self.id),
                         ('product_id', '=', product_id.id)], limit=1)
                    if not line_obj:
                        move_vals = {
                            'product_id': product_id.id,
                            'standard_price': standard_price,
                            'period_id': self.id,
                        }
                        line_id = self.env['cost.price.period.line'].create(move_vals)
                    else:
                        raise except_orm('Cảnh báo!',
                                         ("Trong file bị trùng mã SP " + str(
                                             product_code)))
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_account_cost_price/static/template/mau_cap_nhat_gia_von.xlsx',
            "target": "_parent",
        }

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_account_cost_price.export_cost_price_period/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }


class CostPricePeriodLine(models.Model):
    _name = 'cost.price.period.line'

    period_id = fields.Many2one('cost.price.period', string="Period Cost", ondelete='cascade', index=True)
    date = fields.Date(string="Date")
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string="Date To")
    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    method_add = fields.Selection([('manual', 'Manual'), ('auto', 'Auto')], default='manual', string="Method Add")
    # Previous
    qty_initial = fields.Float(string="Initial Qty", digits='Product Unit of Measure')
    value_initial = fields.Float(string="Initial Value")
    # Period
    qty_in = fields.Float(string="Quantity in", digits='Product Unit of Measure')
    value_in = fields.Float(string="Value in")
    # Cost of Goods
    standard_price = fields.Float(string="Standard Price")
    lines = fields.One2many('cost.price.period.detail', 'period_line_id', 'Lines')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id.id:
            # Check cost method and valuation stock
            variant = self.product_id
            if variant.type == 'product':
                self.uom_id = self.product_id.uom_id.id
            else:
                self.product_id = None
                raise UserError(
                    _("Product must be Average in Cost Method and Manual in Valuation Stock and 'product' in Product Type "))


class CostPricePeriodDetail(models.Model):
    _name = 'cost.price.period.detail'

    period_line_id = fields.Many2one('cost.price.period.line', 'Period Line', ondelete='cascade', index=True)
    account_move_name = fields.Char('Account move name')
    qty = fields.Float('Quantity')
    value = fields.Float('Value')
    description = fields.Text('Description')
