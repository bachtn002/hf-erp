from datetime import datetime
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import odoo.tools as tools
import os


class StockDocumentReportDone(models.TransientModel):
    _name = 'stock.document.report.done'

    name = fields.Char('Name')
    date_trading = fields.Char('Date Trading')
    origin = fields.Char('Origin')
    location = fields.Char('Location')
    location_dest = fields.Char('Location Dest')
    x_description = fields.Char('X Description')
    ref = fields.Char('Ref')
    customer_code = fields.Char('Customer Code')
    customer_name = fields.Char('Customer Name')
    default_code = fields.Char('Default Code')
    product_name = fields.Char('Product Name')
    lot_name = fields.Char('Lot Name')
    uom = fields.Char('Uom')
    quantity = fields.Char('Quantity')
    explain = fields.Char('Explain')
    state = fields.Char('State')
    report_id = fields.Char('Report ID')


class ReportStockDocumentDoneWizard(models.TransientModel):
    _name = 'report.stock.document.done.wizard'

    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    state = fields.Selection([
        ('no_done', 'No Done'),
        ('done', 'Done')],
        default='no_done', string="State")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    x_all_internal = fields.Boolean('All Internal')

    @api.onchange('x_all_internal')
    def _onchange_all_internal(self):
        if self.x_all_internal:
            loaction_ids = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)])
            self.location_ids = [(6, 0, loaction_ids.ids)]
        else:
            self.location_ids = [(5, 0, 0)]

    def open_table_report(self):
        from_date = self.from_date.strftime('%d/%m/%Y')
        to_date = self.to_date.strftime('%d/%m/%Y')
        location_ids = ','.join(
            [str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        product_ids = ','.join(
            [str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'

        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'
        sql = """
                delete from stock_document_report_done;
                insert into stock_document_report_done ( name, date_trading, origin, location, location_dest, x_description, ref
                                          , customer_code, customer_name, default_code, product_name, lot_name, uom, quantity
                                          , explain, state, report_id, create_date, write_date, create_uid, write_uid)
                select name         as name,
                       ngay         as date_trading,
                       mct          as origin,
                       kho_xuat     as location,
                       kho_nhap     as location_dest,
                       lct          as x_description,
                       marefkh      as ref,
                       makh         as customer_code,
                       tenKH        as customer_name,
                       masp         as default_code,
                       product_name as product_name,
                       lot_name     as lot_name,
                       dv           as uom,
                       sum          as quantity,
                       diengiai     as explain,
                       state        as state,
                       %s           as report_id,
                       now()        as create_date,
                       now()        as write_date,
                       %d           as create_uid,
                       %d           as write_uid
                from (SELECT bp.note,
                             bp.name,
                             b.date                                             ngayy,
                             to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy') ngay,
                             b.origin                                           mct,
                             CASE
                                 WHEN bp.x_warehouse_out_name is null THEN COALESCE(('[' || d.name || ']' || d.name), d.name)
                                 ELSE bp.x_warehouse_out_name END as            kho_xuat,
                             CASE
                                 WHEN bp.x_warehouse_in_name is null THEN COALESCE(('[' || dd.name || ']' || dd.name), dd.name)
                                 ELSE bp.x_warehouse_in_name END                kho_nhap,
                             b.x_description                                    lct,
                             rp.ref                                             marefkh,
                             rp.name                                            makh,
                             rp.name                                            tenKH,
                             ct.default_code                                    masp,
                             ct.name                                            product_name,
                             e.name                                             lot_name,
                             u.name                                             dv,
                             b.price_unit                                       dongia,
                             b.x_value                                          giatri,
                             sum(a.qty_done),
                             b.note                                             diengiai,
                             CASE
                                 WHEN b.state = 'done' THEN 'Hoàn thành'
                                 WHEN b.state = 'cancel' THEN 'Đã Hủy'
                                 ELSE 'Chưa hoàn thành' END       as            state

                      FROM stock_move b
                               LEFT JOIN stock_move_line a ON b.id = a.move_id
                               LEFT JOIN stock_picking bp ON b.picking_id = bp.id
                               LEFT JOIN res_partner rp ON rp.id = bp.partner_id
                               LEFT JOIN stock_picking_type spt ON spt.id = b.picking_type_id
                               LEFT JOIN product_product c ON c.id = b.product_id
                               LEFT JOIN product_template ct ON ct.id = c.product_tmpl_id
                               LEFT JOIN product_category cc ON cc.id = ct.categ_id
                               LEFT JOIN stock_location d ON d.id  = a.location_id
                               LEFT JOIN stock_location dd ON dd.id = a.location_dest_id
                               LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                               LEFT JOIN uom_uom u ON b.product_uom = u.id
                      WHERE to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                            to_date('%s', 'dd/mm/yyyy')
                        AND to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                            to_date('%s', 'dd/mm/yyyy')
                        AND b.state = 'done'
                        AND ((d.id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0') or
                             (dd.id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0'))
                        AND (b.product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                      GROUP BY bp.x_warehouse_out_name, bp.x_warehouse_in_name, bp.note, bp.name, b.date, b.x_description, b.price_unit,
                               b.x_value, d.name, d.name, dd.name, dd.name,
                               ct.default_code, ct.name, e.name, b.origin,
                               rp.name, b.note, b.state, u.name, rp.ref) as A;
                """
        self.env.cr.execute(sql % (
            report_id, self.env.user.id, self.env.user.id, from_date, to_date, location_ids, location_ids, location_ids,
            location_ids, product_ids, product_ids))
        self.env.cr.commit()
        return {
            'name': _('Stock Document Report Action'),
            'view_mode': 'tree',
            'res_model': 'stock.document.report.done',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }

    def action_export_report_accountent(self):
        pass

    def action_report_excel(self):
        pass