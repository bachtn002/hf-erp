# -*- coding: utf-8 -*-
# from odoo import http


# class EvElearningCustomV1(http.Controller):
#     @http.route('/ev_elearning_custom_v1/ev_elearning_custom_v1/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ev_elearning_custom_v1/ev_elearning_custom_v1/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ev_elearning_custom_v1.listing', {
#             'root': '/ev_elearning_custom_v1/ev_elearning_custom_v1',
#             'objects': http.request.env['ev_elearning_custom_v1.ev_elearning_custom_v1'].search([]),
#         })

#     @http.route('/ev_elearning_custom_v1/ev_elearning_custom_v1/objects/<model("ev_elearning_custom_v1.ev_elearning_custom_v1"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ev_elearning_custom_v1.object', {
#             'object': obj
#         })
