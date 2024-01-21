# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError


class StockMoveReport(models.TransientModel):
    _name = "stock.move.report"
    _inherit = 'report.base'
    _auto = True
    _description = _("Stock Move Report")

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.stock_move_report_template'

    rpt_name = fields.Char(default='BÁO CÁO TỒN KHO')
    from_date = fields.Date(string='From date')
    to_date = fields.Date(string='To date')

    region_ids = fields.Many2many('stock.region', string='Region')
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    type = fields.Selection(
        [('inventory', 'Inventory report'),
         ('general', 'General account of input – output – inventory'),
         ('general_value',
          'General account of input – output – inventory value')],
        string='Report Type', default='inventory')
    to_lot = fields.Boolean(string='Get Lot')
    categ_ids = fields.Many2many('product.category', string='Category')
    type_view = fields.Selection([
        ('table', 'List'),
        ('pivot', 'Pivot')],
        string='Report view', default='table')
    x_all_internal = fields.Boolean('All Location Internal')

    _sql_constraints = [
        ('date_check', "CHECK(from_date<=to_date)",
         "The start date must be earlier than the end date!")
    ]

    report_type = fields.Selection(default='table')

    @api.onchange('type')
    def onchange_type(self):
        self.x_all_internal = False

    @api.onchange('region_ids')
    def set_domain_for_location_ids(self):
        if self.region_ids:
            return {'domain': {'location_ids': [
                ('x_region_id.id', 'in', self.region_ids.ids)]}}
        else:
            return {'domain': {'location_ids': [(1, '=', 1)]}}

    def get_download_file_name(self):
        return _('stock_move_report.xlsx')

    def _get_report_json(self):
        Store = self.env['stock.move.report.store']
        location_ids = ','.join([str(idd) for idd in
                                 self.location_ids.ids]) if self.location_ids else '0'
        if self.region_ids:
            location_ids += ','
            warehouse_ids = self.env.user.warehouse_ids
            stock_location_region = self.env['stock.location'].search(
                [('x_region_id', 'in', self.region_ids.ids)])
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search(
                    [('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_true_ids = []
                    for stock_location in stock_locations:
                        if stock_location.id in stock_location_region.ids:
                            location_true_ids.append(stock_location.id)
                    if location_true_ids:
                        location_ids += ','.join(
                            [str(id) for id in location_true_ids])
                    else:
                        raise UserError(
                            _('Location not in region! Please choose location'))
            elif not self.location_ids:
                location_ids += ','.join(
                    [str(region) for region in stock_location_region.ids])
        if not self.region_ids and not self.location_ids:
            warehouse_ids = self.env.user.warehouse_ids
            if warehouse_ids:
                stock_locations = self.env['stock.location'].search(
                    [('x_warehouse_id', 'in', warehouse_ids.ids)])
                if stock_locations:
                    location_ids += ','.join(
                        [str(id) for id in stock_locations.ids])
            else:
                location_ids = '0'
        product_ids = ','.join([str(idd) for idd in
                                self.product_ids.ids]) if self.product_ids else '0'
        categ_ids = ','.join(
            [str(idd) for idd in self.categ_ids.ids]) if self.categ_ids else '0'

        date_to = self.to_date.strftime('%d/%m/%Y')

        self.report_type = 'table'

        if self.type == 'inventory':
            self.rpt_name = 'BÁO CÁO TỒN KHO'
            Store = self.env['stock.move.report.store']
            date_from = self.to_date.strftime('%d/%m/%Y')

            if self.type_view == 'pivot':
                self.report_type = 'pivot'
            else:
                if self.x_all_internal:
                    location_ids = '0'
                    Store = self.env['stock.move.all.report.store']

        elif self.type == 'general':
            self.rpt_name = "BÁO CÁO NHẬP XUẤT TỒN"
            Store = self.env['stock.move.in.out.report.store']
            date_from = self.from_date.strftime('%d/%m/%Y')

        elif self.type == 'general_value':
            self.rpt_name = "BÁO CÁO NHẬP XUẤT TỒN CÓ GIÁ TRỊ"
            Store = self.env['stock.move.in.out.value.report.store']
            date_from = self.from_date.strftime('%d/%m/%Y')

            if self.user_has_groups(
                    'account.group_account_user') or self.user_has_groups(
                    'account.group_account_invoice') or self.user_has_groups(
                'account.group_account_manager') or self.user_has_groups(
                'ev_account_cash_bank.group_account_chief'):
                if self.x_all_internal:
                    location_ids = '0'
                    Store = self.env['stock.move.in.out.value.all.report.store']
            else:
                raise UserError(_('You can not view report!'))

        params = {'from_date': date_from, 'to_date': date_to,
                  'location_ids': location_ids, 'product_ids': product_ids,
                  'categ_ids': categ_ids, 'company_id': self.company_id.id,
                  'to_lot': self.to_lot}

        return Store.get_data(**params)

    def prepare_report_pivot_configs(self):
        values = ['sltoncuoi']
        index = ['product_code', 'product_name', 'dv']
        columns = ['location_name']
        return {
            'values': values,
            'index': index,
            'columns': columns,
            'aggfunc': np.sum,
            'margins': True,
            'margins_name': _('Total'),
        }

    def _header_merge(self):
        if self.type == 'general_value':
            if not self.x_all_internal:
                return [
                    ['0:0', '0:1', '.no'],
                    ['1:0', '1:1', 'location_name'],
                    ['2:0', '2:1', 'product_code'],
                    ['3:0', '3:1', 'product_name'],
                    ['4:0', '4:1', 'dv'],
                    ['5:1', '5:1', 'sltondau'],
                    ['6:1', '6:1', 'tondau_standard_price'],
                    ['7:1', '7:1', 'slnhapkho'],
                    ['8:1', '8:1', 'nhapkho_standard_price'],
                    ['9:1', '9:1', 'slxuatkho'],
                    ['10:1', '10:1', 'xuatkho_standard_price'],
                    ['11:1', '11:1', 'sltoncuoi'],
                    ['12:1', '12:1', 'toncuoi_standard_price'],
                    ['5:0', '6:0', 'tondau'],
                    ['7:0', '8:0', 'nhapkho'],
                    ['9:0', '10:0', 'xuatkho'],
                    ['11:0', '12:0', 'toncuoi'],
                ]
            else:
                return [
                    ['0:0', '0:1', '.no'],
                    ['1:0', '1:1', 'product_code'],
                    ['2:0', '2:1', 'product_name'],
                    ['3:0', '3:1', 'dv'],
                    ['4:1', '4:1', 'sltondau'],
                    ['5:1', '5:1', 'tondau_standard_price'],
                    ['6:1', '6:1', 'slnhapkho'],
                    ['7:1', '7:1', 'nhapkho_standard_price'],
                    ['8:1', '8:1', 'slxuatkho'],
                    ['9:1', '9:1', 'xuatkho_standard_price'],
                    ['10:1', '10:1', 'sltoncuoi'],
                    ['11:1', '11:1', 'toncuoi_standard_price'],
                    ['4:0', '5:0', 'tondau'],
                    ['6:0', '7:0', 'nhapkho'],
                    ['8:0', '9:0', 'xuatkho'],
                    ['10:0', '11:0', 'toncuoi'],
                ]
        return []

    def _columns_name(self):
        if self.type_view == 'pivot' and self.type == 'inventory':
            return {
                'product_code': _('Product Code'),
                'product_name': _('Product Name'),
                'dv': _('Unit'),
                'location_name': '',
            }
        return {
            '.no': _('.No'),
            'product_code': _('Product Code'),
            'product_name': _('Product Name'),
            'dv': _('Unit'),
            'location_name': 'Location Name',
            'toncuoi': _('Last Quantity'),
            'tondau': _('First Quantity'),
            'nhapkho': _('In Quantity'),
            'xuatkho': _('Out Quantity'),
            'tondau_standard_price': _('Price'),
            'xuatkho_standard_price': _('Price'),
            'nhapkho_standard_price': _('Price'),
            'toncuoi_standard_price': _('Price'),
            'sltoncuoi': _('Quantity'),
            'sltondau': _('Quantity'),
            'slnhapkho': _('Quantity'),
            'slxuatkho': _('Quantity'),
        }

    def _build_report_pandas_table(self, data):
        df = pd.json_normalize(data)
        df.index += 1

        if self.type == 'inventory':
            if self.x_all_internal:
                from_column, to_column = 3, 4
            else:
                from_column, to_column = 4, 5
        elif self.type == 'general':
            from_column, to_column = 4, 8

        elif self.type == 'general_value':
            if self.x_all_internal:
                from_column, to_column = 3, 11
            else:
                from_column, to_column = 4, 12

        row_sum = df.iloc[:, from_column:to_column].sum()
        df.loc['Total'] = row_sum
        return df.fillna('')
