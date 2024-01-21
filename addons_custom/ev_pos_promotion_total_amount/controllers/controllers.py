# -*- coding: utf-8 -*-
# from odoo import http


# class EvPosPromotionAmountTotal(http.Controller):
#     @http.route('/ev_pos_promotion_amount_total/ev_pos_promotion_amount_total/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_pos_promotion_amount_total/ev_pos_promotion_amount_total/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_pos_promotion_amount_total.listing', {
#             'root': '/ev_pos_promotion_amount_total/ev_pos_promotion_amount_total',
#             'objects': http.request.env['ev_pos_promotion_amount_total.ev_pos_promotion_amount_total'].search([]),
#         })

#     @http.route('/ev_pos_promotion_amount_total/ev_pos_promotion_amount_total/objects/<model("ev_pos_promotion_amount_total.ev_pos_promotion_amount_total"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_pos_promotion_amount_total.object', {
#             'object': obj
#         })
