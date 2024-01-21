# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class TypeSendZns(models.Model):
    _name = 'type.send.zns'
    _description = 'Type send request zns'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    token = fields.Char('Token', required=True)
    active = fields.Boolean('Active Send', default=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Code must be unique'),
    ]

    def get_send_zns_action_type(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id)])
            return {
                'name': self.display_name,
                'type': 'ir.actions.act_window',
                'res_model': 'zns.information',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', zns_info_ids.ids)],
                'target': 'current',
            }
        except Exception as e:
            raise ValidationError(e)

    def get_action_zns_tree_draft(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id), ('state', '=', 'draft')])
            action = self._get_action_zns(zns_info_ids)
            return action
        except Exception as e:
            raise ValidationError(e)

    def get_action_zns_tree_queue(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id), ('state', '=', 'queue')])
            action = self._get_action_zns(zns_info_ids)
            return action
        except Exception as e:
            raise ValidationError(e)

    def get_action_zns_tree_error(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id), ('state', '=', 'error')])
            action = self._get_action_zns(zns_info_ids)
            return action
        except Exception as e:
            raise ValidationError(e)

    def get_action_zns_tree_quota(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id), ('state', '=', 'quota')])
            action = self._get_action_zns(zns_info_ids)
            return action
        except Exception as e:
            raise ValidationError(e)

    def get_action_zns_tree_done(self):
        try:
            self.ensure_one()
            zns_info_ids = self.env['zns.information'].search([('type_send_id', '=', self.id), ('state', '=', 'done')])
            action = self._get_action_zns(zns_info_ids)
            return action
        except Exception as e:
            raise ValidationError(e)

    def _get_action_zns(self, zns_infor):
        try:
            action = {
                'name': self.display_name,
                'type': 'ir.actions.act_window',
                'res_model': 'zns.information',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', zns_infor.ids)],
                'target': 'current',
            }
            return action
        except  Exception as e:
            raise ValidationError(e)
