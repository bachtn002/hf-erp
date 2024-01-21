# -*- coding: utf-8 -*-
import requests
import json
import pytz

from odoo import models, fields, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


class LogUserApi(models.Model):
    _name = 'log.user.api'
    _description = 'Log User Api'

    params = fields.Char(string='Params')
    call_date = fields.Datetime(string='Call Api Date')
    status = fields.Char(string='Status')
    message = fields.Text(string='Message')
    user_not_create = fields.Text(string='User data is not newly created')

    def _call_api_user(self):
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('URL_GET_API_USERS')
            token = self.env['ir.config_parameter'].sudo().get_param('TOKEN_GET_API_USERS')
            obj_log_status = self.env['log.user.api'].search([('status', '=', '1')], limit=1,
                                                             order='create_date desc')
            header = {
                'Content-Disposition': 'form-data',
                'Token': token,
            }
            data = {}
            user_not_create = []
            if not obj_log_status:
                data = {
                    'APICode': 'SYNEMPLOYEE',
                    'fromtime': '',
                    'totime': '',
                }
            else:
                date_start = obj_log_status.call_date.strftime('%Y-%m-%d 00:00:00')
                date_end = datetime.now(pytz.timezone('Asia/Bangkok')).date()
                data = {
                    'APICode': 'SYNEMPLOYEE',
                    'fromtime': date_start,
                    'totime': date_end.strftime('%Y-%m-%d 23:59:59'),
                }
            response = requests.post(url, headers=header, data=data)
            res = response.json()
            if res['Status'] == 1:
                data_user = json.loads(res['Data'])
                today = datetime.now(pytz.timezone('Asia/Bangkok')).date()
                for item in data_user:
                    try:
                        date_start = datetime.strptime(item['NgayBatDauLam'],
                                                       '%Y-%m-%d %H:%M:%S').date() if item['NgayBatDauLam'] != None else False
                        date_off = datetime.strptime(item['NgayNghiViec'],
                                                     '%Y-%m-%d %H:%M:%S').date() if item['NgayNghiViec'] != None else False
                        if item['EmailCaNhan'] == '' or not bool(item['EmailCaNhan']) or item['EmailCaNhan'] == '0':
                            user_not_create.append(item)
                        else:
                            employee = self._check_employee_code(item)
                            if not employee:
                                if not date_off or date_start <= today <= date_off:
                                    user = self._check_user(item)
                                    if not user:
                                        self._create_partner(item)
                                        self._create_user(item)
                            else:
                                # user_not_create.append(item)
                                user = self.env['res.users'].search([('id', '=', employee[0]['id']),
                                                                     ('active', 'in', [True, False])])
                                partner = self.env['res.partner'].search([('id', '=', employee[0]['partner_id']),
                                                                          ('active', 'in', [True, False])])

                                if user:
                                    if user.login != item['EmailCaNhan'].strip():
                                        user.write({'login': item['EmailCaNhan'].strip()})

                                if partner:
                                    field_compare = [('name', item['Ho'] + ' ' + item['HoTen']),
                                                     ('email', item['EmailCaNhan'].strip()),
                                                     ('x_start_working_date_sync',
                                                      datetime.strptime(item['NgayBatDauLam'], '%Y-%m-%d %H:%M:%S').date() if
                                                      item['NgayBatDauLam'] != None else False),
                                                     ('x_end_working_date_sync',
                                                      datetime.strptime(item['NgayNghiViec'], '%Y-%m-%d %H:%M:%S').date() if
                                                      item['NgayNghiViec'] != None else False),
                                                     ('x_position_sync', item['TenChucVu']),
                                                     ('x_department_sync', item['TenPhongBan']),
                                                     ('phone', item['DienThoai'])]

                                    for field in field_compare:
                                        if partner[field[0]] != field[1]:
                                            partner.write({field[0]: field[1]})

                                if date_off and date_off <= today:
                                    user.write({'active': False})
                                    partner.write({'active': False})
                    except Exception as e:
                        user_not_create.append(item)

                self.create({
                    'params': data,
                    'call_date': datetime.fromtimestamp(datetime.now(pytz.timezone('Asia/Bangkok')).timestamp()),
                    'status': '1',
                    'message': '',
                    'user_not_create': str(user_not_create)
                })
            else:
                self.create({
                    'params': data,
                    'call_date': datetime.fromtimestamp(datetime.now(pytz.timezone('Asia/Bangkok')).timestamp()),
                    'status': '0',
                    'message': res['Message'] if 'Message' in res else ''
                })
        except Exception as e:
            raise ValidationError(e)

    def _create_user(self, item):
        grp_portal = self.env.ref('base.group_portal')
        pass_default = self.env['ir.config_parameter'].sudo().get_param('PASSWORD_DEFAULT')
        user_email = item['EmailCaNhan'].strip()
        partner_id = self.env['res.partner'].search([('email', '=', user_email)], limit=1).id
        time_now = datetime.now()
        sql = """
            insert into res_users (login, password, company_id, partner_id, notification_type,
             create_date, write_date, create_uid, write_uid, x_employee_code_sync)
            values ('%s','%s','%s','%s','%s', '%s', '%s', '%s', '%s', '%s')
        """
        self._cr.execute(sql % (
            user_email, pass_default, self.env.company.id, partner_id, 'email', time_now,
            time_now,
            self.env.user.id, self.env.user.id, item['MaNhanVien']))
        new_user = self.env['res.users'].search([('login', '=', user_email)])
        self.env['res.groups'].search([('id', '=', grp_portal.id)]).write({'users': [(4, new_user.id)]})
        new_user.write({'company_ids': [(4, self.env.company.id, False)]})

    def _create_partner(self, data):
        self.env['res.partner'].create({
            'name': data['Ho'] + ' ' + data['HoTen'],
            'company_id': self.env.company.id,
            'email': data['EmailCaNhan'].strip(),
            'x_start_working_date_sync': data['NgayBatDauLam'],
            'x_end_working_date_sync': data['NgayNghiViec'],
            'x_position_sync': data['TenChucVu'],
            'x_department_sync': data['TenPhongBan'],
            'phone': data['DienThoai'],
            'x_employee_code': data['MaNhanVien']
        })

    def _check_employee_code(self, item):
        sql = """
            select * from res_users where x_employee_code_sync = '%s';
        """
        self._cr.execute(sql % item['MaNhanVien'])
        employee = self._cr.dictfetchall()
        return employee

    def _check_user(self, item):
        sql = """
            select * from res_users where login = '%s'
        """
        self._cr.execute(sql % item['EmailCaNhan'].strip())
        user = self._cr.dictfetchall()
        return user
