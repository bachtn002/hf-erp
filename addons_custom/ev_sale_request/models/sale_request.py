from datetime import datetime, date

import xlsxwriter

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import pytz

from odoo.fields import Datetime
from dateutil.relativedelta import relativedelta


class SaleRequest(models.Model):
    _name = 'sale.request'
    _inherit = [
        'mail.thread'
    ]
    name = fields.Char('Name', readonly=True, select=True, copy=True, default='New')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse/Store', required=True)
    date_request = fields.Date('Request Date', default=lambda x: datetime.today(), required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('processed', 'Processed')],
        string='Use status', default='draft', track_visibility='always')
    warehouse_process = fields.Boolean(default=False, string='Warehouse Processed', readonly=1)
    purchase_process = fields.Boolean(default=False, string='Purchase Processed', readonly=1)
    sale_request_line = fields.One2many(comodel_name='sale.request.line', inverse_name='sale_request_id',
                                        string='Sale Request Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    count_general = fields.Float('Check general line to transfer status', default=0)

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('sale.request.seq') or '/'
        d_to = datetime.today()
        name = 'SR.' + str(d_to.year) + str(d_to.strftime('%m'))
        vals['name'] = name + '.' + seq
        if 'sale_request_line' in vals:
            for line in vals['sale_request_line']:
                product = self.env['product.product'].browse(line[2]['product_id'])
                product_type = product.product_tmpl_id.type
                if product_type == 'service':
                    raise UserError(_('Can not choose product with service type'))
                if not product.active:
                    raise UserError(_('Product is not active'))

        return super(SaleRequest, self).create(vals)

    def write(self, vals):
        if 'sale_request_line' in vals:
            for line in vals['sale_request_line']:
                if line[0] == 0:
                    product = self.env['product.product'].browse(line[2]['product_id'])
                    product_type = product.product_tmpl_id.type
                    if product_type == 'service':
                        raise UserError(_('Can not choose product with service type'))
                    if not product.active:
                        raise UserError(_('Product is not active'))
        return super(SaleRequest, self).write(vals)

    @api.constrains('date_request', 'warehouse_id')
    def _check_date_request_one_day(self):
        context = self._context
        current_uid = context.get('uid')
        id_user = self.env['res.users'].browse(current_uid).id
        # date = self.env['sale.request'].search([('date_request', '=', self.date_request), ('create_uid', '=', id_user)])
        date = self.env['sale.request'].sudo().search(
            [('date_request', '=', self.date_request), ('warehouse_id', '=', self.warehouse_id.id)])
        if len(date) > 1:
            raise UserError(_('You can only create sale request one time by a day'))

    # @api.constrains('sale_request_line')
    # def _check_qty(self):
    #     for rc in self.sale_request_line:
    #         if rc.qty <= 0:
    #             raise UserError(_('Product quantity must greater than 0!'))

    def unlink(self):
        for rc in self:
            if rc.state == 'draft':
                return super(SaleRequest, rc).unlink()
            raise UserError(_('You can only delete when state is draft'))

    def get_contract_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_sale_request/static/xls/imp_phieuyeucauhanghoa.xlsx'
        }

    def open_import_stock(self):
        return {
            'name': 'Import file',
            'type': 'ir.actions.act_window',
            'res_model': 'import.xls.wizard.stock',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'current_id': self.id},
        }

    def send_sale_request(self):
        for sale_request_line in self.sale_request_line:
            if not sale_request_line.supply_type:
                raise UserError(
                    _('Supply type must not be empty!'))

        today = fields.Date.today()
        self._check_date_request_one_day()
        if self.date_request > today:
            raise UserError(
                _('You cannot choose a date in the future'))

        data_time_request = self.company_id.x_time_request

        weekend = date.weekday(today)

        if weekend in (5, 6):
            data_time_request = self.company_id.x_time_request_weekend

        if data_time_request == 0.0:
            raise ValidationError(
                _('No fill request accept time'))
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        today_time = Datetime.now()
        date_today = pytz.utc.localize(today_time).astimezone(user_tz)
        data_time_request_second = data_time_request * 3600
        current_data_time_request_second = float(
            date_today.hour * 3600 + date_today.minute * 60 + date_today.second)
        if int(current_data_time_request_second) > int(data_time_request_second) or self.date_request < today:
            raise UserError(
                _('Request accept time out'))
        stop_supply = []
        dupicate_product = []
        for line in self.sale_request_line:
            if line.supply_type == 'stop_supply':
                stop_supply.append(line.product_id.name)
            sale_request_line = self.env['sale.request.line'].search(
                [('sale_request_id', '=', self.id), ('product_id', '=', line.product_id.id),
                 ('product_uom', '=', line.product_uom.id), ('supply_type', '=', line.supply_type)])
            if len(sale_request_line) > 1:
                product_err = line.product_id.name
                if product_err not in dupicate_product:
                    dupicate_product.append(product_err)
        product_stop_supply = ' \n- '.join([str(product) for product in stop_supply])
        dupicate_product_list = ' \n- '.join([str(product) for product in dupicate_product])
        if stop_supply:
            raise UserError(_('Request have product stop supply: \n- %s') % str(product_stop_supply))
        if dupicate_product:
            raise UserError(_('You can not duplicate product: \n- %s') % str(dupicate_product_list))
        self.state = 'sent'
        # self.check_warehouse_and_purchase_process()

    def return_sale_request(self):
        data_time_request = self.company_id.x_time_request
        if data_time_request == 0.0:
            raise ValidationError(
                _('No fill request accept time'))
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        today_time = Datetime.now()
        date_today = pytz.utc.localize(today_time).astimezone(user_tz)
        data_time_request_second = data_time_request * 3600
        current_data_time_request_second = float(
            date_today.hour * 3600 + date_today.minute * 60 + date_today.second)
        if int(current_data_time_request_second) > int(
                data_time_request_second) or date_today.date() > self.date_request:
            raise UserError(_(
                'Request accept time out'))
        if self.count_general > 0:
            raise UserError(_('Requests have been aggregated! You can not go back'))

        self.warehouse_process = False
        self.purchase_process = False
        self.state = 'draft'

    def accept_sale_request(self):
        self.state = 'processed'
        product_lines = self.env['sale.request.line'].search([('sale_request_id', '=', self.id)])

    def check_warehouse_and_purchase_process(self):
        product_lines = self.env['sale.request.line'].search([('sale_request_id', '=', self.id)])
        ware_house_count = 0
        purchase_count = 0
        for line in product_lines:
            if line.supply_type == 'warehouse':
                ware_house_count += 1
            else:
                purchase_count += 1
        if ware_house_count == 0:
            self.warehouse_process = True
        elif purchase_count == 0:
            self.purchase_process = True

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/sale.request.report/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }
        # report = self.env['ir.actions.report']._get_report_from_name('ev_sale_request.report_sale_request_report_xlsx')
        # report = self.env['ir.actions.report'].sudo().get_report_from_name('ev_sale_request.report_sale_request_report_xlsx')
        # report.report_file = "new name"
        # return self.env.ref['ev_sale_request.report_sale_request_report_xlsx'].report_action(self)
