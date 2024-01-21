# -*- coding: utf-8 -*-
# Created by Hoanglv on 06/11/2020

from odoo import _
from odoo.http import request
from odoo.exceptions import except_orm, AccessError, ValidationError, MissingError, UserError, AccessDenied
from psycopg2 import IntegrityError

from .ApiException import ApiException
from .Authentication import Authentication
from .Params import Params
from .Dispatch import Dispatch
from .Response import Response

import traceback
import requests
import functools


def middleware(auth='both'):
    def decorator(func):

        @functools.wraps(func)
        def response_wrap(self, **kw):

            def __dispatch_authen():
                env, user = Dispatch.authenticate(auth, params, context)
                params['user_type'] = Dispatch._get_user_type(user)

                return env, user

            def __dispatch_combiner():
                setattr(self, '_cr', request.cr)
                setattr(self, 'env', env)
                setattr(self, 'params', params)
                setattr(self, 'context', env.context)

            def _verify_params():
                _verify_rules= '_verify_'+func.__name__
                if hasattr(self, _verify_rules):
                    Params.verify(getattr(self, _verify_rules), params)
            
            context = request.context
            env = None
            user = None

            params = Dispatch.get_params()

            if params.get('debug', False):
                env, user = __dispatch_authen()
                __dispatch_combiner()
                _verify_params()
                return func(self)

            try:
                env, user = __dispatch_authen()
                __dispatch_combiner()
                _verify_params()
                return func(self)
            except ApiException as e:
                if env:
                    env.cr.rollback()
                return e.to_json()
            except AccessError as e:
                return ApiException(e.name, ApiException.UNKNOWN_ERROR).to_json()
            except MissingError as e:
                return ApiException(e.name, ApiException.UNKNOWN_ERROR).to_json()
            except UserError as e:
                return ApiException(e.name, ApiException.UNKNOWN_ERROR).to_json()
            except ValidationError as e:
                return ApiException(e.name, ApiException.UNKNOWN_ERROR).to_json()
            except except_orm as e:
                return ApiException(e.value, ApiException.UNKNOWN_ERROR).to_json()
            except IntegrityError as e:
                if e.pgcode == '23505':
                    return ApiException(_('A record already exists, please check it again.'), ApiException.UNKNOWN_ERROR).to_json()
                return ApiException(_('The system is experiencing problems, please try again later.'),
                                  ApiException.UNKNOWN_ERROR).to_json()
            except AccessDenied as e:
                return ApiException(_('You do not have access to current data.'), ApiException.ACCESS_DENIED).to_json()
            except Exception as e:
                return ApiException(_('The system is experiencing problems, please try again later.'),
                                  ApiException.UNKNOWN_ERROR).to_json()

        response_wrap.original_func = func
        return response_wrap
    return decorator
