# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ZNSTemplate(models.Model):
    _name = 'zns.template'
    _description = 'Zalo Notification Service Template'
    _rec_name = 'template_name'
    _order = 'create_date desc'

    template_id = fields.Char('Template ID', required=True)
    template_name = fields.Char('Template Name', required=True)
    app_id = fields.Char('App ID', required=True)
    # oa_id = fields.Char('OA ID', required=True)
    created_time = fields.Float('Created Time', default=0)
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

    timeout = fields.Float('Time Out', default=0)
    preview_url = fields.Char('Preview URL')
    price = fields.Float('Price', default=0)
    apply_template_quota = fields.Boolean('Apply Template Quota')
    template_daily_quota = fields.Integer('Template Daily Quota')
    template_remaining_quota = fields.Integer('Template Remaining Quota')

    template_tag = fields.Selection([
        ('otp', 'OTP'),
        ('in_transaction', 'In Transaction'),
        ('post_transaction', 'Post Transaction'),
        ('account_update', 'Account Update'),
        ('general_update', 'General Update'),
        ('follow_up', 'Follow up')]
        , 'Template Tag', default=None)

    list_params = fields.One2many('zns.template.param', 'zns_template_id')

    _sql_constraints = [
        ('template_id_uniq', 'unique(template_id)', 'The template id  already exists in the system!'),
    ]
