# -*- coding: utf-8 -*-
# from odoo import http


# class EvPosVoucher(http.Controller):
#     @http.route('/ev_pos_voucher/ev_pos_voucher/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_pos_voucher/ev_pos_voucher/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_pos_voucher.listing', {
#             'root': '/ev_pos_voucher/ev_pos_voucher',
#             'objects': http.request.env['ev_pos_voucher.ev_pos_voucher'].search([]),
#         })

#     @http.route('/ev_pos_voucher/ev_pos_voucher/objects/<model("ev_pos_voucher.ev_pos_voucher"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_pos_voucher.object', {
#             'object': obj
#         })
