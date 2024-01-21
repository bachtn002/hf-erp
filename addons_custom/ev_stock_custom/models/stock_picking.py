from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # def _action_done(self):
    #     if self.picking_type_id.code == 'outgoing' or self.location_dest_id.usage == 'transit':
    #         if self.company_id.x_not_export_negative:
    #             list_product = ''
    #             product_ids = ''
    #             lot_ids = ''
    #             for move_id in self.move_lines:
    #                 for line in move_id.move_line_ids:
    #                     if line.product_id.tracking == 'none':
    #                         if not product_ids:
    #                             product_ids += f'{line.product_id.id}'
    #                         else:
    #                             product_ids += f',{line.product_id.id}'
    #                     else:
    #                         if line.lot_id:
    #                             if not lot_ids:
    #                                 lot_ids += f'{line.lot_id.id}'
    #                             else:
    #                                 lot_ids += f',{line.lot_id.id}'
    #             # Check tồn của sản phẩm hoặc lô
    #             check_move_line = self.env['product.product']._generate_list_product_or_lot(product_ids=product_ids,
    #                                                                                         lot_ids=lot_ids,
    #                                                                                         date_to=datetime.date.today().strftime(
    #                                                                                             '%d/%m/%Y'),
    #                                                                                         location_id=self.location_id.id)
    #             if check_move_line:
    #                 for move_line in check_move_line:
    #                     if move_line[2] is None:
    #                         line_ids = self.env['stock.move.line'].sudo().search([('product_id', '=', move_line[0]),
    #                                                                        ('picking_id', '=', self.id)])
    #                         qty_done = []
    #                         for item in line_ids:
    #                             qty_done.append(item.qty_done)
    #                         compare = move_line[4] - sum(qty_done)
    #                         if compare < 0:
    #                             list_product = list_product + "Sản phẩm: %s, nhu cầu %s, xuất âm %s\n" % \
    #                                            (move_line[1], sum(qty_done), compare)
    #                     else:
    #                         line_ids = self.env['stock.move.line'].sudo().search([('lot_id', '=', move_line[2]),
    #                                                                        ('picking_id', '=', self.id)])
    #                         qty_done = []
    #                         for item in line_ids:
    #                             qty_done.append(item.qty_done)
    #                         compare = move_line[4] - sum(qty_done)
    #                         if compare < 0:
    #                             list_product = list_product + "Lô: %s, nhu cầu %s, xuất âm %s\n" % \
    #                                            (move_line[3], sum(qty_done), compare)
    #             # check nhập tồn của sản phẩm và lot
    #             list_check = ''
    #             products = []
    #             lots = []
    #             for item in check_move_line:
    #                 if item[2] is None:
    #                     products.append(item[0])
    #                 else:
    #                     lots.append(item[2])
    #             for move_id in self.move_lines:
    #                 for line in move_id.move_line_ids:
    #                     if line.product_id.tracking == 'none':
    #                         if line.product_id.id not in products:
    #                             list_check = list_check + "Sản phẩm: %s chưa nhập tồn.\n" % line.product_id.name
    #                     else:
    #                         if line.lot_id:
    #                             if line.lot_id.id not in lots:
    #                                 list_check = list_check + "Lô: %s chưa nhập tồn.\n" % line.lot_id.name
    #             if list_check:
    #                 raise ValidationError(f'{list_check}Vui lòng kiểm tra lại!')
    #             # ---------------------------------------------------------
    #             if list_product:
    #                 raise ValidationError(
    #                     f'{list_product}\nKhông đủ tồn để thực hiện xuất kho. \nVui lòng kiểm tra lại!')
    #     res = super(StockPicking, self)._action_done()
    #
    #     # xoá move line thừa (tạo dở dang) vẫn tạo phần dư 0
    #     self.move_ids_without_package.filtered(lambda x: x.quantity_done == 0).sudo().unlink()
    #     return res
