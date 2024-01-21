# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ZNSTemplateLine(models.Model):
    _name = 'zns.template.line'
    _description = 'Zalo Notification Service Template Detail'
    _rec_name = 'template_name'
    _order = 'create_date desc'

    template_id = fields.Many2one('zns.template', 'Template ID', required=True)
    template_name = fields.Char('Template Name')
    timeout = fields.Float('Time Out', default=0)
    preview_url = fields.Char('Preview URL')
    price = fields.Float('Price', default=0)
    apply_template_quota = fields.Boolean('Apply Template Quota')
    template_daily_quota = fields.Integer('Template Daily Quota')
    template_remaining_quota = fields.Integer('Template Remaining Quota')
    status = fields.Selection([
        ('deleted', 'Deleted'),
        ('pending_review', 'Pending Review'),
        ('disable', 'Disable'),
        ('enable', 'Enable'),
        ('reject', 'Reject')]
        , 'State', default=None)
    template_quality = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('undefined', 'Undefined')]
        , 'Template Quality', default=None)
    template_tag = fields.Selection([
        ('otp', 'OTP'),
        ('in_transaction', 'In Transaction'),
        ('post_transaction', 'Post Transaction'),
        ('account_update', 'Account Update'),
        ('general_update', 'General Update')]
        , 'Template Tag', default=None)

    list_params = fields.One2many('zns.template.param', 'zns_template_line_id')
