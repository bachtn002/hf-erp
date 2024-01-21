# -*- coding: utf-8 -*-
import ast

from odoo import models, fields, _
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

            syntax_mini_game = self.env['ir.config_parameter'].sudo().get_param('syntax_mini_game')

            if syntax == syntax_map_partner:
                self.action_send_otp(sender, msg_id, value)
            elif syntax == syntax_search_point:
                self.action_search_point(sender, msg_id)
            elif syntax == syntax_otp:
                self.action_map_partner(sender, msg_id, value)
            elif syntax == syntax_promotion_code:
                self.action_search_promotion_code(sender, msg_id)
            elif syntax == syntax_mini_game:
                self.action_send_link_minigame(sender, msg_id)
            else:
                msg = _('Lỗi cú pháp. Bạn vui lòng kiểm tra lại cú pháp!')
                self.send_feedback_message(sender, msg_id, msg)
            return
        except Exception as e:
            raise ValidationError(e)

    def action_send_link_minigame(self, sender, msg_id):
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

            # CTKM active loại tích lũy lượt chơi
            pos_promotions = self.env['pos.promotion'].search([('type', '=', 'game_total_amount'), ('state', '=', 'active'),('end_date', '>=', fields.Date.today())])
            # Lịch sử tích lũy lượt chơi của CTKM active (loại tích lũy lượt chơi)
            game_reward_histories = self.env['game.reward.history'].search([('phone', '=', zalo_id.phone), ('pos_promotion_id', 'in', pos_promotions.ids)])
            if game_reward_histories:
                for promotion in pos_promotions:
                    """
                    Case1: User có tổng ls lượt chơi game active > 0
                    Case2: User có tổng ls lượt chơi game active = 0 (mua hàng xong trả lại)
                    """
                    game_reward_history = self.env['game.reward.history'].search([('phone', '=', zalo_id.phone), ('pos_promotion_id', '=', promotion.id)])
                    game_reward_total = sum(game_reward_history.mapped('game_turn_reward'))
                    if game_reward_history and game_reward_total > 0:
                        link = self.get_url_minigame(zalo_id.phone, promotion.game_code)

                        msg = 'Bạn đang tham gia %s' % promotion.name + '. Bấm vào link bên dưới để bắt đầu.' + link
                        # title = "Tham gia ngay"
                        # self.send_message_attachment(sender, msg_id, msg, title, link)
                        self.send_feedback_message(sender, msg_id, msg)
                    if game_reward_history and game_reward_total <= 0:
                        msg = 'Bạn chưa có lượt chơi nào được tích lũy từ Homefarm'
                        self.send_feedback_message(sender, msg_id, msg)
            else:
                msg = 'Bạn chưa có lượt chơi nào được tích lũy từ Homefarm'
                self.send_feedback_message(sender, msg_id, msg)
        except Exception as e:
            raise ValidationError(e)

    def get_url_minigame(self, customer_phone, game_code):
        try:
            # tạm thời fix cứng url
            url_mini_game = self.env['ir.config_parameter'].sudo().get_param('url_mini_game')
            url = url_mini_game + '?campaignCode=' + str(game_code) + '&phone=' + str(customer_phone)
            return url
        except Exception as e:
            raise ValidationError(e)
