# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero, float_round


class AccountAssetReport(models.TransientModel):
    _name = 'account.asset.report'

    def _domain_account_analytic(self):
        try:
            if self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
                domain = [(1, '=', 1)]
                return domain
            else:
                account_analytic_ids = []
                for record in self.env.user.warehouse_ids:
                    account_analytic_ids.append(record.x_analytic_account_id.id)
                domain = [('id', 'in', account_analytic_ids)]
                return domain
        except Exception as e:
            raise ValidationError(e)

    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          domain=_domain_account_analytic)
    lines = fields.One2many('account.asset.report.line', 'report_id', 'Lines')
    check_data = fields.Boolean('Check Data', default=False)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    def action_confirm(self):
        if len(self.lines) > 0:
            self.lines.unlink()
        asset_ids = self.env['account.asset'].search(
            [('state', 'in', ['open', 'paused']), ('x_quantity', '>', 0), ('x_remaining_quantity', '>', 0),
             ('account_analytic_id', '=', self.account_analytic_id.id)])
        line_datas = []
        if len(asset_ids) > 0:
            self.check_data = True
        for asset in asset_ids:
            data = {
                'account_analytic_id': self.account_analytic_id.id,
                'x_code': asset.x_code,
                'asset_id': asset.id,
                'report_id': self.id,
                'quantity': asset.x_remaining_quantity,
                'uom_id': asset.x_product_asset_id.uom_id.id,
            }
            line_datas.append((0, 0, data))
        self.lines = line_datas


class AccountAssetReportLine(models.TransientModel):
    _name = 'account.asset.report.line'

    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    asset_id = fields.Many2one('account.asset', 'Asset')
    x_code = fields.Char('Code')
    quantity = fields.Integer('Quantity')
    report_id = fields.Many2one('account.asset.report', 'Report')

    uom_id = fields.Many2one('uom.uom', 'Uom')
