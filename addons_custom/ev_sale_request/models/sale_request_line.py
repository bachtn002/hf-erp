from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class SaleRequestLine(models.Model):
    _name = 'sale.request.line'
    _inherit = [
        'mail.thread'
    ]
    sale_request_id = fields.Many2one(comodel_name='sale.request', string='Sale Request Reference',
                                      ondelete='cascade')
    request_id = fields.Char(related='sale_request_id.name', string='Request Name')
    product_id = fields.Many2one('product.product', string='Product', change_default=True, required=1)
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    qty_apply = fields.Float(string='Apply quantity', digits='Product Unit of Measure', default=0, readonly=1)
    product_uom = fields.Many2one('uom.uom', string='Uom', related='product_id.uom_id')
    supply_type = fields.Selection([
        ('warehouse', 'Warehouse'),
        ('purchase', 'Purchase'),
        ('stop_supply', 'Stop Supply')],
        string='Supply Warehouse', readonly=True)

    check_general = fields.Boolean('Check General', default=False)
    state_general = fields.Selection([
        ('draft', 'Warehouse'),
        ('done', 'Purchase')],
        default='draft', string='Supply Warehouse', readonly=True)
    note = fields.Text('Note')

    @api.model
    def create(self, vals):
        try:
            sale_request = self.env['sale.request'].search([('id', '=', vals['sale_request_id'])], limit=1)
            product = self.env['product.product'].search([('id', '=', vals['product_id'])], limit=1)
            if sale_request.warehouse_id.x_is_supply_warehouse:
                query_warehouse = self._sql_warehouse(sale_request.warehouse_id.id, vals['product_id'])
                self._cr.execute(query_warehouse)
                warehouse = self._cr.dictfetchone()
                if warehouse:
                    if warehouse['supply_type'] == 'stop_supply':
                        vals['supply_type'] = 'stop_supply'
                    else:
                        vals['supply_type'] = 'purchase'
                else:
                    if self.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                        vals['supply_type'] = 'stop_supply'
                    else:
                        vals['supply_type'] = 'purchase'
            else:
                query_region = self._sql_region(sale_request.warehouse_id.x_stock_region_id.id, vals['product_id'])
                self._cr.execute(query_region)
                region = self._cr.dictfetchone()
                if region:
                    vals['supply_type'] = region['supply_type']
                else:
                    query_warehouse = self._sql_warehouse(sale_request.warehouse_id.id, vals['product_id'])
                    self._cr.execute(query_warehouse)
                    warehouse = self._cr.dictfetchone()
                    if warehouse:
                        vals['supply_type'] = warehouse['supply_type']
                    else:
                        vals['supply_type'] = product.x_supply_type
            return super(SaleRequestLine, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def write(self, vals):
        try:
            try:
                if not vals['product_id']:
                    return super(SaleRequestLine, self).write(vals)
            except:
                return super(SaleRequestLine, self).write(vals)
            sale_request = self.env['sale.request'].search([('id', '=', self.sale_request_id.id)], limit=1)
            product = self.env['product.product'].search([('id', '=', vals['product_id'])], limit=1)
            if sale_request.warehouse_id.x_is_supply_warehouse:
                vals['supply_type'] = 'purchase'
                query_warehouse = self._sql_warehouse(sale_request.warehouse_id.id, vals['product_id'])
                self._cr.execute(query_warehouse)
                warehouse = self._cr.dictfetchone()
                if warehouse:
                    if warehouse['supply_type'] == 'stop_supply':
                        vals['supply_type'] = 'stop_supply'
                    else:
                        vals['supply_type'] = 'purchase'
                else:
                    if self.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                        vals['supply_type'] = 'stop_supply'
                    else:
                        vals['supply_type'] = 'purchase'
            else:
                query_region = self._sql_region(sale_request.warehouse_id.x_stock_region_id.id, vals['product_id'])
                self._cr.execute(query_region)
                region = self._cr.dictfetchone()
                if region:
                    vals['supply_type'] = region['supply_type']
                else:
                    query_warehouse = self._sql_warehouse(sale_request.warehouse_id.id, vals['product_id'])
                    self._cr.execute(query_warehouse)
                    warehouse = self._cr.dictfetchone()
                    if warehouse:
                        vals['supply_type'] = warehouse['supply_type']
                    else:
                        vals['supply_type'] = product.x_supply_type
            return super(SaleRequestLine, self).write(vals)
        except Exception as e:
            raise ValidationError(e)

    def get_contract_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'pur_request/static/xls/imp_phieuyeucauhanghoa.xlsx'
        }

    def unlink(self):
        return super(SaleRequestLine, self).unlink()

    def _sql_warehouse(self, warehouse_id, product_id):
        return """
            SELECT b.supply_type
            from supply_adjustment_warehouse a
                     join supply_adjustment b on b.id = a.supply_adjustment_id
            where a.warehouse_id = %s
              and supply_adjustment_id in (select supply_adjustment_id from supply_adjustment_product where product_id = %s)
            order by b.create_date desc
            limit 1
        """ % (warehouse_id, product_id)

    def _sql_region(self, region_id, product_id):
        return """
            SELECT b.supply_type
            from supply_adjustment_region a
                     join supply_adjustment b on b.id = a.supply_adjustment_id
            where a.region_id = %s
              and supply_adjustment_id in (select supply_adjustment_id from supply_adjustment_product where product_id = %s)
        """ % (region_id, product_id)
