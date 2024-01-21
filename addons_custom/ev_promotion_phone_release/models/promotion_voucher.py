from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PromotionVoucher(models.Model):
    _inherit = 'promotion.voucher'

    x_release_phone_types = fields.Selection(string="Promotion Release type",
                                             selection=[('standard', 'Standard'), ('phone', 'Phone')],
                                             default='standard', tracking=True)
    x_phone_promotion_list_ids = fields.One2many('phone.promotion.list', 'promotion_voucher_id', "Phone promotion list")
    x_is_phone_release = fields.Boolean("Is phone release?")
    x_condition_apply = fields.Text('Condition Apply')

    def action_active_confirm(self):
        if self.x_release_phone_types == 'phone' and any(not line.promotion_code for line in self.x_phone_promotion_list_ids):
            raise UserError(_("You need to match phone number with promotion code before active the program!"))

        message = _("Are you sure you want to enable all in-release Promotion Voucher?")
        return {
            'name': _("Message confirm"),
            'type': 'ir.actions.act_window',
            'res_model': 'promotion.voucher.confirm',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_promotion_voucher_id': self.id, 'default_message': message},
            'target': 'new',
        }

    def update_promotion_code_info(self):
        promotion_voucher_types = self.x_release_phone_types
        return {
            'name': _("Update promotion code"),
            'type': 'ir.actions.act_window',
            'res_model': 'update.promotion.code',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_promotion_voucher_types': promotion_voucher_types},
            'target': 'new',
        }

    def import_phone_apply(self):
        # Import danh sach SDT
        return {
            'name': _("Import Phone number"),
            'type': 'ir.actions.act_window',
            'res_model': 'import.phone.promotion.release',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_promotion_voucher_id': self.id, 'default_file_import_type': 'phone'},
            'target': 'new',
        }

    def import_phone_code_apply(self):
        # Import SDT đã phân bổ code
        return {
            'name': _("Import Phone Code number"),
            'type': 'ir.actions.act_window',
            'res_model': 'import.phone.promotion.release',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_promotion_voucher_id': self.id, 'default_file_import_type': 'phone_code'},
            'target': 'new',
        }

    def print_promotion_code_phone(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/promotion.code.phone/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    # button phan bo
    def action_match_phone_with_code(self):
        if self.x_phone_promotion_list_ids and self.promotion_voucher_line:
            list_codes = []
            for voucher in self.promotion_voucher_line:
                number_user = voucher.promotion_use_code
                while number_user > 0:
                    list_codes.append(voucher.name)
                    number_user -= 1
            index = 0
            for line in self.x_phone_promotion_list_ids:
                line.promotion_code = list_codes[index]
                line.state = 'available'
                index += 1
            self.x_is_phone_release = True
        else:
            raise UserError(_("There is no line to match phone number with code"))

    def action_cancel(self):
        for phone in self.x_phone_promotion_list_ids:
            phone.state = 'cancel'
        return super(PromotionVoucher, self).action_cancel()