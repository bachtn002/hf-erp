from odoo import fields, models, api, _
from datetime import datetime

from odoo.exceptions import UserError, _logger
from odoo.tools import float_compare
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class InventoryCheck(models.Model):
    _inherit = 'stock.inventory'

    x_analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('confirm', 'In Progress'),
        ('confirm_warehouse', 'Warehouse Confirm'),
        ('queued', 'Queued'),
        ('done', 'Validated'),
        ('cancel', 'Cancelled'),

    ])
    x_address_company = fields.Char(compute='_compute_address_company')
    x_location_id = fields.Many2one('stock.location', 'Stock Location')
    x_category_ids = fields.Many2many('product.category', string='Product Category')
    x_inventory_group_ids = fields.One2many('stock.inventory.group', 'stock_inventory_id', string='Inventory Group')
    x_products_invisible = fields.Boolean(default=False)
    exhausted = fields.Boolean(
        'Include Exhausted Products', readonly=True,
        states={'draft': [('readonly', False)]}, default=True,
        help="Include also products with quantity of 0")
    accounting_date = fields.Date(
        'Accounting Date', default=fields.Datetime.today,
        help="Date at which the accounting entries will be created"
             " in case of automated inventory valuation."
             " If empty, the inventory date will be used.")

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/xlsx/ev_inventory_check.export_stock_inventory/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.onchange('x_location_id')
    def onchange_location(self):
        if self.x_location_id:
            self.location_ids = self.x_location_id

    @api.onchange('x_category_ids', 'x_inventory_group_ids')
    def onchange_category_inventory_group(self):
        if self.x_category_ids or self.x_inventory_group_ids:
            self.x_products_invisible = True
            product_ids = self.env['product.product'].search(['|', ('categ_id', 'in', self.x_category_ids.ids), (
                'product_tmpl_id', 'in', self.x_inventory_group_ids.product_ids.ids), ('type','=','product')])
            if product_ids:
                self.product_ids = product_ids
        elif not self.x_category_ids and not self.x_inventory_group_ids:
            self.x_products_invisible = False

    @api.depends('company_id')
    def _compute_address_company(self):
        for record in self:
            record.x_address_company = 'Địa chỉ: '
            for r in record.company_id:
                if r.street:
                    record.x_address_company = record.x_address_company + ' ' + r.street
                if r.street2:
                    record.x_address_company = record.x_address_company + ' ' + r.street2
                if r.city:
                    record.x_address_company = record.x_address_company + ' ' + r.city
                if r.state_id:
                    record.x_address_company = record.x_address_company + ' ' + r.state_id.name
                if r.country_id:
                    record.x_address_company = record.x_address_company + ' ' + r.country_id.name

    def action_start(self):
        self.ensure_one()
        self._action_start()
        self._check_company()
        return self.action_open_inventory_lines()

    def _action_start(self):
        """ Confirms the Inventory Adjustment and generates its inventory lines
        if its state is draft and don't have already inventory lines (can happen
        with demo data or tests).
        """
        for inventory in self:
            if inventory.state != 'draft':
                continue
            analytic_id = False
            for location in inventory.location_ids:
                warehouse_id = location.x_warehouse_id
                if warehouse_id:
                    # pos_shop = self.env['pos.shop'].search([('warehouse_id', '=', warehouse_id.id)], limit=1)
                    # if pos_shop:
                    analytic_id = warehouse_id.x_analytic_account_id
            vals = {
                'state': 'confirm',
                'date': fields.Datetime.now(),
                'x_analytic_account_id': analytic_id.id if analytic_id != False else None
            }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)

    def _action_done_store(self):
        negative = next((line for line in self.mapped('line_ids') if
                         line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_(
                'You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s',
                negative.product_id.display_name,
                negative.product_qty
            ))
        self.write({'state': 'confirm_warehouse', 'date': datetime.now()})
        return True

    def action_validate_queue(self):
        self.write({'state': 'queued'})
        self.sudo().with_delay(channel='root.action_done_stock_inventory',
                               max_retries=3)._action_done()

    def _action_done(self):
        negative = next((line for line in self.mapped('line_ids') if
                         line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_(
                'You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s',
                negative.product_id.display_name,
                negative.product_qty
            ))
        self.action_check()
        self.write({'state': 'done', 'date': datetime.now()})
        self.post_inventory()
        stock_move = self.env['stock.move'].search([('inventory_id', '=', self.id)], limit=1)
        if stock_move:
            self._update_analytic_account()
            if self.accounting_date:
                self._update_date_stock_move()
        return True

    def _update_date_stock_move(self):
        accounting_date_tmp = str(self.accounting_date) + ' 16:59:00'
        accounting_date_tmp_obj = datetime.strptime(accounting_date_tmp, '%Y-%m-%d %H:%M:%S')
        sql = """
            UPDATE stock_move a 
            SET date = '%s'
            where inventory_id = %s;
            UPDATE stock_move_line a 
            SET date = '%s'
            from stock_move b
            where 
            a.move_id = b.id
            and b.inventory_id = %s;
        """
        self._cr.execute(sql % (accounting_date_tmp_obj, self.id, accounting_date_tmp_obj, self.id))

    def action_validate(self):
        if not self.exists():
            return
        if self.state == 'confirm_warehouse':
            return

        self.ensure_one()
        if self.state != 'confirm':
            raise UserError(_(
                "You can't validate the inventory '%s', maybe this inventory "
                "has been already validated or isn't ready.", self.name))
        for line in self.line_ids:
            if line.product_qty < 0:
                raise UserError(_('Product quanty must greater than 0'))
            else:
                uom_qty = float_round(line.product_qty, precision_rounding=line.product_uom_id.rounding,
                                      rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.product_qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                defined on the unit of measure "%s". Please change the quantity done or the \
                                rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.product_uom_id.name))
        inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot',
                                                                                     'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
        lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1,
                                                               precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
        if inventory_lines and not lines:
            wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in
                         inventory_lines.mapped('product_id')]
            wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
            return {
                'name': _('Tracked Products in Inventory Adjustment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_model': 'stock.track.confirmation',
                'target': 'new',
                'res_id': wiz.id,
            }
        self.state = 'confirm_warehouse'
        return True

    def _update_analytic_account(self):
        if self.x_analytic_account_id:
            sql = """
                UPDATE account_move_line a 
                SET analytic_account_id = %s
                where exists (select 1 
                FROM account_move b, stock_move c
                WHERE
                a.move_id = b.id 
                and b.stock_move_id = c.id 
                and c.inventory_id = %s);
            """
            self._cr.execute(sql % (self.x_analytic_account_id.id, self.id))

    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        context = {
            'default_is_editable': True,
            'default_inventory_id': self.id,
            'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        if self.location_ids:
            context['default_location_id'] = self.location_ids[0].id
            if len(self.location_ids) == 1:
                if not self.location_ids[0].child_ids:
                    context['readonly_location_id'] = True

        if self.product_ids:
            # no_create on product_id field
            action['view_id'] = self.env.ref('stock.stock_inventory_line_tree_no_product_create').id
            if len(self.product_ids) == 1:
                context['default_product_id'] = self.product_ids[0].id
        else:
            # no product_ids => we're allowed to create new products in tree
            action['view_id'] = self.env.ref('stock.stock_inventory_line_tree').id

        action['context'] = context
        action['domain'] = domain
        return action

    def action_return_inventory(self):
        self.state = 'confirm'

    def action_cancel_inventory(self):
        self.state = 'cancel'

    def action_print_stock_inventory(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_inventory_check.report_template_stock_inventory_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def action_print_stock_inventory_draft(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_inventory_check.report_template_stock_inventory_draft_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.onchange('x_location_id')
    def check_location(self):
        if self.x_location_id:
            inventorys = self.env['stock.inventory'].search([('x_location_id', '=', self.x_location_id.id)])
            if inventorys:
                for record in inventorys:
                    if record.x_location_id.id == self.x_location_id.id and record.state not in ('done', 'cancel'):
                        raise UserError(_('Location processing inventory'))
