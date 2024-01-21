from odoo import models, fields


class CampaignPromotionLine(models.Model):
    _name = 'campaign.promotion.line'
    _inherit = [
        'mail.thread'
    ]
    campaign_promotion_id = fields.Many2one(comodel_name='campaign.promotion', string='Campaign Promotion Reference',
                                            ondelete='cascade')
    promotion = fields.Many2one('pos.promotion', string='Chương trình khuyến mại', required=True)
