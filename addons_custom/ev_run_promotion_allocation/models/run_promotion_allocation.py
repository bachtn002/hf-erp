# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_tmp_promotion = fields.Float('TMP Promotion')

class RunPromotionAllocation(models.Model):
    _name = 'run.promotion.allocation'
    _description = 'Run Promotion Allocation'

    name = fields.Char('Name')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    lines = fields.One2many('run.promotion.allocation.line','allocation_id', 'Lines')
    state = fields.Selection([('draft','Draft'),('wait_backup','Wait Backup'),('wait_process','Wait Process'),('done','Done'),('cancel','Cancel')],'State', default='draft')


    def action_backup(self):
        for line in self.lines:
            line.action_backup()
        self.state = 'wait_process'


    def action_back(self):
        for line in self.lines:
            line.action_back()
        self.state = 'wait_process'

    def action_confirm_0(self):
        orders = self.env['pos.order'].search([('date_order', '>=', str(self.from_date)), ('date_order', '<=', str(self.to_date))])
        lines = []
        for order in orders:
            flag = False
            for line in order.lines:
                if line.price_subtotal_incl == 0 and line.x_is_price_promotion > 0:
                    flag = True
                if line.price_subtotal_incl > 0 and line.price_subtotal_incl < line.x_is_price_promotion:
                    flag = True
            if flag == False:
                continue

            order_args = {
                'allocation_id': self.id,
                'pos_order_id': order.id,
                'total_km': 0,
                'total_allocation': 0,
                'state': 'draft',
            }
            lines.append((0, 0, order_args))
        if len(lines) > 0:
            self.lines = lines
            self.state = 'wait_backup'

    def action_confirm_cost(self):
        orders = self.env['pos.order'].search([('date_order', '>=', str(self.from_date)), ('date_order', '<=', str(self.to_date))])
        lines = []
        for order in orders:
            flag = False
            for line in order.lines:
                if line.x_is_price_promotion == 0:
                    continue

            if flag == False:
                continue

            order_args = {
                'allocation_id': self.id,
                'pos_order_id': order.id,
                'total_km': 0,
                'total_allocation': 0,
                'state': 'draft',
            }
            lines.append((0, 0, order_args))
        if len(lines) > 0:
            self.lines = lines
            self.state = 'wait_backup'

    def action_process_0(self):
        for line in self.lines:
            line.run_allocation_amount_0()
        self.state = 'done'


    def action_confirm(self):
        orders = self.env['pos.order'].search([('date_order','>=', str(self.from_date)),('date_order','<=', str(self.to_date))])
        lines = []
        for order in orders:
            total_promotion = 0
            total_allocation = 0
            for line in order.lines:
                if line.full_product_name == 'KM':
                    total_promotion += line.price_unit
                if line.product_id.default_code == 'TL':
                    total_promotion += line.price_unit
                total_allocation += line.x_is_price_promotion
            check_allocation = round(abs(total_allocation)) - abs(total_promotion)
            if check_allocation == 0:
                continue
            order_args = {
                'allocation_id': self.id,
                'pos_order_id': order.id,
                'total_km': abs(total_promotion),
                'total_allocation': total_allocation,
                'state': 'draft',
            }
            lines.append((0, 0, order_args))

        if len(lines) > 0:
            self.lines = lines
            self.state = 'wait_backup'




    def action_process(self):
        for line in self.lines:
            check = line.run_allocation_1_()
            if check:
                line.state = 'done'
                continue
            line.run_allocation()
            line.run_allocation_tl()
            line.state = 'done'

        self.state = 'done'


    def action_cancel(self):
        self.lines.unlink()
        self.state = 'draft'

