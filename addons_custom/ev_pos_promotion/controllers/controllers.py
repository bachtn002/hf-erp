# -*- coding: utf-8 -*-
# from odoo import http


# class EvPosPromotion(http.Controller):
#     @http.route('/ev_pos_promotion/ev_pos_promotion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_pos_promotion/ev_pos_promotion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_pos_promotion.listing', {
#             'root': '/ev_pos_promotion/ev_pos_promotion',
#             'objects': http.request.env['ev_pos_promotion.ev_pos_promotion'].search([]),
#         })

#     @http.route('/ev_pos_promotion/ev_pos_promotion/objects/<model("ev_pos_promotion.ev_pos_promotion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_pos_promotion.object', {
#             'object': obj
#         })
