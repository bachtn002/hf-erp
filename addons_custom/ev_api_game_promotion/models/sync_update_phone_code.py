import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ...ev_zalo_notification_service.helpers import APIGetToken


class SyncUpdatePhoneCode(models.Model):
    _name = 'sync.update.phone.code'
    _description = 'Sync Update Phone Code'
    _order = 'id desc'

    phone = fields.Char("Customer phone number")
    promotion_code = fields.Char("Promotion code")
    apply_condition = fields.Text("Apply condition")
    token_connect_api = fields.Text("Token API")
    remote_ip = fields.Char("Remote IP")
    message_response = fields.Text("Message")
    message_zns_response = fields.Text("Message ZNS response")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('error', 'Error'),
        ('done', 'Done')],
        'State', default='draft')

    def action_send_promotion_code_zalo(self, phone, msg):
        try:
            zalo_id = self.env['res.partner.zalo'].sudo().search([('phone', '=', phone)], limit=1)
            # msg_id = self.env['data.webhook.zns'].sudo().search([('zalo_id', '=', zalo_id.zalo_id)], limit=1).msg_id
            if not zalo_id:
                mesage = _("Zalo partner is not mapping")
                return mesage
            token = APIGetToken.get_access_token(zalo_id.oa_id, zalo_id.app_id)
            if not token:
                mesage = _("Token is not found")
                return mesage
            url = 'https://openapi.zalo.me/v3.0/oa/message/cs'
            data = {
                'recipient': {
                    # 'message_id': msg_id,
                    'user_id': zalo_id.zalo_id
                },
                'message': {
                    'text': msg
                }
            }
            response = requests.post(url, data=json.dumps(data),
                                     headers={'Content-Type': 'application/json',
                                              'access_token': token,
                                              })
            response = response.json()
            message = response.get('message')
            return message
        except Exception as error:
            return error
            # raise ValidationError(e)

    def action_sync_promotion_code(self):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_minigame_api_sync', max_retries=3)._action_sync_phone_code()
        except Exception as e:
            raise ValidationError(e)

    def _action_sync_phone_code(self):
        promotion_code = self.env['promotion.voucher.line'].search([('name', '=', self.promotion_code)])
        check_valid_data = False
        message_response = ""
        message_customer_response = (_("Chúc mừng bạn nhận được mã ưu đãi: %s. %s") % (self.promotion_code, self.apply_condition))
        if promotion_code:
            phone = self.phone.replace(' ', '')
            if len(self.phone) < 6 or len(self.phone) > 15:
                message_response = _("Phone number length must be between [6,15]")
            else:
                # Check trạng thái mã code
                if promotion_code.state_promotion_code in ['available', 'active']:
                    code = self.promotion_code.replace(' ', '')
                    # cho phép 1 số điện thoại nhiều mã (khác nhau) chặn trường hợp nhiều hơn 1 dòng cùng mã cùng số điện thoại
                    phone_line = self.env['phone.promotion.list'].sudo().search(
                        [('phone', '=', phone), ('promotion_code', '=', code)])
                    code_lines = self.env['phone.promotion.list'].sudo().search(
                        [('promotion_code', '=', code), ('state', '=', 'available')])

                    # Khong phan bo qua so lan su dung
                    if promotion_code.promotion_use_code > len(code_lines) and not phone_line:
                        self.env['phone.promotion.list'].sudo().create({
                            'promotion_code': code,
                            'phone': phone,
                            'state': 'available',
                            'promotion_voucher_id': promotion_code.promotion_voucher_id.id,
                        })
                        # khong gán lại đk áp dụng gửi từ api update phone code
                        # promotion_code.promotion_voucher_id.x_condition_apply = self.apply_condition
                        check_valid_data = True
                    else:
                        message_response = _("Promotion code already maps with other phone number or time use is invalid")
                else:
                    message_response = _("Promotion code is unavailable")
        else:
            message_response = _("Promotion code is not exist")
            # code ko tồn tại trên odoo vẫn gửi tin ZNS do có những code đối tác tặng và sẽ đưa vào game để quay
            # Code ko áp dụng trên POS và chỉ code đó chỉ áp dụng trên app của đối tác (VNPAY...)
            message_zns_response = self.action_send_promotion_code_zalo(self.phone, message_customer_response)
            self.state = 'done'
            self.message_zns_response = message_zns_response
            self.message_response = message_response
            return
        self.message_response = message_response
        if check_valid_data:
            message_zns_response = self.action_send_promotion_code_zalo(self.phone, message_customer_response)
            self.state = 'done'
            self.message_zns_response = message_zns_response
        else:
            self.state = 'error'

