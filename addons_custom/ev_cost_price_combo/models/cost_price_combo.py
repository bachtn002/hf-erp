from odoo import fields, models, api, _

from odoo.exceptions import UserError, ValidationError


class CostPriceCombo(models.Model):
    _name = 'cost.price.combo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Name', default='New')
    account_fiscal_month_id = fields.Many2one('account.fiscal.month', 'Accounting Period')
    date = fields.Date(string='Date', default=fields.Date.today())
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    line_ids = fields.One2many('cost.price.combo.line', 'cost_price_combo_id', string='Cost Price Combo Line')

    state = fields.Selection(
        [('draft', 'Draft'), ('calculate', 'Calculate'), ('confirm', 'Confirm'), ('done', 'Done'),
         ('cancel', 'Cancel')], string="State",
        default='draft', track_visibility='always')

    def action_calculate(self):
        try:
            product_combo = self.env['product.product'].search([('x_is_combo', '=', True)])
            lines = []
            if product_combo:
                for product in product_combo:
                    vals = {
                        'product_id': product.id,
                        'uom_id': product.product_tmpl_id.uom_id.id,
                        'cost_price': 0,
                        'cost_price_combo_id': self.id,
                    }
                    lines.append((0, 0, vals))

            self.line_ids = lines

            for line in self.line_ids:
                product_combos = self.env['product.combo'].search(
                    [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                detail_ids = []
                cost_price = 0
                if product_combos:
                    for detail in product_combos:
                        product_id = self.env['product.product'].search([('id', '=', detail.product_ids.id),
                                                                         ('active', '=', True)], limit=1)
                        unit_cost = product_id.product_tmpl_id.standard_price * detail.no_of_items
                        cost_price += unit_cost
                        vals = {
                            'product_id': product_id.id,
                            'quantity': detail.no_of_items,
                            'cost_price': product_id.product_tmpl_id.standard_price,
                            'cost_price_combo_line_id': line.id
                        }
                        detail_ids.append((0, 0, vals))
                line.detail_ids = detail_ids
                line.cost_price = cost_price
            self.state = 'calculate'

        except Exception as e:
            raise ValidationError(e)

    def action_confirm(self):
        try:
            date_start = self.account_fiscal_month_id.date_from
            date_end = self.account_fiscal_month_id.date_to
            for line in self.line_ids:
                for detail in line.detail_ids:
                    query_detail = self._sql_update_detail(detail.product_id.id, date_start, date_end)
                    self._cr.execute(query_detail)

                query_line = self._sql_update_line(line.cost_price, line.product_id.id, date_start, date_end)
                self._cr.execute(query_line)

                line.product_id.product_tmpl_id.standard_price = line.cost_price
            self.state = 'done'
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cost.price.combo')
        return super(CostPriceCombo, self).create(vals)

    def _sql_update_detail(self, product_id, date_start, date_end):
        return """
            update pos_order_line
            set x_cost_price = 0,
                x_margin     = 0
            where id in (
                select a.id
                from pos_order_line a
                         join pos_order b on b.id = a.order_id
                where (b.date_order + INTERVAL '7 hours')::date >= '%s'
                  and (b.date_order + INTERVAL '7 hours')::date <= '%s'
                  and a.product_id = %s
                  and a.is_combo_line = True
            )
        """ % (date_start, date_end, product_id)

    def _sql_update_line(self, cost_price, product_id, date_start, date_end):
        return """
            update pos_order_line
            set x_cost_price = %s,
                x_margin     = pos_order_line.price_subtotal_incl - pos_order_line.x_is_price_promotion -
                               pos_order_line.amount_promotion_loyalty -
                               pos_order_line.amount_promotion_total - %s
            where id in (
                select a.id
                from pos_order_line a
                         join pos_order b on b.id = a.order_id
                where (b.date_order + INTERVAL '7 hours')::date >= '%s'
                  and (b.date_order + INTERVAL '7 hours')::date <= '%s'
                  and a.product_id = %s
            )
        """ % (cost_price, cost_price, date_start, date_end, product_id)
