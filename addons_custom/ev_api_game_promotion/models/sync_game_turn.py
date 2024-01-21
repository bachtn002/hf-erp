from time import sleep
from odoo import fields, models
from odoo.exceptions import ValidationError

import requests
import json


class SyncGameTurn(models.Model):
    _name = 'sync.game.turn'
    _rec_name = 'pos_order_ref'
    _description = "Sync Game Turn"
    _order = 'id desc'

    pos_order_ref = fields.Char("Post order ref")
    campaign_code = fields.Char("Game code")
    phone = fields.Char("Customer phone number")
    turn = fields.Char("Game turn reward")
    partner_id = fields.Char("Partner id ref")
    hash_value = fields.Text("Hash value")
    message_response = fields.Text("Message external response")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('error', 'Error'),
        ('done', 'Done')],
        'State', default='draft')

    def action_call_api_sync(self):
        try:
            # allow push recordset to queue cause we need to make sure game reward history must be saved first
            for re in self:
                if re.state == 'draft':
                    re.state = 'queue'
                    re.sudo().with_delay(channel='root.action_minigame_api_sync', max_retries=3)._action_sync_game_turn()
        except Exception as e:
            raise ValidationError(e)

    def _action_sync_game_turn(self):
        retry_times = 2
        while (retry_times > 0):
            try:
                base_url = self.env['ir.config_parameter'].sudo().get_param('url_api_mini_game')
                api_key = self.env['ir.config_parameter'].sudo().get_param('X-API-KEY')
                url = base_url + '/api/import-player'
                header = {
                    'Content-Type': 'application/json',
                    'X-API-KEY': api_key,
                }
                data = {}

                data['campaignCode'] = self.campaign_code
                data['phone'] = self.phone
                data['turn'] = self.turn
                data['partnerId'] = self.partner_id
                data['referenceCode'] = self.pos_order_ref
                data['hashValue'] = self.hash_value

                response = requests.post(url, data=json.dumps(data),
                                         headers=header,
                                         verify=False)
                response_json = response.json()
                retry_times -= 2
                if response_json['code'] != 200:
                    self.message_response = str(response_json['code']) + ":" + str(response_json['message'])
                    self.state = 'error'
                else:
                    self.message_response = str(response_json['code']) + ":" + str(response_json['message'])
                    self.state = 'done'
            except requests.exceptions.ConnectionError as e:
                retry_times -= 1
                # if we run out of times retry then raise error instead
                if retry_times == 0:
                    raise ValidationError(e)
                sleep(1)
                continue
            except Exception as e:
                raise ValidationError(e)
