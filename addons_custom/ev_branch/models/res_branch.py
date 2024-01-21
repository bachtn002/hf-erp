# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression


class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    code = fields.Char("Code", required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')
    partner_id = fields.Many2one('res.partner', string='Partner')

    def name_get(self):
        branch_list = []
        for branch in self:
            name = '[' + branch.code + "]" + branch.name
            branch_list.append((branch.id, name))
        return branch_list

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        branch_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return branch_ids

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Private implementation of search() method, allowing specifying the uid to use for the access right check.
        This is useful for example when filling in the selection list for a drop-down and avoiding access rights errors,
        by specifying ``access_rights_uid=1`` to bypass access rights check, but not ir.rules!
        This is ok at the security level because this method is private and not callable through XML-RPC.

        :param access_rights_uid: optional user ID to use when checking access rights
                                  (not for ir.rules, this is only for ir.model.access)
        :return: a list of record ids or an integer (if count is True)
        """
        model = self.with_user(access_rights_uid) if access_rights_uid else self
        model.check_access_rights('read')

        if expression.is_false(self, args):
            # optimization: no need to query, as no record satisfies the domain
            return 0 if count else []

        # the flush must be done before the _where_calc(), as the latter can do some selects
        self._flush_search(args, order=order)

        query = self._where_calc(args)
        if not ('force_record_rule' in self._context and self._context['force_record_rule'] == 1):
            self._apply_ir_rules(query, 'read')

        if count:
            # Ignore order, limit and offset when just counting, they don't make sense and could
            # hurt performance
            query_str, params = query.select("count(1)")
            self._cr.execute(query_str, params)
            res = self._cr.fetchone()
            return res[0]

        query.order = self._generate_order_by(order, query).replace('ORDER BY ', '')
        query.limit = limit
        query.offset = offset

        return query