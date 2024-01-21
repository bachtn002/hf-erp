# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/14/2019

from odoo import _, SUPERUSER_ID, api, tools, registry
from odoo.http import request, HttpRequest
from odoo.exceptions import except_orm, AccessError, ValidationError, MissingError, UserError, AccessDenied
from psycopg2 import IntegrityError

from .ApiException import ApiException
from .Authentication import Authentication
from .Params import Params

import traceback
import json
import requests
import jwt


class Dispatch(object):

    @staticmethod
    def dispatch(ins, action: str, verify: list = [], auth: str = 'user', additional_params: dict = {}):
        """
        Hàm làm nhiệm vụ, kiểm tra thông tin dữ liệu, điều hướng thực thi tác vụ

        @param ins:                 Đối tượng chứa acction
        @param action:              Hạm được điều hướng
        @param verify:              Quy tắc kiểm tra dữ liệu
        @param auth:                Xác thực người dùng thông qua access_token
        @param additional_params:   Tham số bổ sung sau khi sử lý dữ liệu trên router và muốn call đế 1 controller khác
        @return:                    Trả về dữ liệu dược trả về từ action
        """

        def save_log(user, params, exception, exception_message, exception_data):
            db_name = Dispatch._get_db_name()
            _regis = registry(db_name)
            with _regis.cursor() as _cr:
                _env = api.Environment(_cr, SUPERUSER_ID, context)
                _uid = user.id if user else user
                _env['api.logger'].create({'name': '%s|%s' % (str(ins), action),
                                           'user_id': _uid,
                                           'params': params,
                                           'exception': exception,
                                           'exception_message': exception_message,
                                           'exception_data': exception_data})

        dispatch = getattr(ins, action)
        if not dispatch:
            raise ApiException(_('Action has not been defined.'), ApiException.METHOD_NOT_FOUND)

        context = request.context
        params = Dispatch.get_params()
        params.update(additional_params)

        env, user = Dispatch.authenticate(auth, params, context)
        params['user_type'] = Dispatch._get_user_type(user)

        Params.verify(verify, params)
        setattr(ins, '_cr', request.cr)
        setattr(ins, 'env', env)
        setattr(ins, 'params', params)
        setattr(ins, 'context', env.context)

        if params.get('debug', False):
            return dispatch()

        try:
            return dispatch()
        except ApiException as e:
            if env:
                env.cr.rollback()
            save_log(user, params, 'ApiException', str(e), traceback.format_exc())
            raise e
        except AccessError as e:
            save_log(user, params, 'AccessError', str(e), traceback.format_exc())
            raise ApiException(e.name, ApiException.UNKNOWN_ERROR)
        except MissingError as e:
            save_log(user, params, 'MissingError', str(e), traceback.format_exc())
            raise ApiException(e.name, ApiException.UNKNOWN_ERROR)
        except UserError as e:
            save_log(user, params, 'UserError', str(e), traceback.format_exc())
            raise ApiException(e.name, ApiException.UNKNOWN_ERROR)
        except ValidationError as e:
            save_log(user, params, 'ValidationError', str(e), traceback.format_exc())
            raise ApiException(e.name, ApiException.UNKNOWN_ERROR)
        except except_orm as e:
            save_log(user, params, 'except_orm', str(e), traceback.format_exc())
            raise ApiException(e.value, ApiException.UNKNOWN_ERROR)
        except IntegrityError as e:
            if e.pgcode == '23505':
                save_log(user, params, 'IntegrityError', str(e), traceback.format_exc())
                raise ApiException(_('A record already exists, please check it again.'), ApiException.UNKNOWN_ERROR)
            save_log(user, params, 'IntegrityError', str(e), traceback.format_exc())
            raise ApiException(_('The system is experiencing problems, please try again later.'),
                               ApiException.UNKNOWN_ERROR)
        except AccessDenied as e:
            save_log(user, params, 'AccessDenied', str(e), traceback.format_exc())
            raise ApiException(_('You do not have access to current data.'), ApiException.ACCESS_DENIED)
        except Exception as e:
            save_log(user, params, 'Exception', str(e), traceback.format_exc())
            raise ApiException(_('The system is experiencing problems, please try again later.'),
                               ApiException.UNKNOWN_ERROR)

    @staticmethod
    def get_params():
        params = request.jsonrequest if request._request_type == 'json' else request.params
        if params.get('jsonrpc', False):
            params = params.get('params', {})
        access_token = request.httprequest.headers.get('Access-Token', '')
        # Use this before the older version pass access_token in request params
        if access_token:
            params.update({'access_token': access_token})
        if 'Access-Token' in params:
            params.update({'access_token': params['Access-Token']})
            del params['Access-Token']
        return params

    @staticmethod
    def authenticate(auth, params, context):
        env = request.env(user=SUPERUSER_ID, context={'lang': 'vi_VN'})
        if auth == 'user':
            return Dispatch._authenticate(env, params, context)
        elif auth == 'both':
            try:
                return Dispatch._authenticate(env, params, context)
            except ApiException as e:
                if e.code == ApiException.INVALID_ACCESS_TOKEN:
                    raise ApiException(e.message, e.code)
                return env, False
        return env, False

    @staticmethod
    def _authenticate(env, params, context):
        if params.get('access_token', False):
            env, user = Dispatch.access_token_authenticate(env, params, context)
        elif request.session.uid:
            env = request.env(user=request.session.uid)
            user = env['res.users'].browse(request.session.uid)
        elif 'type' in params and params['type'] != 'odoo':
            env, user = Dispatch.social_network_authenticate(params)
        else:
            db_name = Dispatch._get_db_name()
            env, user = Dispatch.login_password_authenticate(db_name, params, context)
        return env, user

    @staticmethod
    def access_token_authenticate(env, params, context):
        Params.verify(['access_token|require|str'], params)

        data = Authentication.verify_access_token(env, params['access_token'])
        login = data.get('login')
        user = env['res.users'].search([('login', '=', login)])
        if Authentication.is_portal(user):
            params['user_type'] = 'portal'
        elif Authentication.is_user(user):
            params['user_type'] = 'internal'
        _ctx = context.copy()
        _ctx.update({'lang': Dispatch._get_request_lang(user)})
        env = request.env(user=user.id, context=_ctx)
        Dispatch.validate_access_token_expired(user, params['access_token'])
        return env, user

    @staticmethod
    def login_password_authenticate(db_name, params, context):
        try:
            Params.verify(['login|str|require', 'password|str|require:type{"odoo"}'], params)
            uid = registry(db_name)('res.users').authenticate(db_name, params['login'], params['password'], {})
            user = request.env(user=uid)['res.users'].browse(uid)
            _ctx = context.copy()
            _ctx.update({'lang': Dispatch._get_request_lang(user)})
            env = request.env(user=uid, context=_ctx)
            if Authentication.is_portal(user):
                params['user_type'] = 'portal'
            elif Authentication.is_user(user):
                params['user_type'] = 'internal'
            Authentication.hook(user, params)
            return env, user
        except ApiException as e:
            raise e
        except Exception as e:
            raise ApiException(_('The account or password is incorrect, please try again.'), ApiException.AUTHORIZED)

    @staticmethod
    def social_network_authenticate(params):
        try:
            if params.get('type') not in ['facebook', 'google', 'apple']:
                raise ApiException(_("The system does not support logging in with this app yet!"), ApiException.AUTHORIZED)
            Params.verify([
                'login|str|require',
                'idToken|str|require:type{"facebook","google", "apple"}',
                'image|str|require:type{"facebook","google"}',
            ], params)
            oauth_provider = request.env(user=SUPERUSER_ID)['auth.oauth.provider'].search(
                [('code', '=', params.get('type'))], limit=1)

            if not oauth_provider:
                raise ApiException(
                    _("The system does not identify this login application. Please check the configuration section"), ApiException.AUTHORIZED)
            access_token = params.pop('idToken')
            params.update({
                'access_token': access_token,
                'state': json.dumps({'t': None})
            })
            user = request.env(user=SUPERUSER_ID)['res.users'].search([('login', '=', params.get('login')),
                                                                       ('oauth_provider_id', '!=', oauth_provider.id)])
            if user:
                raise ApiException(_("Your account is already connected to another social network, please check again."), ApiException.AUTHORIZED)

            db_name, login, access_token = request.env(user=SUPERUSER_ID)['res.users'].auth_oauth(oauth_provider.id, params)

            user = request.env(user=SUPERUSER_ID)['res.users'].search([('login', '=', login)])
            env = request.env(user=user.id, context={'lang': Dispatch._get_request_lang(user)})
            user = env['res.users'].browse(user.id)
            if Authentication.is_portal(user):
                params['user_type'] = 'portal'
            elif Authentication.is_user(user):
                params['user_type'] = 'internal'
            access_token = params.pop('access_token')
            params.update({
                'idToken': access_token,
                'login': login
            })
            Authentication.hook(user, params)
            return env, user
        except ApiException as e:
            raise e
        except Exception as e:
            raise ApiException(_('Unable to log in with this account, please try again.'), ApiException.AUTHORIZED)

    @staticmethod
    def validate_access_token_expired(user, access_token):
        if user.is_access_token_expired(access_token):
            raise ApiException('Warning', _('Access token has expired, please log in again.'))
        user.reset_access_token_expire(access_token)

    @staticmethod
    def _get_user_type(user):
        if not user:
            return ''
        if Authentication.is_portal(user):
            return 'portal'
        elif Authentication.is_user(user):
            return 'internal'
        return ''

    @staticmethod
    def _get_db_name():
        if tools.config.options.get('db_name'):
            return tools.config.options.get('db_name')
        return tools.config.options.get('dbfilter')

    @staticmethod
    def _get_request_lang(user):
        return request.httprequest.headers.get('Lang', user.lang)
