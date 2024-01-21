# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class RPTStockMove(models.TransientModel):
    _name = 'rpt.stock.move'

    name = fields.Char(string='Inventory Report')
    region_ids = fields.Many2many('stock.region', string='Region')
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    type = fields.Selection(
        [('inventory', 'Inventory report'),
         ('general', 'General account of input – output – inventory'),
         ('general_value', 'General account of input – output – inventory value')],
        string='Report Type', default='inventory')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    to_lot = fields.Boolean(string='Get Lot')
    categ_ids = fields.Many2many('product.category', string='Category')
    type_view = fields.Selection([
        ('list', 'List'),
        ('pivot', 'Pivot')],
        string='Report view', default='list')
    x_all_internal = fields.Boolean('All Location Internal')

    @api.onchange('type')
    def onchange_type(self):
        self.x_all_internal = False

    def action_export_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        if self.region_ids:
            location_ids += ','
            warehouse_ids = self.env.user.warehouse_ids
            stock_location_region = self.env['stock.location'].search([('x_region_id', 'in', self.region_ids.ids)])
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_true_ids = []
                    for stock_location in stock_locations:
                        if stock_location.id in stock_location_region.ids:
                            location_true_ids.append(stock_location.id)
                    if location_true_ids:
                        location_ids += ','.join([str(id) for id in location_true_ids])
                    else:
                        raise UserError(_('Location not in region! Please choose location'))
            elif not self.location_ids:
                location_ids += ','.join([str(region) for region in stock_location_region.ids])
        if not self.region_ids and not self.location_ids:
            warehouse_ids = self.env.user.warehouse_ids
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_ids += ','.join([str(id) for id in stock_locations.ids])
            else:
                location_ids = '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        categ_ids = ','.join([str(idd) for idd in self.categ_ids.ids]) if self.categ_ids else '0'

        if self.type == 'inventory':
            if self.type_view == 'pivot':
                report_name = "rpt_stock_move_pivot.rptdesign"
                date_from = self.to_date.strftime('%d/%m/%Y')
            else:
                if self.x_all_internal:
                    report_name = "rpt_stock_move_all.rptdesign"
                    date_from = self.to_date.strftime('%d/%m/%Y')
                else:
                    report_name = "rpt_stock_move.rptdesign"
                    date_from = self.to_date.strftime('%d/%m/%Y')
        elif self.type == 'general':
            report_name = "rpt_stock_move_in_out.rptdesign"
            date_from = self.from_date.strftime('%d/%m/%Y')
        else:
            report_name = "rpt_stock_move_in_out_value.rptdesign"
            date_from = self.from_date.strftime('%d/%m/%Y')

        if self.type == 'general_value':
            if self.user_has_groups('account.group_account_user') or self.user_has_groups(
                    'account.group_account_invoice') or self.user_has_groups(
                'account.group_account_manager') or self.user_has_groups('ev_account_cash_bank.group_account_chief'):
                if self.x_all_internal:
                    location_ids = '0'
                    report_name = "rpt_stock_move_in_out_value_all.rptdesign"
                    date_from = self.from_date.strftime('%d/%m/%Y')
            else:
                raise UserError(_('You can not view report!'))

        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&location_ids': location_ids,
            '&product_ids': product_ids,
            '&categ_ids': categ_ids,
            '&company_id': self.company_id.id,
            '&to_lot': self.to_lot,
        }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

    def action_report_excel(self):

        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        if self.region_ids:
            location_ids += ','
            warehouse_ids = self.env.user.warehouse_ids
            stock_location_region = self.env['stock.location'].search([('x_region_id', 'in', self.region_ids.ids)])
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_true_ids = []
                    for stock_location in stock_locations:
                        if stock_location.id in stock_location_region.ids:
                            location_true_ids.append(stock_location.id)
                    if location_true_ids:
                        location_ids += ','.join([str(id) for id in location_true_ids])
                    else:
                        raise UserError(_('Location not in region! Please choose location'))
            elif not self.location_ids:
                location_ids += ','.join([str(region) for region in stock_location_region.ids])
        if not self.region_ids and not self.location_ids:
            warehouse_ids = self.env.user.warehouse_ids
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_ids += ','.join([str(id) for id in stock_locations.ids])
            else:
                location_ids = '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        categ_ids = ','.join([str(idd) for idd in self.categ_ids.ids]) if self.categ_ids else '0'
        if self.type == 'inventory':
            if self.type_view == 'pivot':
                report_name = "rpt_stock_move_pivot.rptdesign"
                date_from = self.to_date.strftime('%d/%m/%Y')
            else:
                report_name = "rpt_stock_move.rptdesign"
                date_from = self.to_date.strftime('%d/%m/%Y')
        elif self.type == 'general':
            report_name = "rpt_stock_move_in_out.rptdesign"
            date_from = self.from_date.strftime('%d/%m/%Y')
        else:
            report_name = "rpt_stock_move_in_out_value.rptdesign"
            date_from = self.from_date.strftime('%d/%m/%Y')

        if self.type == 'general_value':
            if self.user_has_groups('account.group_account_user') or self.user_has_groups(
                    'account.group_account_invoice') or self.user_has_groups(
                'account.group_account_manager') or self.user_has_groups('ev_account_cash_bank.group_account_chief'):
                param_str = {
                    '&from_date': date_from,
                    '&to_date': date_to,
                    '&location_ids': location_ids,
                    '&product_ids': product_ids,
                    '&categ_ids': categ_ids,
                    '&company_id': self.company_id.id,
                    '&to_lot': self.to_lot
                }
            else:
                raise UserError(_('You can not view report!'))
        else:
            param_str = {
                '&from_date': date_from,
                '&to_date': date_to,
                '&location_ids': location_ids,
                '&product_ids': product_ids,
                '&categ_ids': categ_ids,
                '&company_id': self.company_id.id,
                '&to_lot': self.to_lot,
            }
        birt_link = birt_url + report_name
        return {
            "type": "ir.actions.client",
            'name': 'Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }

    @api.onchange('region_ids')
    def set_domain_for_location_ids(self):
        if self.region_ids:
            return {'domain': {'location_ids': [('x_region_id.id', 'in', self.region_ids.ids)]}}
        else:
            return {'domain': {'location_ids': [(1, '=', 1)]}}
