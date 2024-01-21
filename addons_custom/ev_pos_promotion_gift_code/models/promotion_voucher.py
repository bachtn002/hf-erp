# -*- coding: utf-8 -*-
import random

from odoo import models, api, fields, _
from datetime import datetime
import base64
from odoo.modules.module import get_module_resource

today = datetime.today().strftime('%Y-%m-%d')


class PromotionVoucher(models.Model):
    _inherit = 'promotion.voucher'

    @api.model
    def get_promotion_voucher_line(self, rules, phone):
        is_display_code = self.env['ir.config_parameter'].sudo().get_param('ev_pos_promotion_gift_code.is_display_code')
        dict_promotion_code = []
        for rule in rules:
            sql = """                
            select pvl.name code, pv.id promotion_voucher_id, pv.x_condition_apply condition_apply, 
            pv.expired_date expired_date, pvl.promotion_use_code, coalesce(ppl.count,0), pvl.promotion_id promotion_id
                  from promotion_voucher_line pvl
                      left join (select count (*) as count, promotion_code
                      from phone_promotion_list
                      group by promotion_code) ppl
                  on pvl.name = ppl.promotion_code
                      left join promotion_voucher pv on pv.id = pvl.promotion_voucher_id
                  where pvl.promotion_id = %s
                    and pvl.state_promotion_code = 'available'
                    and pv.expired_date >= '%s'
                    and pv.state = 'active'
                    and pv.x_release_phone_types = 'phone'
                    and not exists (select 1 from phone_promotion_list 
                     where phone = '%s' and pvl.name = promotion_code)
                     and pvl.promotion_use_code >  coalesce(ppl.count,0)
                  order by random()
                  limit %s;
            """
            self._cr.execute(sql % (rule['pos_promotion_id'], today, phone, rule['number_code_give']))
            res = self._cr.dictfetchall()
            if len(res) < rule['number_code_give']:
                return {
                    'promotion_no_code': self.env['pos.promotion'].browse(rule['promotion_id']).name
                }
            if res:
                for line in res:
                    dict_promotion_code.append({
                        'code': line['code'] if is_display_code else '',
                        'promotion_id': rule['promotion_id'],
                        'pos_promotion_id': rule['pos_promotion_id'],
                        'promotion_voucher_id': line['promotion_voucher_id'],
                        'condition': line['condition_apply'],
                        'expired_date': line['expired_date'],
                        'code_for_save': line['code'],
                        'image': self.get_image_base64(),
                    })
        return dict_promotion_code

    def get_image_base64(self):
        image_path = get_module_resource('ev_pos_promotion_gift_code', 'static/src/img', 'qr.png')
        return base64.b64encode(open(image_path, 'rb').read())
