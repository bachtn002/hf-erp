# -*- coding: utf-8 -*-
# from odoo import http


# class EvCheckVoucherCode(http.Controller):
#     @http.route('/ev_check_voucher_code/ev_check_voucher_code/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_check_voucher_code/ev_check_voucher_code/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_check_voucher_code.listing', {
#             'root': '/ev_check_voucher_code/ev_check_voucher_code',
#             'objects': http.request.env['ev_check_voucher_code.ev_check_voucher_code'].search([]),
#         })

#     @http.route('/ev_check_voucher_code/ev_check_voucher_code/objects/<model("ev_check_voucher_code.ev_check_voucher_code"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_check_voucher_code.object', {
#             'object': obj
#         })
