from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockTransfer(models.Model):
    _inherit = 'stock.transfer'

    package_lines = fields.One2many('stock.package.transfer', 'stock_transfer_id', 'Package Out Line', domain=[('state', '!=', 'cancel')])
    # check box: phân biệt phiếu điều chuyển được xác nhận xuất hàng bằng scan, nhập hàng bằng scan
    is_confirm_in_from_scan = fields.Boolean("Is confirm IN from scan?", default=False)
    is_confirm_out_from_scan = fields.Boolean("Is confirm OUT from scan?", default=False)
    total_package_number = fields.Integer("Total Package", default=0)

    def action_validate_scan(self):
        if self.state in ['draft']:
            self.action_confirm()
            self.action_check_available()
            # mark transfer confirmed by scan
            self.is_confirm_out_from_scan = True
            # confirm
            self.action_choose_out_date()
        elif self.state in ['confirmed']:
            self.action_check_available()
            self.action_choose_out_date()
            # mark transfer confirmed by scan
            self.is_confirm_out_from_scan = True
        elif self.state in ['ready']:
            # mark transfer confirmed by scan
            self.is_confirm_out_from_scan = True
            self.action_choose_out_date()
        elif self.state == 'transfer':
            for line in self.transfer_line_ids:
                if line.product_qty_scanned < (line.out_quantity - line.qty_packed):
                    raise UserError(_("Quantity receive can not be difference quantity delivery!"))
            # mark transfer confirmed by scan
            self.is_confirm_in_from_scan = True
            self.action_choose_in_date()

    def action_choose_out_date(self):
        try:
            packages = self.env['stock.package.transfer'].search([('stock_transfer_id', '=', self.id), ('state', '!=', 'cancel')])
            if packages:
                for line in self.transfer_line_ids:
                    line.out_quantity = 0
                # update total package out
                self.total_package_number = len(packages)
                self.out_picking_id.total_package_number = len(packages)
                for pack in packages:
                    if pack.qty_out != pack.qty:
                        raise UserError(_('Quantity out must be equal to quantity package'))
                    if pack.state not in ('packaged', 'cancel'):
                        raise UserError(_('State package must be packaged'))
                    # Cap nhat so luong xuat
                    for pack_line in pack.line_ids:
                        for transfer_line in self.transfer_line_ids:
                            if transfer_line.product_id.id == pack_line.product_id.id:
                                transfer_line.out_quantity += pack_line.qty_done
                                break
            else:
                # Case xuat rời
                if self.is_confirm_out_from_scan:
                    for trans_line in self.transfer_line_ids:
                        qty_scanned = trans_line.product_qty_scanned
                        # update quantity out when confirm from scan with quantity scanned
                        trans_line.out_quantity = qty_scanned
                        # update quantity scanned to zero ready for scan in
                        trans_line.product_qty_scanned = 0
            return super(StockTransfer, self).action_choose_out_date()
        except Exception as e:
            raise ValidationError(e)

    def action_choose_in_date(self):
        try:
            packages = self.env['stock.package.transfer'].search([('stock_transfer_id', '=', self.id), ('state', '!=', 'cancel')])
            if packages:
                for line in self.transfer_line_ids:
                    line.in_quantity = 0
                self.in_picking_id.total_package_number = len(packages)
                for pack in packages:
                    if pack.qty_in != pack.qty:
                        raise UserError(_('Quantity in must be equal to quantity package'))
                    if pack.state not in ('packaged', 'cancel'):
                        raise UserError(_('State package must be packaged'))
                    # Cap nhat so luong xuat
                    for pack_line in pack.line_ids:
                        for transfer_line in self.transfer_line_ids:
                            if transfer_line.product_id.id == pack_line.product_id.id:
                                transfer_line.in_quantity += pack_line.qty_done
                                break
                    if pack.state == 'packaged':
                        pack.state = 'unpackaged'
                        pack.date_unpack = fields.datetime.now()
            else:
                # case nhap rời
                if self.is_confirm_in_from_scan:
                    for trans_line in self.transfer_line_ids:
                        qty_scanned = trans_line.product_qty_scanned
                        if qty_scanned != trans_line.out_quantity:
                            raise UserError(_('Quantity in must be equal to quantity package'))
                        # update quantity out when confirm from scan with quantity scanned
                        trans_line.in_quantity = qty_scanned
                        # update quantity scanned to zero
                        trans_line.product_qty_scanned = 0
            return super(StockTransfer, self).action_choose_in_date()
        except Exception as e:
            raise ValidationError(e)

        # region Client Action handle functions
    def get_view_transfer(self):
        if self.state == 'transfer':
            view_id = self.env.ref('ev_stock_transfer.stock_transfer_to_form_view').id
        else:
            view_id = self.env.ref('ev_stock_transfer.stock_transfer_from_form_view').id
        if not view_id:
            raise UserError(_("No view was found!"))
        return view_id

    def _get_stock_transfer_fields_to_read(self):
        """ List of fields on the stock.transfer object that are needed by the
        client action. The purpose of this function is to be overridden in order
        to inject new fields to the client action.
        """
        return [
            'display_name',
            'state',
            'warehouse_id',
            'warehouse_dest_id',
            'transfer_line_ids',
            'package_lines',
        ]

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        if any(pack.state == 'processing' for pack in self.package_lines):
            raise UserError(_("Package can be delivery or receipt when package's state in processing!"))

        transfer_fields_to_read = self._get_stock_transfer_fields_to_read()
        transfer = self.read(transfer_fields_to_read)

        for trans in transfer:
            package_lines = self.env['stock.package.transfer'].search([('id', 'in', trans.pop('package_lines')), ('state', '!=', 'cancel')])

            trans['line_ids'] = []
            for line in package_lines:
                trans['line_ids'].append({
                    'id': line.id,
                    'package_id': line.id,
                    'display_name': line.display_name or line.name,
                    'product_barcode': line.display_name,
                    'qty': line.qty,
                    'qty_done': line.qty_in if line.stock_transfer_id.state == 'transfer' else line.qty_out,
                })

            # Prefetch data
            id, name = trans.pop('warehouse_id')
            trans['warehouse_id'] = {'id': id, 'display_name': name}
            # pack['warehouse_id'].update({'id': id, 'display_name': name})
            id, name = trans.pop('warehouse_dest_id')
            trans['warehouse_dest_id'] = {'id': id, 'display_name': name}
            if self.env.company.nomenclature_id:
                trans['nomenclature_id'] = [self.env.company.nomenclature_id.id]
            if not package_lines:
                product_ids = []
                transfer_line_ids = self.env['stock.transfer.line'].browse(trans.pop('transfer_line_ids'))
                if not transfer_line_ids:
                    raise UserError(_("There is no line to scan!"))
                for line in transfer_line_ids:
                    # load all product is outside the packages except product is package cover
                    if line.qty_packed < line.quantity and not line.product_id.is_package_cover:
                        product_ids.append(line.product_id.id)
                        # # SL y/c - SL đã đóng thùng nếu SL y/c > SL scan rời ngược lại bằng sl scan rời
                        # qty_out_to_scan = line.quantity - line.qty_packed if line.quantity > line.product_qty_scanned else line.product_qty_scanned
                        # # SL xuat - so luong dong thung
                        # qty_in_to_scan = line.out_quantity - line.qty_packed
                        trans['line_ids'].append({
                            'id': line.id,
                            'product_id': line.product_id.id,
                            'display_name': line.display_name if line.display_name else line.product_id.name,
                            'product_barcode': "",
                            'qty': line.out_quantity if self.state == 'transfer' else line.quantity,
                            'qty_done': line.product_qty_scanned,
                            'uom_id': line.product_uom.name,
                        })

                tracking_and_barcode_per_product_id = {}
                for res in self.env['product.product'].with_context(active_test=False).search_read(
                        [('id', 'in', product_ids)], ['tracking', 'barcode', 'is_package_cover']):
                    tracking_and_barcode_per_product_id[res.pop("id")] = res

                for line in trans['line_ids']:
                    if line.get('product_id'):
                        id = line['product_id']
                        line['product_id'] = {"id": id, **tracking_and_barcode_per_product_id[id]}

        return transfer

    def _check_scan_confirm_right(self):
        # Check access right allow to confirm out/in package
        if not self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            warehouse_source = self.warehouse_id.id in self.env.user.warehouse_ids.ids
            warehouse_dest = self.warehouse_dest_id.id in self.env.user.warehouse_ids.ids
            if not warehouse_source and not warehouse_dest:
                return False
            if self.state in ('draft', 'confirmed', 'ready') and not warehouse_source:
                return False
            if self.state in ('done', 'transfer') and not warehouse_dest:
                return False
        return True

    def write(self, values):
        package_lines = []
        transfer_lines = []
        if 'transfer_scan_line' in values:
            if not self._check_scan_confirm_right():
                raise UserError(_("You not allow to confirm this transfer!"))
            for line in values['transfer_scan_line']:
                qty_scan = line[2].pop('qty_done')
                if not line[2]['product_id']:
                    # if line have no product then this line is package line not transfer line
                    # Update package quantity state is not ready we assume this transfer is out
                    if self.state == 'transfer':
                        line[2]['qty_in'] = qty_scan
                    else:
                        line[2]['qty_out'] = qty_scan
                    line[2].pop('product_id')
                    package_lines.append(line)
                else:
                    line[2]['product_qty_scanned'] = qty_scan
                    transfer_lines.append((1, line[1], {'product_qty_scanned': qty_scan}))
            values.pop('transfer_scan_line')
            values['package_lines'] = package_lines
            values['transfer_line_ids'] = transfer_lines
        return super(StockTransfer, self).write(values)

    def create_new_package(self):
        try:
            if self.state in ('draft', 'confirmed', 'ready'):
                package_vals = {
                    'stock_transfer_id': self.id,
                    'warehouse_id': self.warehouse_id.id,
                    'warehouse_dest_id': self.warehouse_dest_id.id,
                    'qty': 1,
                    'qty_in': 0,
                    'qty_out': 0,
                    'weight': 0,
                    'date_packaged': fields.Datetime.now(),
                    'state': 'processing',
                }
                package = self.env['stock.package.transfer'].create(package_vals)
                query = """
                        select t.product_id, t.uom_id, sum(t.quantity) as quantity
                        from (
                                 SELECT a.product_id as product_id, a.uom_id as uom_id, -a.qty_done as quantity
                                 from stock_package_transfer_line a
                                    join stock_package_transfer b on b.id = a.package_transfer_id
                                    join product_product pp on pp.id = a.product_id
                                    join product_template tmpl on pp.product_tmpl_id = tmpl.id
                                 where b.stock_transfer_id = %s
                                   and b.state = 'packaged'
                                   and (tmpl.is_package_cover IS NULL or tmpl.is_package_cover = false)
    
                                 union all
    
                                 select a.product_id, a.product_uom as uom_id, a.quantity
                                 from stock_transfer_line a
                                    join product_product pp on pp.id = a.product_id
                                    join product_template tmpl on pp.product_tmpl_id = tmpl.id
                                 where stock_transfer_id = %s
                                    and (tmpl.is_package_cover IS NULL or tmpl.is_package_cover = false)
                             ) as t
                        group by t.product_id, t.uom_id
                    """
                # lấy danh sách sản phẩm và số lượng chưa đóng so với phiếu xuất kho
                self._cr.execute(query, (self.id, self.id))
                list = self._cr.dictfetchall()
                vals = []
                for detail in list:
                    if detail['quantity'] > 0:
                        val = {
                            'product_id': detail['product_id'],
                            'uom_id': detail['uom_id'],
                            'qty': detail['quantity'],
                            'qty_done': 0,
                            'package_transfer_id': package.id,
                        }
                        vals.append((0, 0, val))
                if len(vals) == 0:
                    package.state = 'draft'
                    package.unlink()
                    return False
                package.line_ids = vals
                return package
            else:
                return False
        except Exception as e:
            raise ValidationError(e)

    def action_create_package(self):
        # Check accecss right
        if not self.user_has_groups('ev_stock_package.group_user_package_activity'):
            raise UserError(_("You are not allow to proceed this action"))
        # button create package click => open scan products screen
        # Create package => call action client action (action_process)
        existing_packages = self.env['stock.package.transfer'].search(
            [('state', '=', 'processing'), ('stock_transfer_id', '=', self.id)])
        if existing_packages:
            action = self.env["ir.actions.actions"]._for_xml_id("ev_stock_package.stock_transfer_wizard_action")
            action['context'] = {
                'default_stock_transfer_id': self.id,
            }
            return action
        package_id = self.create_new_package()
        if not package_id:
            raise UserError(_("There is no line to create new Pack!"))
        return package_id.action_process()

    def open_scan_package(self):
        """
        open view scan package
        """
        try:
            packages = self.env['stock.package.transfer'].search([('stock_transfer_id', '=', self.id), ('state', '!=', 'cancel')])
            # action call client action delivery packages
            action = self.env["ir.actions.actions"]._for_xml_id("ev_stock_package.stock_barcode_transfer_client_action")
            params = {
                'model': 'stock.transfer',
                'package_id': self.id,
                'state': self.state,
                'is_scan_product': False if packages else True,
                'nomenclature_id': [self.env.company.nomenclature_id.id],
            }
            ctx = self.env.context.copy()
            ctx.update({'active_id': self.id})
            ctx.update({'active_ids': self.ids})
            return dict(action, target='fullscreen', params=params, context=ctx)
        except Exception as e:
            raise ValidationError(e)

    # endregion