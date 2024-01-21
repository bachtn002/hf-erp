# -*- coding: utf-8 -*-
import ast

from odoo import models, _
from odoo.exceptions import ValidationError

from ...ev_zalo_notification_service.helpers import APIZNS


class DataWebhookZNS(models.Model):
    _inherit = 'data.webhook.zns'

    def action_parsing(self, sender, msg_id, text):
        try:
            syntax = text.split(' ')[0]
            value = text.split(' ')[1] if len(text.split(' ')) > 1 else ''
            syntax_map_partner = self.env['ir.config_parameter'].sudo().get_param('syntax_map_partner')
            syntax_search_point = self.env['ir.config_parameter'].sudo().get_param('syntax_search_point')
            syntax_otp = self.env['ir.config_parameter'].sudo().get_param('syntax_otp_map')

            syntax_promotion_code = self.env['ir.config_parameter'].sudo().get_param('syntax_promotion_code')

            if syntax == syntax_map_partner:
                self.action_send_otp(sender, msg_id, value)
            elif syntax == syntax_search_point:
                self.action_search_point(sender, msg_id)
            elif syntax == syntax_otp:
                self.action_map_partner(sender, msg_id, value)
            elif syntax == syntax_promotion_code:
                self.action_search_promotion_code(sender, msg_id)
            else:
                msg = _('Lỗi cú pháp. Bạn vui lòng kiểm tra lại cú pháp!')
                self.send_feedback_message(sender, msg_id, msg)
                return
        except Exception as e:
            raise ValidationError(e)

    def action_search_promotion_code(self, sender, msg_id):
        try:
            data_webhook = ast.literal_eval(self.data)
            app_id = data_webhook.get('app_id')
            oa_id = data_webhook.get('recipient').get('id')
            check_follow = APIZNS.get_profile(sender, app_id, oa_id)
            if not check_follow:
                msg = _('Bạn hãy quan tâm Zalo Homefarm để thực hiện chức năng này')
                self.send_feedback_message_follow(sender, msg_id, msg)
                return

            zalo_id = self.check_partner(sender)
            if not zalo_id:
                msg = _('Bạn cần đăng ký liên kết tài khoản để thực hiện chức năng này.\n'
                        'Để đăng ký tài khoản, vui lòng soạn tin và gửi theo cú pháp: #dk + khoảng trắng + số điện thoại.\n'
                        'Ví dụ: #dk 0900000001')
                self.send_feedback_message(sender, msg_id, msg)
                return

            query = """
                SELECT a.promotion_code, b.x_condition_apply, 
                        case
                           when b.date - c.start_date >= 0 then to_char(b.date, 'dd-mm-yyyy')
                           else to_char(c.start_date, 'dd-mm-yyyy') end as begin_date,
                       case
                           when b.expired_date is null then to_char(c.end_date, 'dd-mm-yyyy')
                           when b.expired_date - c.end_date <= 0 then to_char(b.expired_date, 'dd-mm-yyyy')
                           else to_char(c.end_date, 'dd-mm-yyyy') end   as expired_date
                from phone_promotion_list a
                         join promotion_voucher b on b.id = a.promotion_voucher_id
                         join pos_promotion c on c.id = b.promotion_id
                where a.phone = '%s'
                  and a.state = 'available'
                  and b.state = 'active'
                  and (b.expired_date is null or b.expired_date::date >= now()::date)
                  and c.state = 'active'
                  and c.end_date::date >= now()::date
            """
            self.env.cr.execute(query % zalo_id.phone)
            values = self.env.cr.dictfetchall()
            if values:
                for val in values:
                    code = val.get('promotion_code')
                    condition = val.get('x_condition_apply')
                    date = val.get('begin_date')
                    expired_date = val.get('expired_date')
                    msg = _('Bạn có mã ưu đãi: %s. Điều kiện áp dụng: %s. Thời hạn: %s đến %s') % (
                    code, condition, date, expired_date)
                    # title = _("Bấm để sử dụng code %s") % code
                    # link = "https://portal.homefarm.vn/barcode/?code=" + str(code) + "&zaloId=" + str(sender)
                    # self.send_message_attachment(sender, msg_id, msg, title, link)
                    self.send_feedback_message(sender, msg_id, msg)
            else:
                msg = _('Rất tiếc, bạn không có mã ưu đãi nào.')
                self.send_feedback_message(sender, msg_id, msg)
                return
            return
        except Exception as e:
            raise ValidationError(e)
