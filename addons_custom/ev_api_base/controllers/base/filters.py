# -*- coding: utf-8 -*-
# Created by Hoanglv on 1/6/2020

from odoo.http import Controller, route
from odoo import _

from ..helpers import Route, Dispatch, ApiException, Response, Filter, middleware


class Filters(Controller):

    _verify = ['key|str|nullable',
               'reverse|bool']

    @route(route=Route('filters'), methods=['GET'], auth='none', type='http', cors='*')
    @middleware(auth='none')
    def filters(self):
        """
        Lấy danh sách bộ lọc

        @param params: Danh sách tham số gửi lên từ client
            @requires:
            @options:   key         | str       |   key filter
                        reverse     | boolean   |   Đảo ngược thứ tự bộ lọc nếu True
        @return: Nếu không gửi lên tham số 'key' sẽ trả về danh sách key
                 Nếu gửi thêm 'key' sẽ trả về thông tin filter ứng với key
        """
        if 'key' in self.params:
            data = Filter().get(self.params.get('key'), reverse=self.params.get('reverse', False))
        else:
            data = Filter().get_key()
        return Response.success(_('Retrieve data successfully!'), data=data).to_json()
