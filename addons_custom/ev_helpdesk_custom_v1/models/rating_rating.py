# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.modules.module import get_resource_path
import base64

RATING_LIMIT_HIGHLY_SATISFIED = 5
RATING_LIMIT_SATISFIED = 4
RATING_LIMIT_NOT_SATISFIED = 3
RATING_LIMIT_DISSATISFIED = 2
RATING_LIMIT_HIGHLY_DISSATISFIED = 1


class RatingRating(models.Model):
    _inherit = 'rating.rating'

    rating_text = fields.Selection(selection_add=[
        ('highly_satisfied', 'Highly Satisfied'),
        ('dissatisfied', 'Dissatisfied')])

    def _get_rating_image_filename(self):
        self.ensure_one()
        if self.rating >= RATING_LIMIT_HIGHLY_SATISFIED:
            rating_int = 5
        elif self.rating >= RATING_LIMIT_SATISFIED:
            rating_int = 4
        elif self.rating >= RATING_LIMIT_NOT_SATISFIED:
            rating_int = 3
        elif self.rating >= RATING_LIMIT_DISSATISFIED:
            rating_int = 2
        elif self.rating >= RATING_LIMIT_HIGHLY_DISSATISFIED:
            rating_int = 1
        else:
            rating_int = 0
        return '%s.png' % rating_int

    def _compute_rating_image(self):
        for rating in self:
            try:
                image_path = get_resource_path('ev_helpdesk_custom_v1', 'static/img',
                                               rating._get_rating_image_filename())
                rating.write({
                    'rating_image': base64.b64encode(
                        open(image_path, 'rb').read()) if image_path else False
                })
            except (IOError, OSError):
                rating.rating_image = False

    @api.depends('rating')
    def _compute_rating_text(self):
        for rating in self:
            if rating.rating >= RATING_LIMIT_HIGHLY_SATISFIED:
                rating.rating_text = 'highly_satisfied'
            elif rating.rating >= RATING_LIMIT_SATISFIED:
                rating.rating_text = 'satisfied'
            elif rating.rating >= RATING_LIMIT_NOT_SATISFIED:
                rating.rating_text = 'not_satisfied'
            elif rating.rating >= RATING_LIMIT_DISSATISFIED:
                rating.rating_text = 'dissatisfied'
            elif rating.rating >= RATING_LIMIT_HIGHLY_DISSATISFIED:
                rating.rating_text = 'highly_dissatisfied'
            else:
                rating.rating_text = 'no_rating'
