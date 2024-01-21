# -*- coding: utf-8 -*-
from datetime import datetime, date

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError

from dateutil.relativedelta import relativedelta


class SaleRequest(models.Model):
    _inherit = 'sale.request'

    check_consumption_forecast = fields.Boolean("Check Consumption Forecast", default=False)
    date_request = fields.Date('Request Date', default=lambda x: datetime.today() + relativedelta(hours=7),
                               required=True)

    @api.onchange('warehouse_id')
    def _check_consumption_forecast(self):
        try:
            if self.warehouse_id:
                record_id = str(self.id).split('_')[1]
                check_number = self.check_number(record_id)
                if not check_number:
                    sale_request = False
                    warehouse = False
                else:
                    sale_request = self.search([('id', '=', record_id)])
                    warehouse = sale_request.warehouse_id

                print(self.warehouse_id, warehouse)
                if self.warehouse_id == warehouse:
                    print('check', self.check_consumption_forecast)
                    self.sale_request_line = sale_request.sale_request_line
                    self.check_consumption_forecast = sale_request.check_consumption_forecast
                else:
                    self.sale_request_line = None

                    if self.warehouse_id.consumption_forecast == True:
                        self.check_consumption_forecast = True
                    else:
                        self.check_consumption_forecast = False
        except Exception as e:
            raise ValidationError(e)

    def check_number(self, number):
        try:
            int(number)
            return True
        except Exception:
            return False

    def write(self, vals):
        warehouse_id = self.warehouse_id
        if vals.get('warehouse_id'):
            if vals.get('warehouse_id') != warehouse_id.id:
                self.sale_request_line.unlink()
        return super().write(vals)

    def send_sale_request(self):
        try:
            if self.check_consumption_forecast == True:
                raise ValidationError(_("You must have choose consumption_forecast before"))
            else:
                list_product_errors = []
                list_product_purchase_false = []
                for line in self.sale_request_line:
                    if line.supply_type == 'purchase' and not line.product_id.product_tmpl_id.purchase_ok:
                        list_product_purchase_false.append(line.product_id.product_tmpl_id.name)
                    if line.qty < line.moq and line.qty != 0:
                        list_product_errors.append(line.product_id.product_tmpl_id.name)

                mess_error = ' , '.join([str(err) for err in list_product_errors])
                mess_purchase_false = ' , '.join([str(err) for err in list_product_purchase_false])
                if len(mess_purchase_false) != 0:
                    raise UserError(_('Product not purchase ok: (%s)') % str(mess_purchase_false))
                if len(mess_error) != 0:
                    raise UserError(_('Quantity request must be less than MOQ: (%s)') % str(mess_error))
                return super(SaleRequest, self).send_sale_request()
        except Exception as e:
            raise ValidationError(e)

    def action_request_forecast(self):
        try:
            self.check_consumption_forecast = False
            if len(self.sale_request_line) > 0:
                return {
                    'name': _('Notification'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.request.notification',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                }
            else:
                self.action_get_line_forecast()
        except Exception as e:
            raise ValidationError(e)

    def action_get_line_forecast(self):
        try:
            if self.warehouse_id:
                shop_id = self.env['pos.shop'].search([('warehouse_id', '=', self.warehouse_id.id)], limit=1)
                if shop_id:
                    request_forecast = self.env['request.forecast'].sudo().search(
                        [('shop_id', '=', shop_id.id), ('date', '=', self.date_request)])
                    vals = []
                    for line in request_forecast:
                        if line.product_id.product_tmpl_id not in shop_id.product_ids:
                            if not line.product_id.product_tmpl_id.x_is_tools:
                                continue
                        else:
                            if not line.product_id.product_tmpl_id.sale_ok and not line.product_id.product_tmpl_id.x_is_tools:
                                continue
                            if not line.product_id.product_tmpl_id.available_in_pos and line.product_id.product_tmpl_id.sale_ok and not line.product_id.product_tmpl_id.x_is_tools:
                                continue
                        moq = 0
                        supply_type = ''
                        if self.warehouse_id.x_is_supply_warehouse:
                            query_warehouse = self._sql_warehouse(self.warehouse_id.id, line.product_id.id)
                            self._cr.execute(query_warehouse)
                            warehouse = self._cr.dictfetchone()
                            if warehouse:
                                if warehouse['supply_type'] == 'stop_supply':
                                    supply_type = 'stop_supply'
                                else:
                                    supply_type = 'purchase'
                                    moq = line.product_id.product_tmpl_id.x_moq_purchase
                            else:
                                if line.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                                    supply_type = 'stop_supply'
                                else:
                                    supply_type = 'purchase'
                                    moq = line.product_id.product_tmpl_id.x_moq_purchase
                        else:
                            query_region = self._sql_region(self.warehouse_id.x_stock_region_id.id,
                                                            line.product_id.id)
                            self._cr.execute(query_region)
                            region = self._cr.dictfetchone()
                            if region:
                                if region['supply_type'] == 'warehouse':
                                    supply_type = 'warehouse'
                                    moq = line.product_id.product_tmpl_id.x_moq_warehouse
                                elif region['supply_type'] == 'purchase':
                                    supply_type = 'purchase'
                                    moq = line.product_id.product_tmpl_id.x_moq_purchase
                                elif region['supply_type'] == 'stop_supply':
                                    supply_type = 'stop_supply'
                            else:
                                query_warehouse = self._sql_warehouse(self.warehouse_id.id, line.product_id.id)
                                self._cr.execute(query_warehouse)
                                warehouse = self._cr.dictfetchone()
                                if warehouse:
                                    if warehouse['supply_type'] == 'warehouse':
                                        supply_type = 'warehouse'
                                        moq = line.product_id.product_tmpl_id.x_moq_warehouse
                                    elif warehouse['supply_type'] == 'purchase':
                                        supply_type = 'purchase'
                                        moq = line.product_id.product_tmpl_id.x_moq_purchase
                                    elif warehouse['supply_type'] == 'stop_supply':
                                        supply_type = 'stop_supply'
                                else:
                                    if line.product_id.product_tmpl_id.x_supply_type == 'warehouse':
                                        supply_type = 'warehouse'
                                        moq = line.product_id.product_tmpl_id.x_moq_warehouse
                                    elif line.product_id.product_tmpl_id.x_supply_type == 'purchase':
                                        supply_type = 'purchase'
                                        moq = line.product_id.product_tmpl_id.x_moq_purchase
                                    elif line.product_id.product_tmpl_id.x_supply_type == 'stop_supply':
                                        supply_type = 'stop_supply'
                        val = {
                            'product_id': line.product_id.id,
                            'qty': line.predicted_qty,
                            'qty_forecast': line.predicted_qty,
                            'moq': moq,
                            'supply_type': supply_type
                        }
                        vals.append((0, 0, val))
                    self.sale_request_line = None
                    self.sale_request_line = vals if len(vals) >= 1 else None
        except Exception as e:
            raise ValidationError(e)

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

    def action_print_excel(self):
        if self.check_consumption_forecast == True:
            raise ValidationError(_("You must have choose consumption_forecast before"))
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': ('/report/xlsx/sale.request.report/%s' % self.id),
                'target': 'new',
                'res_id': self.id,
            }

    def open_import_stock(self):
        if self.check_consumption_forecast == True:
            raise ValidationError(_("You must have choose consumption_forecast before"))
        else:
            return {
                'name': 'Import file',
                'type': 'ir.actions.act_window',
                'res_model': 'import.xls.wizard.stock',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'current_id': self.id},
            }
