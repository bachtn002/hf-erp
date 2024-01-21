# -*- coding: utf-8 -*-
from datetime import datetime

import xlrd
import base64
import xlwt

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError

try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule


class StockCard(models.TransientModel):
    _name = 'stock.card'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    name = fields.Char("Description", default="Stock card")
    product_id = fields.Many2one('product.product', "Product", required=True)
    product_uom = fields.Many2one('uom.uom', "Unit of measurement")
    location_id = fields.Many2one('stock.location', "Location", required=True)
    from_date = fields.Date("From date", required=True, default=fields.Date.today().strftime('%Y-%m-01'))
    to_date = fields.Date("To date", required=True, default=fields.Date.today())
    opening_stock = fields.Float("Opening stock")  # Ton dau ky
    closing_stock = fields.Float("Closing stock")
    move_lines = fields.One2many('stock.card.line', 'stock_card_id')

    @api.onchange('to_date', 'from_date')
    def _onchange_to_date(self):
        if self.to_date and self.to_date > fields.Date.today():
            raise ValidationError(_('\"To date\" must not be greater than \"Today\".'))
        if self.from_date and self.to_date and self.to_date < self.from_date:
            raise ValidationError(_('\"From date\" must not be greater than \"To date\".'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id
        else:
            self.product_uom = False

    def action_generate(self):
        self.ensure_one()
        for line in self.move_lines:
            line.unlink()
        self.opening_stock = self.calculate_opening_stock()
        self.generate_card_lines()

    def calculate_opening_stock(self):
        '''
        Lấy tổng nhập đến đầu kỳ trừ đi tổng xuất đến đầu kỳ  --> ra số lượng tồn đầu kì
        :return:
        '''
        quantity_in = 0.0
        quantity_out = 0.0
        #######in#######
        # query_quant_in = "select SUM(qty_done) as sum_in from stock_move_line " \
        #                  "WHERE location_dest_id = %s AND state='done' AND product_id = %s AND (date::timestamp + INTERVAL '7 hours')::date < %s::date"

        # Fix uom stock move line != uom product by congnd
        query_quant_in = """
            select sum(sum_in) as sum_in
            from (select case
                             when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                             else qty_done end sum_in
                  from stock_move_line a
                           join product_product b on b.id = a.product_id
                           join product_template c on c.id = b.product_tmpl_id
                           join uom_uom d on d.id = c.uom_id
                  where location_dest_id = %s
                    AND state='done'
                    AND product_id = %s
                    AND (date::timestamp + INTERVAL '7 hours')::date < %s::date) si
        """

        self._cr.execute(query_quant_in, (self.location_id.id, self.product_id.id, str(self.from_date)))
        res_sum_in = self._cr.dictfetchone()
        if 'sum_in' in res_sum_in:
            if res_sum_in['sum_in'] is not None:
                quantity_in = res_sum_in['sum_in']
        #######out#######
        # query_quant_out = "select SUM(qty_done) as sum_out from stock_move_line " \
        #                   "where location_id = %s AND state='done'  AND product_id = %s AND (date::timestamp + INTERVAL '7 hours')::date < %s::date"

        # Fix uom stock move line != uom product by congnd
        query_quant_out = """
                    select sum(sum_in) as sum_out
                    from (select case
                                     when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                     else qty_done end sum_in
                          from stock_move_line a
                                   join product_product b on b.id = a.product_id
                                   join product_template c on c.id = b.product_tmpl_id
                                   join uom_uom d on d.id = c.uom_id
                          where location_id = %s
                            AND state='done'
                            AND product_id = %s
                            AND (date::timestamp + INTERVAL '7 hours')::date < %s::date) so
                """

        self._cr.execute(query_quant_out, (self.location_id.id, self.product_id.id, str(self.from_date)))
        res_sum_out = self._cr.dictfetchone()
        if 'sum_out' in res_sum_out:
            if res_sum_out['sum_out'] is not None:
                quantity_out = res_sum_out['sum_out']
        ret = quantity_in - quantity_out
        return ret

    def generate_card_lines(self):
        '''
        Tìm các stock.move trong khoảng thời gian >= from_date và <= to_date
        sau đó sinh ra các card.line
        :return:
        '''
        # query_period_moves = '''
        #     SELECT sm.id as move_id, sml.location_id, sml.location_dest_id, (sml.date + INTERVAL '7 hours')::date sml_date,
        #         SUM(sml.qty_done), sp.name as pick_name, SUM(sml.qty_done) product_qty, sp.id as picking_id,
        #         sm.origin origin, sm.note, sm.x_description,
        #         CASE
        #         WHEN rp_po.name IS NOT NULL then rp_po.name
        #         WHEN rp.name IS NOT NULL then rp.name
		# 		WHEN sl_2.complete_name IS NOT NULL then sl_2.complete_name
		# 		WHEN sl.complete_name IS NOT NULL then sl.complete_name
		# 		END
		# 		as partner_name, sp.origin as picking_origin,
        #         si.name as inventory_name,
        #         CASE
		# 		WHEN si.write_uid IS NOT NULL then rp_ru_si.name
		# 		WHEN si.write_uid is null then rp_ru_sm.name
		# 		END as user
        #     FROM stock_move_line as sml
        #     LEFT JOIN stock_move as sm ON sml.move_id = sm.id
        #     LEFT JOIN stock_picking as sp ON sm.picking_id = sp.id
        #     LEFT JOIN res_partner rp on sp.partner_id = rp.id
        #     LEFT JOIN stock_inventory si on si.id = sm.inventory_id
        #     LEFT JOIN stock_location sl on sl.id = si.x_location_id
		# 	LEFT JOIN stock_location sl_2 on sl_2.id = sp.location_dest_id
		# 	LEFT JOIN res_users ru_si on ru_si.id = si.write_uid
		# 	LEFT JOIN res_partner rp_ru_si on rp_ru_si.id = ru_si.partner_id
		# 	LEFT JOIN res_users ru_sm on ru_sm.id = sm.write_uid
		# 	LEFT JOIN res_partner rp_ru_sm on rp_ru_sm.id = ru_sm.partner_id
		# 	LEFT JOIN pos_order po on po.id = sp.pos_order_id
		# 	LEFT JOIN res_partner rp_po on rp_po.id = po.partner_id
        #     WHERE sml.product_id = %s
        #         AND (sml.location_id = %s OR sml.location_dest_id = %s)
        #         AND (sml.date + INTERVAL '7 hours')::date >= %s::date
        #         AND (sml.date + INTERVAL '7 hours')::date < (%s::date + '1 day'::interval)
        #         AND sml.state = 'done'
        #     GROUP BY sm.id, sml.location_id, sml.location_dest_id, sml.date,
        #         sp.name, sp.id, sm.origin, sm.note, rp.name,sl_2.complete_name, sl.complete_name , si.name, si.write_uid
        #         , rp_ru_si.name, rp_ru_sm.name, rp_po.name
        #     ORDER BY sml.date;
        # '''
        query_period_moves = """
            select move_id, location_id, location_dest_id, sml_date, sum(qty_done), pick_name,
                   sum(product_qty) as product_qty , picking_id, origin, note, x_description, 
                   partner_name, picking_origin, inventory_name, user
            from (SELECT sm.id                 as              move_id,
                         sml.location_id,
                         sml.location_dest_id,
                         (sml.date + INTERVAL '7 hours')::date sml_date,
                         case
                             when sml.product_uom_id != c.uom_id then sml.qty_done * d.factor
                             else qty_done end                 qty_done,
                         sp.name               as              pick_name,
                         case
                             when sml.product_uom_id != c.uom_id then sml.qty_done * d.factor
                             else qty_done end as              product_qty,
                         sp.id                 as              picking_id,
                         sm.origin                             origin,
                         sm.note,
                         sm.x_description,
                         CASE
                             WHEN rp_po.name IS NOT NULL then rp_po.name
                             WHEN rp.name IS NOT NULL then rp.name
                             WHEN sl_2.complete_name IS NOT NULL then sl_2.complete_name
                             WHEN sl.complete_name IS NOT NULL then sl.complete_name
                             END  as              partner_name,
                         sp.origin             as              picking_origin,
                         si.name               as              inventory_name,
                         CASE
                             WHEN si.write_uid IS NOT NULL then rp_ru_si.name
                             WHEN si.write_uid is null then rp_ru_sm.name
                             END               as              user
                  FROM stock_move_line as sml
                           LEFT JOIN stock_move as sm ON sml.move_id = sm.id
                           LEFT JOIN stock_picking as sp ON sm.picking_id = sp.id
                           LEFT JOIN res_partner rp on sp.partner_id = rp.id
                           LEFT JOIN stock_inventory si on si.id = sm.inventory_id
                           LEFT JOIN stock_location sl on sl.id = si.x_location_id
                           LEFT JOIN stock_location sl_2 on sl_2.id = sp.location_dest_id
                           LEFT JOIN res_users ru_si on ru_si.id = si.write_uid
                           LEFT JOIN res_partner rp_ru_si on rp_ru_si.id = ru_si.partner_id
                           LEFT JOIN res_users ru_sm on ru_sm.id = sm.write_uid
                           LEFT JOIN res_partner rp_ru_sm on rp_ru_sm.id = ru_sm.partner_id
                           LEFT JOIN pos_order po on po.id = sp.pos_order_id
                           LEFT JOIN res_partner rp_po on rp_po.id = po.partner_id
                           LEFT join product_product b on b.id = sml.product_id
                           LEFT join product_template c on c.id = b.product_tmpl_id
                           LEFT join uom_uom d on d.id = c.uom_id
                  WHERE sml.product_id = %s
                    AND (sml.location_id = %s OR sml.location_dest_id = %s)
                    AND (sml.date + INTERVAL '7 hours')::date >= %s::date
                    AND (sml.date + INTERVAL '7 hours')::date < (%s::date + '1 day'::interval)
                    AND sml.state = 'done'
                ) as scl
            GROUP BY move_id, location_id, location_dest_id, sml_date,
                pick_name, picking_id, origin, note, x_description, partner_name, picking_origin , inventory_name, 
                user
            ORDER BY sml_date;
        """
        self._cr.execute(query_period_moves,
                         (self.product_id.id, self.location_id.id, self.location_id.id, self.from_date, self.to_date))
        res_period_moves = self._cr.dictfetchall()
        card_line_obj = self.env['stock.card.line']

        temp_inventory = self.opening_stock
        for row in res_period_moves:
            quant_in = 0.0
            quant_out = 0.0

            if row['location_id'] == self.location_id.id:
                quant_out = row['product_qty']
            else:
                quant_in = row['product_qty']

            temp_inventory = temp_inventory + quant_in - quant_out
            inventory = temp_inventory
            note = row['note']
            origin = row['origin']
            picking_origin = row['picking_origin']
            inventory_name = row['inventory_name']
            picking_name = row['pick_name']
            x_description = ''
            if origin or picking_origin:
                x_description = row['x_description']
            elif inventory_name:
                x_description = row['x_description'] + " KIEM KE"
            # move_id = row['move_id']
            date_move = row['sml_date']
            # the_move = stock_move.sudo().search([('id', '=', move_id)])
            # date_move = (the_move.date + timedelta(hours=7)).date()
            args = {
                'stock_card_id': self.id,
                'date': date_move,
                'move_id': row['move_id'],
                'reference': origin or picking_origin or inventory_name,
                'picking_name': picking_name or "-",
                'note': note or "--",
                'qty_in': quant_in,
                'qty_out': quant_out,
                'qty_inventory': inventory,
                'x_description': x_description,
                'partner_name': row['partner_name'],
                'user': row['user']
            }
            card_line_obj.create(args)
        self.closing_stock = temp_inventory

    def action_print(self):
        self.action_generate()
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_card.report_template_stock_card_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def action_print_excel(self):
        # return self.env.ref['ev_stock_card.stock_card_xlsx'].report_action(self)
        self.action_generate()
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/ev_stock_card.stock_card_xlsx/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

        # wb = xlwt.Workbook(encoding="UTF-8")
        # date_str = str(datetime.today().date())
        # ws = wb.add_sheet(date_str)
        # editable = xlwt.easyxf("protection: cell_locked false;")
        # read_only = xlwt.easyxf("")
        # header_style = xlwt.easyxf("pattern: pattern solid, fore_color black; align: HORZ CENTER, VERT CENTER;font: height 280,color white;\
        #                                                 borders: left thin, right thin, top thin,top_color white, bottom_color white, right_color white, left_color white; pattern: pattern solid;")
        #
        # ws.col(0).width = 10 * 150
        # ws.col(1).width = 10 * 500
        # ws.col(2).width = 10 * 600
        # ws.col(3).width = 10 * 250
        # ws.col(4).width = 10 * 250
        # ws.col(5).width = 10 * 500
        # ws.col(6).width = 10 * 500
        # ws.write(0, 0, u'STT', header_style)
        # ws.write(0, 1, u'Mã SP', header_style)
        # ws.write(0, 2, u'Tên SP', header_style)
        # ws.write(0, 3, u"Đơn vị", header_style)
        # ws.write(0, 4, u"SL", header_style)
        # ws.write(0, 5, u"Giá bán", header_style)
        # ws.write(0, 6, u"Ghi chú", header_style)
        # stream = stringIOModule.BytesIO()
        # wb.save(stream)
        # xls = stream.getvalue()
        # vals = {
        #     'name': date_str + '.xls',
        #     'datas': base64.b64encode(xls),
        #     'datas_fname': self.name + ' ' + date_str + '.xls',
        #     'type': 'binary',
        #     'res_model': 'stock.transfer',
        #     'res_id': self.id,
        # }
        # file_xls = self.env['ir.attachment'].create(vals)
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': '/web/content/' + str(file_xls.id) + '?download=true',
        #     'target': 'new',
        # }
    # def action_print_excel(self):
    #     birt_url = config['birt_url'] or '0'
    #     if birt_url == '0':
    #         raise ValidationError("Chưa cấu hình birt_url!")
    #     report_name = "rpt_stock_card.rptdesign"
    #     param_str = {
    #         "&id": self.id,
    #         "&from_date": self.from_date.strftime('%d/%m/%Y'),
    #         "&to_date": self.from_date.strftime('%d/%m/%Y'),
    #     }
    #
    #     return {
    #         "type": "ir.actions.client",
    #         'name': 'Thẻ kho',
    #         'tag': 'BirtViewerActionCurrent',
    #         'target': 'self',
    #         'context': {
    #             'birt_link': birt_url + report_name,
    #             'payload_data': param_str,
    #         }
    #     }
