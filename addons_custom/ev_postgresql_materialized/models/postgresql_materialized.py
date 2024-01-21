# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class PostgreSQLMaterialized(models.Model):
    _name = 'postgresql.materialized'
    _description = 'PostgreSQL Materialized'
    _order = 'from_date ASC, view_type ASC'
    _sql_constraints = [('unique_name', 'unique(name)', 'Name must be unique')]

    def _check_materialized_created(self):
        for row in self:
            row.is_created = row._is_materialized_exists()

    name = fields.Char('Name', readonly=True)
    from_date = fields.Date(
        string='From date',
        default=lambda x: fields.Datetime.now().replace(day=1))
    to_date = fields.Date(string='To date',
                          default=lambda x:
                          (fields.Datetime.now().replace(day=1) +
                           relativedelta(months=1)) - relativedelta(days=1))
    view_type = fields.Selection([], string='View Type', required=True)
    is_created = fields.Boolean(string='Is Created',
                                compute=_check_materialized_created)

    @api.model
    def create(self, vals):
        result = super(PostgreSQLMaterialized, self).create(vals)
        result.name = result._materialized_name()
        if result._is_materialized_exists():
            result._refesh_materialized()
        else:
            result._init_materialized()
        return result

    def _materialized_name(self):
        return self._name_build(self.view_type, self.from_date, self.to_date)

    def _name_build(self, view_type, from_date, to_date):
        from_date = from_date.strftime('%d_%m_%Y')
        to_date = to_date.strftime('%d_%m_%Y')
        return '%s_materialized_%s_%s' % (view_type, from_date, to_date)

    def action_refresh(self):
        self.ensure_one()
        self._refesh_materialized()

    def action_recreate(self):
        self.ensure_one()
        self._drop_materialized_if_exists()
        self._init_materialized()
        if not self._context.get('no_depend', False):
            depends = self.search([('view_type', '=', self.view_type),
                                   ('from_date', '>=', self.to_date)],
                                  order='from_date ASC')
            for depend in depends:
                depend.with_context(no_depend=True).action_recreate()

    @api.model
    def action_cron_previous_month_materialized(self):
        for view_type in dict(self._fields['view_type'].selection).keys():
            self._previos_month_materialized(view_type)

    def _previous_month_materialized(self, view_type):
        start_prev_month = (fields.Date.today() +
                            relativedelta(months=-1)).replace(day=1)
        end_pre_month = start_prev_month + relativedelta(
            months=1) - relativedelta(days=1)
        vals = {
            'view_type': view_type,
            'from_date': start_prev_month,
            'to_date': end_pre_month
        }
        name = self._name_build(view_type, start_prev_month, end_pre_month)
        materialized = self.search([('name', '=', name)])
        if materialized:
            return materialized
        return self.create(vals)

    def _init_materialized(self):
        sql, params = self._query_factory(view_type=self.view_type)
        if not sql:
            return
        materialized_sql = f"""
            CREATE MATERIALIZED VIEW public.{self.name} AS
                ({sql})
        """
        self._cr.execute(materialized_sql, params)

    def _drop_materialized_if_exists(self):
        self.ensure_one()
        if self._is_materialized_exists():
            sql = f"DROP MATERIALIZED VIEW {self.name} CASCADE"
            self._cr.execute(sql)

    def _refesh_materialized(self):
        for row in self:
            if row._is_materialized_exists():
                sql = f"REFRESH MATERIALIZED VIEW {row.name}"
                self._cr.execute(sql)

    def _is_materialized_exists(self):
        self.ensure_one()
        sql = f"""SELECT matviewname
                  FROM pg_matviews
                  WHERE matviewname = '{self.name}'"""
        self._cr.execute(sql)
        result = self._cr.dictfetchall()
        if result:
            return True
        return False

    def _last_materialized(self, view_type, to_date):
        domain = self._prepare_domain_get_last_materialized(view_type, to_date)
        last = self.search(domain, order='to_date desc', limit=1)
        if last:
            return last
        return False

    def _prepare_domain_get_last_materialized(self, view_type, to_date):
        domain = [('view_type', '=', view_type), ('to_date', '<', to_date)]
        if self:
            domain += [('id', '!=', self.id)]
        return domain

    def _query_factory(self,
                       view_type,
                       from_date=False,
                       to_date=False,
                       **kwargs):
        """Overwrite function
        Hàm này trả về câu query + params dùng để tạo materizialized

        Keyword Arguments:
            materialized_before {bool} -- Materizalied đã tồn tại trước đó (default: {False})
            from_date {bool} -- Từ ngày (default: {False})
            to_date {bool} -- Đến ngày (default: {False})

        Returns:
            str: Câu truy vấn lấy dữ liệu
            tuple: tham số cho câu truy vấn
        """
        sql = ''
        params = ()
        return sql, params
