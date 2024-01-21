from odoo import models, fields, api


class CampaignPromotion(models.Model):
    _name = 'campaign.promotion'
    _inherit = [
        'mail.thread'
    ]
    name = fields.Char(string='Campaign Name', required=True)
    date = fields.Date(string='Campaign Time', required=True, default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=1)
    campaign_promotion_line = fields.One2many(comodel_name='campaign.promotion.line',
                                              inverse_name='campaign_promotion_id',
                                              string='Campaign Promotion Lines')
    promotion = fields.One2many(comodel_name='pos.promotion',
                                inverse_name='campaign_promotion',
                                string='Chương trình khuyến mại')

    @api.model
    def create(self, vals):
        res = super(CampaignPromotion, self).create(vals)
        for line in res.campaign_promotion_line:
            line.promotion.write({'campaign_promotion': res.id})
        return res

    def write(self, vals):
        res = super(CampaignPromotion, self).write(vals)
        for line in self.campaign_promotion_line:
            line.promotion.write({'campaign_promotion': self.id})
        return res
