from email.policy import default
from attr import field
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class PrintStamp(models.TransientModel):
    _name = 'print.stamp'
    _description = 'Print stamp'
    _rec_name = 'shop_id'

    shop_id = fields.Many2one(comodel_name='pos.shop',
                              string='Shop ID', required=True)
    promotion_ids = fields.Many2many(
        'pos.promotion', 'print_stamp_promotion_rel', 'promotion_id', 'print_stamp_id')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist', string="Price List")
    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion')
    stamp_type = fields.Selection([
        ('shelf', 'Shelf'),
        ('promotion', 'Promotion'),
        ('product', 'Product'),
        ('other', 'Other')
    ], string='Stamp Type')
    print_stamp_line_ids = fields.One2many(comodel_name='print.stamp.line', inverse_name='print_stamp_id',
                                           string="Print Stamp Line")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    button_choose = fields.Boolean('check choose click', default=False)

    @api.onchange('shop_id')
    def _onchange_pricelist_id(self):
        try:
            if self.shop_id:
                pos_config = self.env['pos.config'].search(
                    [('x_pos_shop_id', '=', self.shop_id.id)], limit=1)
                self.promotion_id = None
                self.print_stamp_line_ids = None
                self.button_choose = False
                if pos_config:
                    self.pricelist_id = pos_config.pricelist_id
                else:
                    self.pricelist_id = None
                if self.stamp_type in ('product', 'shelf'):
                    product_ids = self.env['product.product'].search(['|', '|', '&', '&',
                                                                      ('product_tmpl_id', 'in',
                                                                       self.shop_id.product_ids.ids),
                                                                      ('product_tmpl_id.x_print_stamp', '=', True),
                                                                      ('product_tmpl_id.available_in_pos', '=', True),
                                                                      '&',
                                                                      ('product_tmpl_id.x_is_tools', '=', True),
                                                                      ('product_tmpl_id.x_print_stamp', '=', True),
                                                                      '&',
                                                                      ('product_tmpl_id.x_is_combo', '=', True),
                                                                      ('product_tmpl_id.available_in_pos', '=', True),
                                                                      ])
                    if self.stamp_type == 'shelf':
                        product_ids = self.env['product.product'].search(
                            ['|', '&',
                             ('product_tmpl_id', 'in', self.shop_id.product_ids.ids),
                             ('product_tmpl_id.available_in_pos', '=', True),
                             '&',
                             ('product_tmpl_id.x_is_combo', '=', True),
                             ('product_tmpl_id.available_in_pos', '=', True),
                             ])
                    vals = []
                    for line in product_ids:
                        pricelist_item = self.env['product.pricelist.item'].sudo().search(
                            ['|', ('date_end', '=', False), ('date_end', '>=', datetime.today()), '|', ('date_start', '=', False), ('date_start', '<=', datetime.today()),
                             ('pricelist_id', '=', self.pricelist_id.id),
                             ('product_tmpl_id', '=', line.product_tmpl_id.id)], order='create_date desc',
                            limit=1)
                        if pricelist_item:
                            price_unit = pricelist_item.fixed_price
                        else:
                            price_unit = line.product_tmpl_id.list_price
                        price = price_unit

                        expire_date = False
                        if relativedelta(days=line.x_expiry):
                            expire_date = date.today() + relativedelta(days=line.x_expiry)
                        val = {
                            'product_id': line.id,
                            'uom_id': line.product_tmpl_id.uom_id.id,
                            'price_unit': price,
                            'packed_date': datetime.now() + relativedelta(hours=7) if line.product_tmpl_id.x_empty_date == False else None,
                            'expire_date': expire_date if line.product_tmpl_id.x_empty_date == False else None,
                            'origin': line.product_tmpl_id.x_origin,
                        }
                        vals.append((0, 0, val))
                    self.print_stamp_line_ids = vals

        except Exception as e:
            raise ValidationError(e)

    @api.onchange('shop_id', 'promotion_id')
    def _onchange_promotion_id(self):
        try:
            if self.stamp_type == 'promotion':
                if self.shop_id:
                    date = datetime.today()
                    pos_config = self.env['pos.config'].search(
                        [('x_pos_shop_id', '=', self.shop_id.id)], limit=1)
                    query = """
                        SELECT pos_promotion_id
                        from pos_config_pos_promotion_rel a
                                 join pos_promotion b on b.id = a.pos_promotion_id
                        where a.pos_config_id = %s
                        and b.apply_all_res_partner_apply = True
                        and b.apply_manual_pos_config = True
                        and b.type = 'qty_price'
                        and b.state = 'active'
                        and b.check_promotion = False
                    """ % (pos_config.id)
                    self._cr.execute(query)
                    promotion_ids = self._cr.fetchall()
                    ids = []
                    ids_other = []

                    promotion_other_config = self.env['product.other.config'].search(
                        [('promotion_id.state', '=', 'active'), ('promotion_id.check_promotion', '=', False),
                         ('promotion_id.end_date', '>=', date)])
                    for promotion in promotion_ids:
                        ids.append(promotion[0])
                    for promotion_other in promotion_other_config:
                        if pos_config.id in promotion_other.promotion_id.pos_configs.ids or promotion_other.promotion_id.apply_all_pos_config == True:
                            ids_other.append(promotion_other.promotion_id.id)
                    domain = ['|', '|', '&', '&', '&', '&',
                              ('id', 'in', ids), ('end_date', '>=', date),
                              ('type', '=', 'qty_price'), ('state', '=', 'active'),
                              ('apply_all_res_partner_apply', '=', True),
                              '&', '&', '&', '&','&',('check_promotion', '=', False),
                              ('end_date', '>=', date), ('type', '=', 'qty_price'), ('state', '=', 'active'),
                              ('apply_all_pos_config', '=', True), ('apply_all_res_partner_apply', '=', True),
                              '&', '&', '&',
                              ('end_date', '>=', date), ('state', '=', 'active'), ('id', 'in', ids_other),
                              ('apply_all_res_partner_apply', '=', True)]

                    list_ids = self.env['pos.promotion'].sudo().search(domain)
                    self.promotion_ids = list_ids
                    return {'domain': {'promotion_id': domain}}
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('promotion_id')
    def _onchange_promotion_id_set_line(self):
        try:
            if self.promotion_id:
                self.button_choose = False
                if self.promotion_id.type == 'qty_price':
                    self.print_stamp_line_ids = None
                    # lấy chi tiết sản các sản phẩm trong chương trình khuyến mại
                    lines = self.env['pos.promotion.qty.price'].search(
                        [('promotion_id', '=', self.promotion_id.id)])
                    vals = []
                    for line in lines:
                        # lấy giá cũ sản phẩm price_unit
                        pricelist_item = self.env['product.pricelist.item'].sudo().search(
                            [('pricelist_id', '=', self.pricelist_id.id),
                             ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), '|',
                             ('date_end', '=', False), ('date_end', '>=', datetime.today()), '|', ('date_start', '=', False), ('date_start', '<=', datetime.today())], order='create_date desc',
                            limit=1)
                        if pricelist_item:
                            price_unit = pricelist_item.fixed_price
                        else:
                            price_unit = line.product_id.product_tmpl_id.list_price
                        price = price_unit
                        # lấy giá sau khuyến mại price
                        if line.check_discount_price == 'price':
                            price = price_unit - line.price_unit
                        elif line.check_discount_price == 'discount':
                            price = price_unit - price_unit * \
                                    (line.discount / 100)
                        # lấy tên trên tên dưới theo cấu hình
                        product_config = self.env['product.promotion.config'].sudo().search(
                            [('product_id', '=', line.product_id.id)], limit=1)

                        val = {
                            'product_id': line.product_id.id,
                            'uom_id': line.product_id.product_tmpl_id.uom_id.id,
                            'price_unit_before': price_unit,
                            'price_unit': price,
                            'packed_date': self.promotion_id.start_date,
                            'expire_date': self.promotion_id.end_date,
                            'note': line.note,
                            'name_above': product_config.name_above if product_config else None,
                            'name_below': product_config.name_below if product_config else None,
                            # 'allow_printing': False,
                        }
                        vals.append((0, 0, val))
                    self.print_stamp_line_ids = vals
                elif self.promotion_id.type != 'qty_price':
                    self.print_stamp_line_ids = None
                    other_config = self.env['product.other.config'].search(
                        [('promotion_id', '=', self.promotion_id.id)], limit=1)

                    vals = []
                    for line in other_config.other_line_ids:
                        val = {
                            'name_above': line.name_above,
                            'name_below': line.name_below,
                            'uom_id': line.uom_id,
                            'price_unit_before': line.price_unit_before,
                            'price_unit': line.price_unit,
                            'packed_date': line.packed_date,
                            'expire_date': line.expire_date,
                            'note': line.note,
                            # 'allow_printing': False,
                        }
                        vals.append((0, 0, val))
                    self.print_stamp_line_ids = vals
        except Exception as e:
            raise ValidationError(e)

    def action_choose_all(self):
        try:
            self.button_choose = True
            for line in self.print_stamp_line_ids:
                line.allow_printing = True
        except Exception as e:
            raise ValidationError(e)

    def action_unchoose_all(self):
        try:
            for line in self.print_stamp_line_ids:
                line.allow_printing = False
            self.button_choose = False
        except Exception as e:
            raise ValidationError(e)

    def print_stamp_shelf(self):
        try:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_print_stamp_product.report_print_stamp_shelf_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        except Exception as e:
            raise ValidationError(e)

    def print_stamp_shelf_product(self):
        try:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_print_stamp_product.report_print_stamp_shelf_product_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        except Exception as e:
            raise ValidationError(e)

    def print_stamp_product(self):
        try:
            list_product_errors = []
            for line in self.print_stamp_line_ids:
                if not line.product_id.product_tmpl_id.x_print_stamp and not line.product_id.product_tmpl_id.x_is_combo :
                    list_product_errors.append(
                        line.product_id.product_tmpl_id.name)

            mess_error = ' , '.join([str(err) for err in list_product_errors])
            if len(mess_error) != 0:
                raise UserError(_('Product not print stamp: (%s)') %
                                str(mess_error))
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_print_stamp_product.report_print_stamp_product_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        except Exception as e:
            raise ValidationError(e)

    def print_stamp_promotion(self):
        try:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_print_stamp_product.report_print_stamp_promotion_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        except Exception as e:
            raise ValidationError(e)
