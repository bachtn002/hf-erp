from odoo import models, fields, api


class PosPromotionCustom(models.Model):
    _inherit = 'pos.promotion'
    campaign_promotion = fields.Many2one('campaign.promotion', string='Chiến dịch', readonly=0)

    def write(self, vals):
        return super(PosPromotionCustom, self).write(vals)
