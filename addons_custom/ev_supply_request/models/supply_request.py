# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, except_orm, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.osv import osv
import xlrd
import xlrd3
import base64
from datetime import date
from datetime import datetime


class SupplyRequest(models.Model):
    _name = 'supply.request'
    _order = 'date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Supply Request'

    name = fields.Char('Number', default=lambda self: _('New'))
    date = fields.Date('Date', default=lambda x: datetime.today(), track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('receive', 'Receive'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], copy=False, default='draft', track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    line_ids = fields.One2many('supply.request.line', 'supply_request_id', string='Information')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    supply_warehouse_group_ids = fields.Many2many('supply.warehouse.group', 'supply_warehouse_group_table',
                                                  'supply_id', 'group_id', string='Warehouse Group')

    supply_product_group_ids = fields.Many2many('supply.product.group', 'supply_product_group_table', 'supply_id',
                                                'group_id',
                                                string='Product Group')

    supply_purchase_order_ids = fields.One2many('supply.purchase.order.line', 'supply_request_id',
                                                string='Supply Purchase Order')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        # send mail activity
        # create name when create record
        month = date.today().month
        year = date.today().year
        # Format prefix: RQ%(y)s%(month)s/xxxx
        prefix = f'SRP{year % 100}{month:02d}/'
        request_id = self.env['supply.request'].search([('company_id', '=', res.company_id.id), ('id', '!=', res.id)],
                                                       order='create_date desc', limit=1)
        if not request_id:
            res.name = f'{prefix}0001'
        else:
            suffix = f'{int(request_id.name[-4:]) + 1:04d}'
            res.name = f'{prefix}{suffix}'
        # end
        return res

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("You cannot delete record if the state is not 'Draft'."))
        return super(SupplyRequest, self).unlink()

    def action_calculate(self):
        try:
            self.ensure_one()
            today = fields.Date.today()
            if self.date > today:
                raise UserError(
                    _('You cannot choose a date in the future'))
            if self.state == 'receive':
                return True
            warehouse_ids = []
            for warehouse in self.supply_warehouse_group_ids.warehouse_ids:
                warehouse_ids.append(warehouse.id)
            product_ids = []
            for product in self.supply_product_group_ids.product_ids:
                product_ids.append(product.id)
            sale_request_obj = self.env['sale.request']
            sale_request_line_obj = self.env['sale.request.line']
            supply_request_line_obj = []
            sale_request_line_obj = sale_request_line_obj.sudo().search(
                [('sale_request_id.warehouse_id', 'in', warehouse_ids),
                 ('sale_request_id.date_request', '=', self.date + relativedelta(hours=7)),
                 ('sale_request_id.state', '=', 'sent'), ('supply_type', '=', 'purchase'),
                 ('check_general', '=', False), ('product_id.id', 'in', product_ids)], order='create_date asc')

            sale_request_obj = sale_request_obj.sudo().search(
                [('warehouse_id', 'in', warehouse_ids), ('date_request', '=', self.date + relativedelta(hours=7)),
                 ('state', '=', 'sent')], order='create_date asc')
            for line in sale_request_line_obj:
                warehouse_id = line.sale_request_id.warehouse_id
                region_id = line.sale_request_id.warehouse_id.x_stock_region_id
                seller_id = 0
                price = 0
                check = False
                if region_id:
                    query_region = self._sql_price_stock_reigon(region_id.id, line.product_id.product_tmpl_id.id,
                                                                self.date)
                    self._cr.execute(query_region)

                    value_region = self._cr.dictfetchone()

                    if value_region:
                        price = value_region['price']
                        seller_id = value_region['name']
                        check = True
                if check == False:
                    query_warehouse = self._sql_price_stock_warehouse(warehouse_id.id, line.product_id.product_tmpl_id.id,
                                                                      self.date)
                    self._cr.execute(query_warehouse)
                    value_warehouse = self._cr.dictfetchone()
                    if value_warehouse:
                        price = value_warehouse['price']
                        seller_id = value_warehouse['name']
                    else:
                        query_price_locattion_false = self._sql_price_locattion_false(line.product_id.product_tmpl_id.id,
                                                                                self.date)
                        self._cr.execute(query_price_locattion_false)
                        value_price_locattion_false = self._cr.dictfetchone()
                        if value_price_locattion_false:
                            price = value_price_locattion_false['price']
                            seller_id = value_price_locattion_false['id']

                vals = {
                    'supply_request_id': self.id,
                    'request_line_id': line.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.product_uom.id,
                    'qty_request': line.qty,
                    'categ_id': line.product_id.categ_id.id,
                    'warehouse_dest_id': line.sale_request_id.warehouse_id.id,
                    'partner_id': seller_id if seller_id != 0 else None,
                    'price_unit': price,
                    'qty_buy': 0,
                    'note': line.note,
                }
                supply_request_line_obj.append((0, 0, vals))
                line.check_general = True
                line.sale_request_id.count_general += 1
                if line.sale_request_id.count_general == len(line.sale_request_id.sale_request_line):
                    line.sale_request_id.state = 'processed'
            self.line_ids = supply_request_line_obj
            self.state = 'receive'
        except Exception as e:
            raise ValidationError(e)

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'cancel':
            return True
        if self.state == 'receive':
            for line in self.line_ids:
                if line.request_line_id.sale_request_id.state != 'sent':
                    line.request_line_id.sale_request_id.state = 'sent'
                if line.request_line_id.check_general:
                    line.request_line_id.check_general = False
                    line.request_line_id.sale_request_id.count_general -= 1
                    if line.request_line_id.sale_request_id.count_general < len(
                            line.request_line_id.sale_request_id.sale_request_line) and line.request_line_id.sale_request_id.state == 'processed':
                        line.request_line_id.sale_request_id.state = 'sent'
        self.state = 'cancel'

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'done':
            return True
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        if len(self.supply_purchase_order_ids) == 0:
            raise UserError(_('Nothing to general'))
        for line in self.line_ids:
            if line.qty_buy > 0:
                line.request_line_id.qty_apply = line.qty_buy
        check_po = False
        for line in self.supply_purchase_order_ids:
            if line.qty_buy > 0:
                if line.price_unit <= 0:
                    raise UserError(_('Price unit be than 0'))
                if not line.partner_id:
                    raise UserError(_("You need to configure the partner'."))
                picking_type_id = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', line.warehouse_dest_id.id), ('code', '=', 'incoming')], limit=1)
                purchase_order = purchase_order_obj.search(
                    [('partner_id', '=', line.partner_id.id), ('picking_type_id', '=', picking_type_id.id),
                     ('origin', '=', self.name)], limit=1)
                if purchase_order:
                    purchase_order_line_value = self._prepare_purchase_order_line(line.product_id, line.qty_buy,
                                                                                  line.uom_id, self.company_id,
                                                                                  purchase_order.partner_id,
                                                                                  purchase_order, line.price_unit,
                                                                                  line.note)
                    purchase_order_line_obj.create(purchase_order_line_value)
                    line.purchase_order_id = purchase_order.id
                    check_po = True
                else:
                    purchase_order_id = purchase_order_obj.create({
                        'partner_id': line.partner_id.id,
                        'date_order': self.date,
                        'picking_type_id': picking_type_id.id,
                        'origin': self.name
                    })
                    if purchase_order_id:
                        purchase_order_line_value = self._prepare_purchase_order_line(line.product_id, line.qty_buy,
                                                                                      line.uom_id, self.company_id,
                                                                                      purchase_order_id.partner_id,
                                                                                      purchase_order_id,
                                                                                      line.price_unit, line.note)
                        purchase_order_line_obj.create(purchase_order_line_value)
                        line.purchase_order_id = purchase_order_id.id
                        check_po = True
        if check_po:
            self.state = 'done'

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po, price_unit,
                                     note):
        partner = supplier.name
        uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        # _select_seller is used if the supplier have different price depending
        # the quantities ordered.
        seller = supplier

        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name)
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == company_id.id)

        product_lang = product_id.with_prefetch().with_context(
            lang=seller.lang,
            partner_id=seller.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        # date_planned = po.date_planned or self.env['purchase.order.line']._get_date_planned(seller, po=po)
        date_planned = po.date_planned or fields.Date.today()
        return {
            'name': name,
            'product_qty': uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'x_note': note,
            'order_id': po.id,
        }

    def action_confirm_order(self):
        self.ensure_one()
        for line in self.supply_purchase_order_ids:
            line.purchase_order_id.button_confirm()

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_supply_request.export_supply_request/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

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
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 5
            arr_line_error_not_exist_database = []
            warehouse_not_exist_database = []
            warehouse_not_exist_supply = []
            product_not_exist_supply = []
            supply_purchase_order_ids = []
            date = datetime.today()
            product_ids = []
            warehouse_ids = []
            for line in self.line_ids:
                product_ids.append(line.product_id.id)
                warehouse_ids.append(line.warehouse_dest_id.id)

            print(product_ids)
            print(warehouse_ids)
            while index < sheet.nrows:
                warehouse_code = sheet.cell(index, 0).value
                if warehouse_code == '':
                    break
                warehouse_code = str(warehouse_code).upper()
                warehouse_obj = self.env['stock.warehouse'].search([('code', '=', warehouse_code)], limit=1)
                if not warehouse_obj:
                    warehouse_not_exist_database.append(index + 1)
                if warehouse_obj.id not in warehouse_ids:
                    warehouse_not_exist_supply.append(index + 1)
                listToStr_warehouse_not_exist_database = ' , '.join(
                    [str(elem) for elem in warehouse_not_exist_database])
                if len(warehouse_not_exist_database) != 0:
                    raise ValidationError(
                        _('Kho không tồn tại trong hệ thống, dòng (%s)') % str(listToStr_warehouse_not_exist_database))
                listToStr_warehouse_not_exist_supply = ' , '.join(
                    [str(elem) for elem in warehouse_not_exist_supply])
                if len(warehouse_not_exist_supply) != 0:
                    raise ValidationError(
                        _('Kho không tồn tại phiếu tổng hợp, dòng (%s)') % str(listToStr_warehouse_not_exist_supply))
                product_code = sheet.cell(index, 3).value
                if self._is_number(product_code):
                    product_code = str(product_code).split('.')[0]
                else:
                    product_code = str(product_code).upper()
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_obj:
                    arr_line_error_not_exist_database.append(index + 1)
                if product_obj.id not in product_ids:
                    product_not_exist_supply.append(index + 1)
                listToStr_line_not_exist_database = ' , '.join(
                    [str(elem) for elem in arr_line_error_not_exist_database])
                if len(arr_line_error_not_exist_database) != 0:
                    raise ValidationError(
                        _('Product is not exists, line (%s)') % str(listToStr_line_not_exist_database))
                listToStr_product_not_exist_supply = ' , '.join(
                    [str(elem) for elem in product_not_exist_supply])
                if len(product_not_exist_supply) != 0:
                    raise ValidationError(
                        _('Sản phẩm không tồn tại trong phiếu tổng hợp, line (%s)') % str(listToStr_product_not_exist_supply))
                uom_name = sheet.cell(index, 5).value
                uom_obj = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                if not uom_obj:
                    raise UserError(_('Không tồn tại đơn vị tính' + str(uom_name)))
                partner_code = sheet.cell(index, 6).value
                partner_obj = self.env['res.partner'].search([('ref', '=', partner_code)], limit=1)
                if not partner_obj:
                    raise UserError(_('Không tồn tại NCC tại dòng ' + str(index + 1)))
                qty = sheet.cell(index, 7).value
                price_unit = sheet.cell(index, 7).value
                price = 0
                warehouse_id = warehouse_obj
                region_id = warehouse_obj.x_stock_region_id
                check = False
                if region_id:
                    query_region = self._sql_import_price_stock_reigon(region_id.id, product_obj.product_tmpl_id.id,
                                                                partner_obj.id,date)
                    self._cr.execute(query_region)

                    value_region = self._cr.dictfetchone()
                    if value_region:
                        price = value_region['price']
                        check = True
                if check == False:
                    query_warehouse = self._sql_import_price_stock_warehouse(warehouse_id.id,
                                                                      product_obj.product_tmpl_id.id,
                                                                      partner_obj.id,date)
                    self._cr.execute(query_warehouse)
                    value_warehouse = self._cr.dictfetchone()
                    if value_warehouse:
                        price = value_warehouse['price']
                    else:
                        query_price_location_false = self._sql_import_price_location_false(product_obj.product_tmpl_id.id,
                                                                                    partner_obj.id,date)
                        self._cr.execute(query_price_location_false)
                        value_price_location_false = self._cr.dictfetchone()
                        if value_price_location_false:
                            price = value_price_location_false['price']

                if product_obj and warehouse_obj and uom_obj:
                    if product_obj.uom_po_id.category_id.id != uom_obj.category_id.id:
                        raise UserError(_('Đơn vị tính khác nhóm cấu hình trong sản phẩm' + str(uom_name)))
                    line_obj = self.env['supply.request.line'].search([('supply_request_id', '=', self.id),
                                                                       ['product_id', '=', product_obj.id],
                                                                       ['warehouse_dest_id', '=', warehouse_obj.id]],
                                                                      limit=1)
                    if line_obj:
                        line_obj.qty_buy += qty
                        line_obj.uom_id = uom_obj.id
                    supply_purchase = {
                        'supply_request_id': self.id,
                        'product_id': product_obj.id,
                        'uom_id': product_obj.uom_id.id,
                        'categ_id': product_obj.categ_id.id,
                        'warehouse_dest_id': warehouse_obj.id,
                        'partner_id': partner_obj.id,
                        'price_unit': price,
                        'qty_buy': qty,
                        'note': sheet.cell(index, 9).value,
                    }
                    supply_purchase_order_ids.append((0, 0, supply_purchase))
                index = index + 1
            self.supply_purchase_order_ids = supply_purchase_order_ids
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def _sql_price_stock_warehouse(self, warehouse_id, product_id, date):
        return """
            select b.name,
                   b.x_listed_price,
                   b.price
            from price_stock_warehouse a
                join product_supplierinfo b on b.id = a.supplierinfo_id
                join product_template c on c.id = b.product_tmpl_id
            where a.warehouse_id = %s
                and supplierinfo_id in (SELECT a.id
                                      from product_supplierinfo a
                                               join res_partner b on b.id = a.name
                                               join product_template c on c.id = a.product_tmpl_id
                                      where c.id = %s
                                        and a.x_price_location = True
                                        and case
                                                when a.date_start is not null and a.date_end is not null
                                                    then a.date_start <= '%s' and
                                                         a.date_end >= '%s'
                                                when a.date_start is null and a.date_end is not null
                                                    then a.date_end >= '%s'
                                                when a.date_start is not null and a.date_end is null
                                                    then a.date_start <= '%s'
                                                else 1 = 1
                                          end
                                      order by a.price asc)
              
            order by price asc
            limit 1
        """ % ( warehouse_id, product_id, date, date, date, date)

    def _sql_price_stock_reigon(self, region_id, product_id, date):
        return """
            select b.name,
                   b.x_listed_price,
                   b.price
            from price_stock_region a
                join product_supplierinfo b on b.id = a.supplierinfo_id
                join product_template c on c.id = b.product_tmpl_id
            where a.region_id = %s
                and a.supplierinfo_id in (SELECT a.id
                                      from product_supplierinfo a
                                               join res_partner b on b.id = a.name
                                               join product_template c on c.id = a.product_tmpl_id
                                      where c.id = %s
                                        and a.x_price_location = True
                                        and case
                                                when a.date_start is not null and a.date_end is not null
                                                    then a.date_start <= '%s' and
                                                         a.date_end >= '%s'
                                                when a.date_start is null and a.date_end is not null
                                                    then a.date_end >= '%s'
                                                when a.date_start is not null and a.date_end is null
                                                    then a.date_start <= '%s'
                                                else 1 = 1
                                          end
                                      order by a.price asc)
             
            order by price asc
            limit 1
        """ % (region_id, product_id, date, date, date, date)

    def _sql_price_locattion_false(self, product_id, date):
        return """
            SELECT b.id, a.x_listed_price, a.price
            from product_supplierinfo a
                       join res_partner b on b.id = a.name
                       join product_template c on c.id = a.product_tmpl_id
            where c.id = %s
                and a.x_price_location = False
                and case
                        when a.date_start is not null and a.date_end is not null
                            then a.date_start <= '%s' and
                                 a.date_end >= '%s'
                        when a.date_start is null and a.date_end is not null
                            then a.date_end >= '%s'
                        when a.date_start is not null and a.date_end is null
                            then a.date_start <= '%s'
                        else 1 = 1
                  end
            order by a.price asc
            limit 1
        """ % (product_id, date, date, date, date,)

    def _sql_import_price_stock_warehouse(self, warehouse_id, product_id, partner_id, date):
        return """
            select b.id,
                   b.x_listed_price,
                   b.price
            from price_stock_warehouse a
                     join product_supplierinfo b on b.id = a.supplierinfo_id
                     join product_template c on c.id = b.product_tmpl_id
            where a.warehouse_id = %s
              and a.supplierinfo_id in (SELECT a.id
                                        from product_supplierinfo a
                                                 join res_partner b on b.id = a.name
                                                 join product_template c on c.id = a.product_tmpl_id
                                        where c.id = %s
                                          and b.id = %s
                                          and a.x_price_location = True
                                          and case
                                                  when a.date_start is not null and a.date_end is not null
                                                      then a.date_start  <= '%s' and a.date_end  >= '%s'
                                                  when a.date_start is null and a.date_end is not null
                                                      then a.date_end >= '%s'
                                                  when a.date_start is not null and a.date_end is null
                                                      then a.date_start <= '%s'
                                                  else 1 = 1
                                            end
                                        order by a.price asc)
            order by price asc
            limit 1
        """ % (warehouse_id, product_id, partner_id, date, date, date, date)

    def _sql_import_price_stock_reigon(self, region_id, product_id, partner_id, date):
        return """
            select b.id,
                   b.x_listed_price,
                   b.price
            from price_stock_region a
                     join product_supplierinfo b on b.id = a.supplierinfo_id
            where a.region_id = %s
              and a.supplierinfo_id in (SELECT a.id
                                        from product_supplierinfo a
                                                 join res_partner b on b.id = a.name
                                                 join product_template c on c.id = a.product_tmpl_id
                                        where c.id = %s
                                          and b.id = %s
                                          and a.x_price_location = True
                                          and case
                                                  when a.date_start is not null and a.date_end is not null
                                                      then a.date_start <= '%s' and a.date_end >= '%s'
                                                  when a.date_start is null and a.date_end is not null
                                                      then a.date_end  >= '%s'
                                                  when a.date_start is not null and a.date_end is null
                                                      then a.date_start  <= '%s'
                                                  else 1 = 1
                                            end
                                        order by a.price asc)
            order by price asc
            limit 1
        """ % (region_id, product_id, partner_id, date, date, date, date)

    def _sql_import_price_location_false(self, product_id, partner_id, date):
        return """
            SELECT b.id, a.x_listed_price, a.price
            from product_supplierinfo a
                       join res_partner b on b.id = a.name
                       join product_template c on c.id = a.product_tmpl_id
            where c.id = %s
                and b.id = %s
                and a.x_price_location = False
                and case
                        when a.date_start is not null and a.date_end is not null
                            then a.date_start <= '%s' and
                                 a.date_end >= '%s'
                        when a.date_start is null and a.date_end is not null
                            then a.date_end >= '%s'
                        when a.date_start is not null and a.date_end is null
                            then a.date_start <= '%s'
                        else 1 = 1
                  end
            order by a.price asc
            limit 1
        """ % (product_id, partner_id, date, date, date, date)
