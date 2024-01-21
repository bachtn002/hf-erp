# -*- coding: utf-8 -*-
from odoo import models, fields, _


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    x_day_to_complete = fields.Float(string="Day to complete")

class ChannelUsersRelation(models.Model):
    _inherit = 'slide.channel.partner'

    def _recompute_completion(self):
        read_group_res = self.env['slide.slide.partner'].sudo().read_group(
            ['&', '&', ('channel_id', 'in', self.mapped('channel_id').ids),
             ('partner_id', 'in', self.mapped('partner_id').ids),
             ('completed', '=', True),
             ('slide_id.is_published', '=', True),
             ('slide_id.active', '=', True)],
            ['channel_id', 'partner_id'],
            groupby=['channel_id', 'partner_id'], lazy=False)
        mapped_data = dict()
        for item in read_group_res:
            mapped_data.setdefault(item['channel_id'][0], dict())
            mapped_data[item['channel_id'][0]][item['partner_id'][0]] = item['__count']

        partner_karma = dict.fromkeys(self.mapped('partner_id').ids, 0)
        for record in self:
            record.completed_slides_count = mapped_data.get(record.channel_id.id, dict()).get(record.partner_id.id, 0)
            record.completion = round(100.0 * record.completed_slides_count / (record.channel_id.total_slides or 1))
            record.completed = record.completion == 100
            if not record.completed and record.channel_id.active and record.completed_slides_count >= record.channel_id.total_slides:
                partner_karma[record.partner_id.id] += record.channel_id.karma_gen_channel_finish

        partner_karma = {partner_id: karma_to_add
                         for partner_id, karma_to_add in partner_karma.items() if karma_to_add > 0}

        if partner_karma:
            users = self.env['res.users'].sudo().search([('partner_id', 'in', list(partner_karma.keys()))])
            for user in users:
                users.add_karma(partner_karma[user.partner_id.id])