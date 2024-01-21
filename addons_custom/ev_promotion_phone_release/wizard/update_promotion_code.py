from odoo import api, fields, models


class UpdatePromotionCode(models.TransientModel):
    _inherit = 'update.promotion.code'

    promotion_voucher_types = fields.Selection(string="Promotion Release type",
                                             selection=[('standard', 'Standard'), ('phone', 'Phone')])
    condition_apply = fields.Text("Condition Apply")

    def action_update(self):
        promotion_code = self.env['promotion.voucher'].browse(self._context.get('active_id'))
        if self.condition_apply:
            promotion_code.x_condition_apply = self.condition_apply
        return super(UpdatePromotionCode, self).action_update()
