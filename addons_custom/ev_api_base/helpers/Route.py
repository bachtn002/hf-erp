# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/14/2019

from odoo import tools

APP = tools.config.options.get('api_base_app') or 'odoo'


class Route(object):

    __ROOT_ENTRY_POINT = '/api/v{0}/{1}/{2}'

    def __new__(cls, route, version='1', app=APP):
        return cls.__route(route, app, version)

    @staticmethod
    def __route(route, app, version):
        return Route.__ROOT_ENTRY_POINT.format(version, app, route)
