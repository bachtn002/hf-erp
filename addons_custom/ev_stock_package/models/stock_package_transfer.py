# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import requests
import json


class StockPackageTransfer(models.Model):
    _name = 'stock.package.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_stock_transfer(self):
        try:

            if self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
                domain = [('state', 'in', ('draft', 'confirmed', 'ready'))]
                return domain
            else:
                warehouse_ids = []
                for record in self.env.user.warehouse_ids:
                    warehouse_ids.append(record.id)
                domain = [('state', 'in', ('draft', 'confirmed', 'ready')), ('warehouse_id', 'in', warehouse_ids)]
                return domain

        except Exception as e:
            raise ValidationError(e)

    name = fields.Char(string="Name package", default=lambda self: _('New'), required=True, readonly=True)
    date_packaged = fields.Datetime(string="Date Packaged", default=lambda x: fields.Datetime.now(), required=True)
    date_unpack = fields.Datetime(string="Date Unpack")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('packaged', 'Packaged'),
        ('unpackaged', 'Unpackaged'),
        ('cancel', 'Cancel')
    ], string="State", default='draft', track_visibility='onchange')
    stock_transfer_id = fields.Many2one('stock.transfer', string="Stock Transfer ID", required=True,
                                        domain=_default_stock_transfer)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    warehouse_dest_id = fields.Many2one('stock.warehouse', string="Warehouse Dest")
    weight = fields.Float(string="Weight", digits='Product Unit of Measure')
    line_ids = fields.One2many('stock.package.transfer.line', 'package_transfer_id', string="Line Ids")

    qty = fields.Integer(string="Quantity Package", default=1)
    qty_out = fields.Integer(string="Quantity Package Out", default=0)
    qty_in = fields.Integer(string="Quantity Package In", default=0)

    is_using_package_cover = fields.Boolean(string='Is using package cover')

    @api.onchange('qty_out', 'qty_in')
    def onchange_quantity(self):
        if self.qty_in > 1 or self.qty_out > 1:
            raise UserError(_("Package quantity delivery or receive can not be greater 1"))

    @api.onchange('stock_transfer_id')
    def _get_warehouse(self):
        try:
            self.warehouse_id = self.stock_transfer_id.warehouse_id
            self.warehouse_dest_id = self.stock_transfer_id.warehouse_dest_id

        except Exception as e:
            raise ValidationError(e)

    def get_current_package_state(self):
        return self.state

    def get_time_out_printing(self):
        timeout = self.env['ir.config_parameter'].sudo().get_param('ev_stock_package.time_out_print_popup_showed')
        return timeout

    def get_times_printing(self):
        try:
            time_printing = self.env['ir.config_parameter'].sudo().get_param('ev_stock_package.print_times')
            return time_printing or 1
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('stock_transfer_id')
    def _get_line_ids(self):
        try:
            query = """
                select t.product_id, t.uom_id, sum(t.quantity) as quantity
                from (
                         SELECT a.product_id as product_id, a.uom_id as uom_id, -a.qty_done as quantity
                         from stock_package_transfer_line a
                                  join stock_package_transfer b on b.id = a.package_transfer_id
                         where b.stock_transfer_id = %s
                           and b.state = 'packaged'
                
                         union all
                
                         select product_id, product_uom as uom_id, quantity
                         from stock_transfer_line a
                         where stock_transfer_id = %s
                     ) as t
                group by t.product_id, t.uom_id
            """
            if self.stock_transfer_id:
                # lấy danh sách sản phẩm và số lượng chưa đóng so với phiếu xuất kho
                self._cr.execute(query, (self.stock_transfer_id.id, self.stock_transfer_id.id))
                list = self._cr.dictfetchall()
                vals = []
                for detail in list:
                    if detail['quantity'] > 0:
                        val = {
                            'product_id': detail['product_id'],
                            'uom_id': detail['uom_id'],
                            'qty': detail['quantity'],
                            'qty_done': 0,
                            'package_transfer_id': self.id,
                        }
                        vals.append((0, 0, val))
                self.line_ids = False
                self.line_ids = vals

        except Exception as e:
            raise ValidationError(e)

    # region Client Action handle functions
    @api.model
    def get_all_package_by_name(self):
        packages = self.env['stock.package.transfer'].search([('state', '=', 'packaged')])
        packages_read = packages.read(['id', 'name'])
        results = {package['name']: package for package in packages_read}
        return results

    def _get_package_fields_to_read(self):
        """ List of fields on the stock.package.transfer object that are needed by the
        client action. The purpose of this function is to be overridden in order
        to inject new fields to the client action.
        """
        return [
            'display_name',
            'stock_transfer_id',
            'warehouse_id',
            'warehouse_dest_id',
            'line_ids',
            'qty',
            'qty_out',
            'qty_in',
        ]

    @api.model
    def _get_package_line_ids_fields_to_read(self):
        """ read() on package.line_ids only returns the id and the display
        name however a lot more data from stock.move.line are used by the client
        action.
        """
        return [
            'product_id',
            'display_name',
            'product_barcode',
            'qty',
            'qty_done',
            'uom_id',
        ]

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        try:
            # get fields of models
            package_fields_to_read = self._get_package_fields_to_read()
            package_line_ids_fields_to_read = self._get_package_line_ids_fields_to_read()
            packages = self.read(package_fields_to_read)

            # source_location_list, destination_location_list = self._get_locations()
            for pack in packages:
                pack['line_ids'] = self.env['stock.package.transfer.line'].browse(pack.pop('line_ids')).read(
                    package_line_ids_fields_to_read)

                # Prefetch data
                product_ids = tuple(set([move_line_id['product_id'][0] for move_line_id in pack['line_ids']]))
                tracking_and_barcode_per_product_id = {}
                for res in self.env['product.product'].with_context(active_test=False).search_read(
                        [('id', 'in', product_ids)], ['tracking', 'barcode', 'is_package_cover']):
                    tracking_and_barcode_per_product_id[res.pop("id")] = res

                for line_id in pack['line_ids']:
                    id = line_id.pop('product_id')[0]
                    line_id['product_id'] = {"id": id, **tracking_and_barcode_per_product_id[id]}
                id, name = pack.pop('warehouse_id')
                pack['warehouse_id'] = {'id': id, 'display_name': name}
                id, name = pack.pop('warehouse_dest_id')
                pack['warehouse_dest_id'] = {'id': id, 'display_name': name}
                if self.env.company.nomenclature_id:
                    pack['nomenclature_id'] = [self.env.company.nomenclature_id.id]
            return packages
        except Exception as e:
            raise ValidationError(e)

    def action_process(self):
        if not self.line_ids:
            raise UserError(_("There is no line to create new Pack!"))
        """Return client action to open """
        if self.state == 'draft':
            self.state = 'processing'
        # action call action client
        action = self.env["ir.actions.actions"]._for_xml_id("ev_stock_package.stock_barcode_package_client_action")
        params = {
            'model': 'stock.package.transfer',
            'package_id': self.id,
            'state': self.stock_transfer_id.state,
            'is_scan_product': True,
            'nomenclature_id': [self.env.company.nomenclature_id.id],
        }
        ctx = self.env.context.copy()
        ctx.update({'active_id': self.id})
        ctx.update({'active_ids': self.ids})
        return dict(action, target='fullscreen', params=params, context=ctx)

    # endregion

    def action_print_stamp_package(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_package.report_template_stamp_package_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def write(self, values):
        # Check access right allow to confirm out/in package
        if not self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            warehouse_source = self.stock_transfer_id.warehouse_id.id in self.env.user.warehouse_ids.ids
            warehouse_dest = self.stock_transfer_id.warehouse_dest_id.id in self.env.user.warehouse_ids.ids
            if values.get('qty_in') or values.get('qty_out'):
                if not warehouse_source and not warehouse_dest:
                    raise UserError(_("You not allow to confirm this transfer!"))
                if self.stock_transfer_id.state in ('draft', 'confirmed', 'ready') and not warehouse_source:
                    raise UserError(_("You not allow to confirm this transfer!"))
                if self.stock_transfer_id.state in ('done', 'transfer') and not warehouse_dest:
                    raise UserError(_("You not allow to confirm this transfer!"))
        return super(StockPackageTransfer, self).write(values)

    def action_confirm(self):
        if self.state == 'packaged':
            raise UserError(_("Package already packaged!"))
        try:
            for line in self.line_ids:
                # remove product have qty = 0
                if line.qty_done <= 0:
                    line.unlink()
                    continue
                # Change package quantity equal with qty done
                line.qty = line.qty_done
                # ghi lại số lượng xuất
                for transfer_line in self.stock_transfer_id.transfer_line_ids:
                    if transfer_line.product_id.id == line.product_id.id:
                        transfer_line.qty_packed += line.qty_done
                        if transfer_line.product_id.is_package_cover:
                            transfer_line.quantity = transfer_line.qty_packed
                        break

                # Get the new lines, check package using cover or not
                if line.product_id.is_package_cover:
                    self.is_using_package_cover = True
                    exist_cover_line = self.env['stock.transfer.line'].search([('product_id', '=', line.product_id.id),
                                                            ('stock_transfer_id', '=', self.stock_transfer_id.id)])
                    if not exist_cover_line:
                        self.stock_transfer_id.write({'transfer_line_ids': [(0, 0, {
                            'stock_transfer_id': self.stock_transfer_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.uom_id.id,
                            'quantity': line.qty,
                            'qty_packed': line.qty_done
                        })]})

            if self.state == 'processing':
                self.date_packaged = datetime.now()
                self.state = 'packaged'
        except Exception as e:
            raise ValidationError(e)

    def action_unpackage(self):
        try:
            if self.state == 'packaged':
                # Ghi lại số lượng nhận sản phẩm
                for line in self.line_ids:
                    for transfer_line in self.stock_transfer_id.transfer_line_ids:
                        if transfer_line.product_id == line.product_id:
                            transfer_line.in_quantity += line.qty_done
                self.state = 'unpackaged'
                self.date_unpack = fields.datetime.now()
        except Exception as e:
            raise ValidationError(e)

    def action_cancel(self):
        try:
            if self.stock_transfer_id.state not in ('transfer', 'done'):
                if self.state == 'packaged':
                    for line in self.line_ids:
                        # Reverse qty_packed of transfer
                        for transfer_line in self.stock_transfer_id.transfer_line_ids:
                            if transfer_line.product_id.id == line.product_id.id:
                                transfer_line.qty_packed -= line.qty_done
                                # remove line if it's package cover line and quantity is zero
                                if transfer_line.product_id.is_package_cover:
                                    # package cover have quantity and quantity pack equal
                                    transfer_line.quantity -= line.qty_done
                                    if transfer_line.qty_packed <= 0:
                                        self.stock_transfer_id.transfer_line_ids = [(2, transfer_line.id)]
                                        continue

                        # Reverse quantity done of Package to zero
                        line.qty_done = 0
                    # Change state of package
                    self.state = 'cancel'
                else:
                    self.state = 'cancel'
            else:
                raise UserError(_('Package can not be cancel when Transfer already transferred or done!'))
        except Exception as e:
            raise ValidationError(e)

    def action_back_to_draft(self):
        try:
            if self.state == 'cancel':
                self.state = 'draft'
        except Exception as e:
            raise ValidationError(e)

    def get_stock_package_transfer_barcode(self):
        try:
            fields_to_read = self._get_fields_package_transfer_to_read()
            fields_line_ids_to_read = self._get_fields_line_ids_to_read()
            package_transfers = self.read(fields_to_read)
            for package in package_transfers:
                line_ids = self.env['stock.package.transfer.line'].browse(package.pop('line_ids')).read(
                    fields_line_ids_to_read)
        except Exception as e:
            raise ValidationError(e)

    def _get_fields_package_transfer_to_read(self):
        return [
            'name',
            'stock_transfer_id',
            'warehouse_id',
            'warehouse_dest_id',
            'weight',
            'state',
            'line_ids',
        ]

    def _get_fields_line_ids_to_read(self):
        return [
            'product_id',
            'uom_id',
            'qty',
            'qty_done',
            'package_transfer_id',
        ]

    @api.model
    def create(self, vals):
        try:
            res = super(StockPackageTransfer, self).create(vals)
            if res.stock_transfer_id.state not in ('draft', 'confirmed', 'ready'):
                raise UserError(_("Can not create Package when transfer's state is not in draft, confirm or ready "))
            # create name when create record
            month = date.today().month
            year = date.today().year
            day = date.today().day
            # Format prefix: RQ%(y)s%(month)s/xxxx
            prefix = f'SPTR{year % 100}{month:02d}{day:02d}/'
            package_id = self.env['stock.package.transfer'].search([('id', '!=', res.id)],
                                                                   order='create_date desc', limit=1)
            if not package_id:
                res.name = f'{prefix}00001'
            else:
                number = int(package_id.name.split('/')[1])
                suffix = f'{number + 1:05d}'
                res.name = f'{prefix}{suffix}'
            # end
            return res

        except Exception as e:
            raise ValidationError(e)

    def unlink(self):
        try:
            for rec in self:
                if rec.state not in ('draft', 'cancel'):
                    raise UserError(_('You can not delete package with state not in draft or cancel'))
            return super(StockPackageTransfer, self).unlink()
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            domain = domain
        else:
            warehouse_ids = self.env['res.users'].sudo().search([('id', '=', self._uid)]).warehouse_ids.ids
            domain_warehouse = []
            domain_warehouse.append('warehouse_id')
            if len(warehouse_ids) == 1:
                domain_warehouse.append('=')
                listToStr = ' '.join(map(str, warehouse_ids))
                warehouse_id = int(listToStr)
                domain_warehouse.append(warehouse_id)
            else:
                domain_warehouse.append('in')
                domain_warehouse.append(warehouse_ids)
            domain.append(domain_warehouse)
        return super(StockPackageTransfer, self).search_read(domain, fields, offset, limit, order)


    def get_data_scale(self):
        print('call')
        try:
            url = 'http://localhost:5000/data'
            response = requests.get(url,headers={'Content-Type': 'application/json',
                                                 'Cache-Control': 'no-cache', })
            print('res:', response)
            dt = response.json()
            if 'result_from_scale' in dt:
                print(dt['result_from_scale'])
                return dt['result_from_scale']
        except Exception as e:
            raise ValidationError(e)
