# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import math
import re
import time
import traceback

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class Currency(models.Model):
    _inherit = "res.currency"

    x_base_currency_id = fields.Many2one('res.currency', 'Base Currency')
