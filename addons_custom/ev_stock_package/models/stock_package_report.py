from xml.dom import ValidationErr
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPackageReport(models.TransientModel):
    _name = 'stock.package.report'

    name = fields.Char('Package name')
    stock_transfer_id = fields.Char(string="Stock Transfer ID")

    # state = fields.Char('State')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('packaged', 'Packaged'),
        ('unpackaged', 'Unpackaged'),
        ('cancel', 'Cancel')
    ], string="State")

    weight = fields.Float('Weight', digits='Product Unit of Measure')
    date_packaged = fields.Datetime(string="Date Packaged")
    warehouse_id = fields.Char(string="Warehouse")
    warehouse_dest_id = fields.Char(string="Warehouse Dest")
    report_line_ids = fields.One2many('stock.package.report.line', 'package_report_id', 'Report Line ids')
    button_clicked = fields.Boolean("Button clicked")

    def button_report(self):
        try:
            self.button_clicked = True
            if len(self.report_line_ids) > 0:
                self.report_line_ids.unlink()
            package_ids = self.env['stock.package.transfer'].search(
                [('name', '=', self.name)])
            print(package_ids)
            if package_ids:
                self.stock_transfer_id = package_ids.stock_transfer_id.name
                self.date_packaged = package_ids.date_packaged
                self.warehouse_id = package_ids.warehouse_id.name
                self.warehouse_dest_id = package_ids.warehouse_dest_id.name
                self.state = package_ids.state
                print("self: ", self.state)
                print("package: ", package_ids.state)
                self.weight = package_ids.weight
    
                list = []
                for line in package_ids.line_ids:
                    list.append((0, 0, {
                        'product_id': line.product_id.id,
                        'uom_id': line.uom_id.id,
                        'qty': line.qty,
                        'qty_done': line.qty_done,
                    }))
                self.report_line_ids = list
            else:
                raise UserError(_('Name package does not exits'))
        except Exception as e:
            raise ValidationError(e)
