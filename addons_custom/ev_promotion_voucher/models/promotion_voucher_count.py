from datetime import date, datetime

from odoo import models, fields, _


class PromotionVoucherCount(models.Model):
    _name = 'promotion.voucher.count'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Voucher Count'

    promotion_voucher_count_id = fields.Many2one(comodel_name='promotion.voucher', string='Promotion Voucher Reference',
                                                 ondelete='cascade')
    promotion_code = fields.Char('Promotion Code')
    pos_order_uid = fields.Char('Đơn hàng')
    date = fields.Char('Ngày sử dụng')

    def update_promotion_used(self, pos_reference, code_promotion, customer_id):
        # số bản ghi promotion code đã sử dụng trong bảng promotion.voucher.count
        record_promotion_code = self.env['promotion.voucher.count'].search([('promotion_code', '=', code_promotion)])

        # số lần sử dụng mã promotion code
        promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
        promotion_use_code = promotion_voucher_line.promotion_use_code
        promotion_voucher = promotion_voucher_line.promotion_voucher_id
        date_used = str(datetime.today().date().strftime("%d/%m/%Y"))
        self._cr.execute(
            f"""INSERT INTO promotion_voucher_count(promotion_voucher_count_id,promotion_code,pos_order_uid,date) 
                VALUES ('{promotion_voucher.id}','{code_promotion}','{pos_reference}','{date_used}')""")
        promotion_voucher_count_records = self.env['promotion.voucher.count'].search(
            [('promotion_voucher_count_id', '=', promotion_voucher.id)])
        count_code = 0  # số mã code trong bảng tạm
        for rc in promotion_voucher_count_records:
            if code_promotion == rc.promotion_code:
                count_code += 1
        lines = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])

        count_code_use = promotion_voucher.promotion_use_code - count_code


        if lines.promotion_use_code == 1:
            lines.state_promotion_code = 'used'
            lines.promotion_use_code = 0
        else:
            lines.promotion_use_code = count_code_use

    def delete_promotion_code_used(self, pos_reference, code_promotion):
        promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
        promotion_voucher = promotion_voucher_line.promotion_voucher_id
        self._cr.execute(
            f"""DELETE FROM promotion_voucher_count 
                WHERE promotion_code = '{code_promotion}' 
                and pos_order_uid='{pos_reference}'""")
        promotion_voucher_count_records = self.env['promotion.voucher.count'].search(
            [('promotion_voucher_count_id', '=', promotion_voucher.id)])
        count_code = 0
        for rc in promotion_voucher_count_records:
            if code_promotion == rc.promotion_code:
                count_code += 1
        lines = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
        count_code_use = promotion_voucher.promotion_use_code - count_code
        if lines.promotion_use_code == 0:
            lines.state_promotion_code = 'available'
            lines.promotion_use_code = 1
        else:
            lines.promotion_use_code = count_code_use

    def check_promotion_code(self, pos_reference, code_promotion, customer_id):
        # số bản ghi promotion code đã sử dụng trong bảng promotion.voucher.count
        print('1-1')
        record_promotion_code = self.env['promotion.voucher.count'].search([('promotion_code', '=', code_promotion)])
        length_code_table = len(record_promotion_code)
        promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
        # promotion_use_code = promotion_voucher_line.promotion_use_code
        promotion_use_code = promotion_voucher_line.promotion_voucher_id.promotion_use_code
        data = {}
        promotion_voucher_lines = self.search([])
        if promotion_voucher_line.id != False:
            record_same_pr_code = self.env['promotion.voucher.count'].search(
                [('pos_order_uid', '=', pos_reference),('promotion_voucher_count_id','=', promotion_voucher_line.promotion_voucher_id.id)])
        else:
            record_same_pr_code = []
        lot_id = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)], limit=1)
        if not lot_id:
            data['type'] = 'existed'
            data['message'] = _('Code "%s" not exist in database. Please check!') %code_promotion
            return data
        if lot_id.state_promotion_code != 'available':
            data['type'] = 'not_activated'
            data[
                'message'] = _('Code "%s" not use promotion. Please check!') %code_promotion
            return data
        if length_code_table == promotion_use_code:
            data['type'] = 'not_exp'
            data[
                'message'] = _('Code "%s" not use promotion. Please check!') %code_promotion
            return data
        if len(record_same_pr_code) > 0:
            data['type'] = 'not_exp'
            data['message'] = _('Order used promotion code. Please check!')
            return data
        if lot_id.expired_date and lot_id.expired_date < date.today():
            data['type'] = 'not_exp'
            data['message'] = _('Code "%s" expired date.') % lot_id.name
            return data
        data = {
            'type': 'valid',
            'promotion_id': lot_id.promotion_voucher_id.promotion_id.type,
            'lot_id': lot_id.id,
            'get_promotion_id': lot_id.promotion_voucher_id.promotion_id.id,
            'code_promotion': lot_id.name
        }
        return data
