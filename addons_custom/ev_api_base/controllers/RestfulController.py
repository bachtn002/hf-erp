# # -*- coding: utf-8 -*-
# # Created by Hoanglv on 06/11/2020

# from odoo.http import Controller, route
# from helpers import Response, 


# class RestfulController(Controller):
#     model = ''
#     __model__ = None

#     def __init__(cls):
#         if not self._model:
#             raise Exception('Model name for provided, please config model attribute for RestfulController instance')
#         cls.__model__ = request.env[self._model]

#     def create(self, vals):
#         res = False
#         if isinstance(vals, object):
#             return self.__model__.create(vals)
#         if isinstance(vals, list):
#             res = []
#             for val in vals:
#                 res.append(self.create(val))
#         return res

#     def write(self, vals):
#         model = self.__model__.browse(vals['id'])
#         del vals['id']
#         return model.write(vals)

#     def unlink(self, vals)

  