class RunPromotionAllocationLine(models.Model):
    _name = 'run.promotion.allocation.line'
    _description = 'Run Promotion Allocation Line'

    allocation_id = fields.Many2one('run.promotion.allocation','Allocation')
    pos_order_id = fields.Many2one('pos.order','Order')
    total_km = fields.Float('Total Promotion')
    total_allocation = fields.Float('Total Allocation')
    state = fields.Selection([('draft','Draft'),('process','Process'),('done','Done')],'State', default='draft')

    def action_backup(self):
        for line in self.pos_order_id.lines:
            if line.x_is_price_promotion != 0:
                line.x_tmp_promotion = line.x_is_price_promotion

    def action_back(self):
        for line in self.pos_order_id.lines:
            if line.x_tmp_promotion != 0:
                line.x_is_price_promotion = line.x_tmp_promotion

    def run_allocation_amount_0(self):
        total_promotion = 0
        for line in self.pos_order_id.lines:
            if line.price_subtotal_incl == 0 and line.x_is_price_promotion > 0:
                total_promotion += line.x_is_price_promotion
                line.x_is_price_promotion = 0
                continue
            if line.price_subtotal_incl > 0 and line.price_subtotal_incl < line.x_is_price_promotion:
                promotion_tru = line.x_is_price_promotion - line.price_subtotal_incl
                total_promotion += promotion_tru
                line.x_is_price_promotion = line.x_is_price_promotion - promotion_tru

        for line in self.pos_order_id.lines:
            if line.price_subtotal_incl > 0:
                total = line.x_is_price_promotion + total_promotion
                if total < line.price_subtotal_incl:
                    line.write({'x_is_price_promotion': line.x_is_price_promotion + total_promotion})
                    return True



    def run_allocation_1_(self):
        total_promotion = 0
        total_allocation = 0
        for line in self.pos_order_id.lines:
            if line.full_product_name == 'KM':
                total_promotion += line.price_unit
            if line.product_id.default_code == 'TL':
                total_promotion += line.price_unit
            total_allocation += line.x_is_price_promotion
        check_promotion = abs(total_promotion) - total_allocation
        if check_promotion >= 1 and check_promotion < 100:
            for line in self.pos_order_id.lines:
                if line.x_is_price_promotion > 0:
                    line.write({'x_is_price_promotion': line.x_is_price_promotion + check_promotion})
                    return True

        if check_promotion <= -1 and check_promotion > -100:
            for line in self.pos_order_id.lines:
                if line.x_is_price_promotion > 0:
                    line.write({'x_is_price_promotion': line.x_is_price_promotion + check_promotion})
                    return True
        return False


    def run_allocation_tl(self):
        if self.pos_order_id.id == 450391:
            print(450391)
        total_promotion = 0
        for line in self.pos_order_id.lines:
            if line.product_id.default_code == 'TL':
                total_promotion += line.price_unit
        if total_promotion == 0:
            return True

        total_amount = 0
        for line in self.pos_order_id.lines:
            if (line.product_id.type == 'product' and line.price_unit > 0) or (line.product_id.x_is_combo and line.price_unit > 0):
                total_amount += line.price_subtotal_incl

        sum_promotion = 0
        sum_promotion_allow = 0
        if total_amount == 0:
            return
        for line in self.pos_order_id.lines:
            if (line.product_id.type == 'product' and line.price_unit > 0) or (line.product_id.x_is_combo and line.price_unit > 0):
                tile = line.price_subtotal_incl / total_amount
                sum_promotion += round(abs(total_promotion) * tile)
                if sum_promotion <= abs(total_promotion):
                    line.x_is_price_promotion += round(abs(total_promotion) * tile)
                    sum_promotion_allow += round(abs(total_promotion) * tile)
                else:
                    line.x_is_price_promotion += abs(total_promotion) - sum_promotion_allow


    def run_allocation(self):
        if self.pos_order_id.id == 450391:
            print(450391)
        total_promotion = 0
        total_allocation = 0
        for line in self.pos_order_id.lines:
            if line.full_product_name == 'KM':
                total_promotion += line.price_unit
            total_allocation += line.x_is_price_promotion
        check_allocation = total_allocation + total_promotion
        if total_promotion == 0:
            for line in self.pos_order_id.lines:
                line.x_is_price_promotion = 0

        if check_allocation != 0 and total_promotion != 0:
            tru = total_allocation - abs(total_promotion)
            if tru >= 1 and tru < 100:
                for line in self.pos_order_id.lines:
                    if line.x_is_price_promotion > 0:
                        line.write({'x_is_price_promotion': line.x_is_price_promotion - tru})
                        return
            elif tru <= -1 and tru > -100:
                for line in self.pos_order_id.lines:
                    if line.x_is_price_promotion > 0:
                        line.write({'x_is_price_promotion': line.x_is_price_promotion + abs(tru)})
                        return
            else:
                n = abs(total_allocation/total_promotion)
                if n > 0:
                    sum_promotion = 0
                    sum_promotion_allow = 0
                    for line in self.pos_order_id.lines:
                        if line.x_is_price_promotion > 0:
                            sum_promotion += line.x_is_price_promotion / n
                            if sum_promotion <= abs(total_promotion):
                                line.x_is_price_promotion = round(line.x_is_price_promotion/n)
                                sum_promotion_allow += round(line.x_is_price_promotion/n)
                            else:
                                line.x_is_price_promotion = abs(total_promotion) - sum_promotion_allow
                elif n == 0:
                    total_amount = 0
                    for line in self.pos_order_id.lines:
                        if (line.product_id.type == 'product' and line.price_unit > 0) or (line.product_id.x_is_combo and line.price_unit > 0):
                            total_amount += line.price_subtotal_incl

                    sum_promotion = 0
                    sum_promotion_allow = 0
                    for line in self.pos_order_id.lines:
                        if (line.product_id.type == 'product' and line.price_unit > 0) or (line.product_id.x_is_combo and line.price_unit > 0):
                            tile = line.price_subtotal_incl/total_amount
                            sum_promotion += abs(total_promotion) * tile
                            if sum_promotion <= abs(total_promotion):
                                line.x_is_price_promotion = round(abs(total_promotion) * tile)
                                sum_promotion_allow += round(abs(total_promotion) * tile)
                            else:
                                line.x_is_price_promotion = abs(total_promotion) - sum_promotion_allow