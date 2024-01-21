# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SlidePartnerRelation(models.Model):
    _inherit = 'slide.slide.partner'

    def _compute_field_value(self, field):
        super()._compute_field_value(field)
        if field.name == 'survey_scoring_success':
            for record in self:
                record.write({'completed': True if record.survey_scoring_success else False})

    def write(self, values):
        res = super(SlidePartnerRelation, self).write(values)
        if 'completed' in values:
            for record in self:
                record._set_completed_callback()
        return res