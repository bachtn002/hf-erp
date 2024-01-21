# -*- coding: utf-8 -*-
import requests

from datetime import datetime

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from ...ev_zalo_notification_service.helpers import APIGetToken
import logging

_logger = logging.getLogger(__name__)


class ParamGetTemplate(models.TransientModel):
    _name = 'param.rate.zns'
    _description = 'Create a Param get list zns'

    from_date = fields.Datetime('From Date', required=True)
    to_date = fields.Datetime('To Date', required=True)
    offset = fields.Integer('Offset', help='The order of the first rate in the returned list')
    limit = fields.Integer('Limit', help='Maximum 10000')

    def get_rate(self):
        try:
            url = 'https://business.openapi.zalo.me/rating/get'
            if self.limit > 10000:
                raise UserError(_('Limit must be less than 10000'))
            template_id = self.env['zns.template'].browse(self._context.get('active_id'))

            zalo_oa = self.env['zalo.official.account'].sudo().search(
                [('oa_id', '=', template_id.oa_id), ('app_id', '=', template_id.app_id)])
            if not zalo_oa:
                raise UserError(_("Can not find Zalo OA corresponse with template %s and app %s ") % (template_id.template_id, template_id.app_id))

            token = APIGetToken.get_access_token(template_id.oa_id, template_id.app_id)
            from_time = int(self.from_date.timestamp() * 1000)
            to_time = int(self.to_date.timestamp() * 1000)

            params = {
                'template_id': template_id.template_id,
                'from_time': from_time,
                'to_time': to_time,
                'offset': 0,
                'limit': self.limit if self.limit else 0
            }

            response = requests.get(url=url, params=params, headers={'Content-Type': 'application/json',
                                                                     'access_token': token})
            if response.status_code == 200:
                response = response.json()
                if response.get('error') != 0:
                    raise UserError(_("Error: %s") %response.get('message'))
                if len(response.get('data').get('data')) <= 0:
                    return

                for dt in response.get('data').get('data'):
                    msg_id = dt.get('msgId')
                    tracking_id = dt.get('trackingId')
                    oa_id = dt.get('oaId')
                    ms = float(dt.get('submitDate'))
                    submit_date = datetime.fromtimestamp(ms / 1000.0)
                    # Sangnt cmt cho phep kh danh gia nhieu lan
                    rate_zns = self.env['rate.zns'].search([('msg_id', '=', msg_id), ('submit_date', '=', submit_date)])
                    if rate_zns:
                        continue

                    vals = {
                        'template_id': template_id.template_id,
                        'note': dt.get('note'),
                        'rate': dt.get('rate'),
                        'msg_id': msg_id,
                        'feed_back': dt.get('feedbacks'),
                        'tracking_id': tracking_id,
                        'submit_date': submit_date,
                        'oa_id': oa_id,
                    }
                    self.env['rate.zns'].create(vals)
        except Exception as e:
            raise ValidationError(e)
