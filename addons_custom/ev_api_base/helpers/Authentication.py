# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/14/2019

from odoo import _, registry, tools

from .ApiException import ApiException

from hashlib import sha3_256
import jwt
from datetime import datetime


ROLE_MANAGER = 'sale_manager'
ROLE_LEADER = 'sale_leader'
ROLE_USER = 'sale_man'


class Authentication(object):

    __KEY = 'd2rpreuTowU061pc'

    MANAGER = 'sale_manager'
    LEADER = 'sale_leader'
    USER = 'sale_man'

    POS_MANAGER = 'pos_manager'
    POS_USER = 'pos_user'

    __ROLE_GROUP = {
        'sales_team': {
            'sales_team.group_sale_manager': MANAGER,
            'sales_team.group_sale_salesman_all_leads': LEADER,
            'sales_team.group_sale_salesman': USER
        },
        'point_of_sale': {
            'point_of_sale.group_pos_manager': POS_MANAGER,
            'point_of_sale.group_pos_user': POS_USER,
        },
    }

    @staticmethod
    def hook(user, params):
        """

        @param user:
        @param params:
        @return:
        """
        # Authentication.user_can_login_multi_device(user, params.get('device_id'))

    @staticmethod
    def generate_access_token(login, device_id):
        payload = {'login': sha3_256(login.encode('utf-8')).hexdigest(),
                   'device_id': device_id,
                   'ts': datetime.now().timestamp()}
        return jwt.encode(payload, Authentication.__KEY, algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_access_token(env, access_token):
        try:
            jwt.decode(access_token, Authentication.__KEY, algorithms=['HS256'])

            header, payload, sign = access_token.split('.')
            is_sign_in = env['res.users.device'].search([('access_token', '=', sign)])
            if not is_sign_in:
                raise Exception()

            return {'login': is_sign_in.user_id.login}
        except Exception as e:
            raise ApiException(_('Access token is not valid.'), ApiException.INVALID_ACCESS_TOKEN)

    @staticmethod
    def get_user_roles(user):
        result = {}
        if not user:
            return result

        for group, roles in Authentication.__ROLE_GROUP.items():
            for role, key in roles.items():
                if user.has_group(role):
                    result.update({group: key})
                    break
        return result

    @staticmethod
    def get_user_config(user, env):
        configs = []
        config_id = {'id': None, 'name': ''}
        if user.company_id and user.company_id.warehouse_id:
            stock_warehouse = env['stock.warehouse'].sudo().search([('id', '=', user.company_id.warehouse_id.id)])
            if not stock_warehouse:
                return config_id
            pos_configs = env['pos.config'].sudo().search([('stock_location_id', '=', stock_warehouse.lot_stock_id.id)])
            for cfg in pos_configs:
                configs.append({
                    'id': cfg.id,
                    'name': cfg.name or ''
                })
        return configs

    @staticmethod
    def get_user_companies(user):
        companies = []
        if user.company_ids:
            for company in user.company_ids:
                companies.append({
                    'id': company.id,
                    'name': company.name or '',
                })
        return companies

    @staticmethod
    def user_can_login_multi_device(user, device_id):
        pass
        if user.access_device_number == -1:
            return

        if user.access_device_number == 0:
            raise ApiException(_('Existing accounts are not allowed to log in on mobile devices.',
                               ApiException.NOT_ALLOWED_DEVICE))

        current_device_number = user.device_ids.search_count([('device_id', '!=', device_id), ('user_id', '=', user.id)])
        if current_device_number >= user.access_device_number:
            raise ApiException(_('The current login account exceeds the number of mobile devices allowed.',
                               ApiException.OVER_ALLOWED_DEVICE))

    @staticmethod
    def is_portal(user):
        if user.has_group('base.group_portal'):
            return True
        return False

    @staticmethod
    def is_user(user):
        if user.has_group('sales_team.group_sale_salesman'):
            return True
        return False

    @staticmethod
    def is_leader(user):
        if user.has_group('sales_team.group_sale_salesman_all_leads'):
            return True
        return False

    @staticmethod
    def is_manager(user):
        if user.has_group('sales_team.group_sale_manager'):
            return True
        return False

    @staticmethod
    def is_multi_company(user):
        if len(user.company_ids) > 1:
            return True
        return False

    @staticmethod
    def get_company_ids(env, company_id: int = None):
        if Authentication.is_branch_manager(env.user):
            company_ids = [env.user.company_id.id]
            if Authentication.is_multi_company(env.user):
                company_ids = env.user.company_ids.ids
            return company_ids

        if Authentication.is_multi_company(env.user):
            if company_id not in env.user.company_ids.ids:
                company_id = env.user.company_id.id
            return [company_id]
        else:
            return [env.user.company_id.id]
