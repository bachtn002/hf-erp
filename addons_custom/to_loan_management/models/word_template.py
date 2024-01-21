from dateutil import rrule

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class WordTemplate(models.Model):
    _name = 'word.template'

    _rec_name = 'name_display'
    name_display = fields.Char('Name Display')
    file_name = fields.Char('Name')
    file_data = fields.Binary("Data")
