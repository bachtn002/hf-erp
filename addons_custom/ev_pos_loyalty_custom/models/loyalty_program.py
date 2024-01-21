# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    x_money_per_point = fields.Integer(string='Money Per Point (VND)', digits=0,
                                       help=_('The amount corresponding to 1 point'))
    x_point_cost = fields.Float('Point Cost', help=_('Point used'))
    x_discount_amount = fields.Float('Discount Amount', help=_('Amount to be exchanged for points'))
    product_id = fields.Many2one('product.product', string='Product',
                                 help=_("Use to calculate promotion value. Type is service"))
    product_rule = fields.Many2many('product.product', 'loyalty_program_rel', string='Sản phẩm')
    product_cate_rule = fields.Many2many('product.category', string='Loại sản phẩm')
    valid_product_ids = fields.One2many('product.product', compute='_compute_valid_product')
    res_partner_id_not_apply = fields.Many2many('res.partner', string='Customer Not Apply')
    res_partner_id_not_apply_group = fields.Many2many('res.partner.group', string='Customer Not Apply Group')
    pos_config_apply = fields.Many2many('pos.config', string='Pos Apply')
    # pos_config_apply = fields.Many2many('pos.config', string='Pos Apply',domain=[('loyalty_id', '=', False)], store = True)

    @api.constrains('pos_config_apply')
    def check_pos(self):
        for pos_rc in self.pos_config_apply:
            # self._cr.execute(f"""SELECT * FROM loyalty_program_pos_config_rel""")
            # pos_config_ids = self._cr.fetchall()
            # pos_config = []
            # for pos in pos_config_ids:
            #     if pos[1] == pos_rc.id:
            #         pos_config.append(pos)
            # pos_config_delete = []
            # for pos in pos_config:
            #     if pos[0] != self.id:
            #         pos_config_delete.append(pos)
            # if len(pos_config_delete) > 0:
            #     for pos_dl in pos_config_delete:
            #         sql = """
            #                     DELETE FROM loyalty_program_pos_config_rel
            #                     WHERE loyalty_program_id = %s AND  pos_config_id = %s;
            #                                         """
            #         self._cr.execute(sql, (pos_dl[0], pos_dl[1],))
            pos_rc.loyalty_id = self
        self._cr.execute(f"""SELECT * FROM loyalty_program_pos_config_rel WHERE loyalty_program_id ={self.id}""")
        pos_config_ids = self._cr.fetchall()
        pos_config_apply_loyalty = []
        for pc in pos_config_ids:
            pos_config_apply_loyalty.append(pc[1])
        loyalty_ids = self.env['pos.config'].search([('loyalty_id','=', self.id)])
        pos_config_all = []
        for loyalty_id in loyalty_ids:
            pos_config_all.append(loyalty_id.id)
        pos_config_delete = []
        for pc in pos_config_all:
            if pc not in pos_config_apply_loyalty:
                pos_config_delete.append(pc)
        for pc in pos_config_delete:
            pos_config = self.env['pos.config'].search([('id','=', pc)])
            pos_config.loyalty_id = False

    @api.onchange('x_money_per_point')
    def _onchange_x_money_per_point(self):
        if self.x_money_per_point:
            self.points = self.x_money_per_point and (1.0 / self.x_money_per_point) or 0.0
            print(self.points)

    @api.depends('product_rule')
    def _compute_valid_product(self):
        print('product_rule', self.product_rule)

    # @api.depends('points')
    # def _compute_x_money_per_point(self):
    #     for loyalty in self:
    #         loyalty.x_money_per_point = loyalty.points and (1.0 / loyalty.points) or 0.0
    #
    @api.model
    def create(self, values):
        res = super(LoyaltyProgram, self).create(values)
        # product_km = self.env['product.product'].search([('default_code', '=', 'Giảm trừ điểm tích lũy')])
        # if len(product_km) > 0:
        #     values['product_id'] = product_km.id
        # else:
        #     self.env['product.template'].create({
        #         'name': 'Giảm trừ điểm tích lũy',
        #         'default_code': 'Giảm trừ điểm tích lũy',
        #         'type': 'service',
        #         'sale_ok': True,
        #         'purchase_ok': True,
        #         'available_in_pos': True
        #     })
        #     self.env.cr.commit()
        #     product_km_add = self.env['product.product'].search([('default_code', '=', 'Giảm trừ điểm tích lũy')])
        #     values['product_id'] = product_km_add.id

        x_money_per_point = values.pop('x_money_per_point')
        values['points'] = x_money_per_point and (1.0 / x_money_per_point) or 0.0
        return res

    def write(self, values):
        res = super(LoyaltyProgram, self).write(values)
        if 'x_money_per_point' in values:
            x_money_per_point = values.pop('x_money_per_point')
            # values['points'] = x_money_per_point and (1.0 / x_money_per_point) or 0.0
            self.points = x_money_per_point and (1.0 / x_money_per_point) or 0.0
        return res

    @api.constrains('res_partner_id_not_apply_group')
    def add_res_partner_group(self):
        self.res_partner_id_not_apply = self.res_partner_id_not_apply_group.x_partner_ids
