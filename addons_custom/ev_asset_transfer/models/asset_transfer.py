# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class AssetTransfer(models.Model):
    _name = 'asset.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Asset Transfer', default=lambda self: _('New'),track_visibility='onchange')
    date = fields.Datetime('Date',track_visibility='onchange',default=fields.Datetime.now)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    account_analytic_dest_id = fields.Many2one('account.analytic.account', 'Analytic Account Dest')
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancel')], 'State',track_visibility='onchange', default='draft')
    lines = fields.One2many('asset.transfer.line','asset_transfer_id', 'Lines', track_visibility='onchange')

    def _validate_data(self):
        for line in self.lines:
            if line.qty_done > line.qty:
                raise ValidationError(_('Số lượng điều chuyển không được lớn hơn số lượng tài sản'))
            if line.qty_done < 0:
                raise ValidationError(_('Số lượng điều chuyển không được nhỏ hơn 0'))
            if line.qty > 0 and line.qty_done == 0:
                raise ValidationError(_('Số lượng điều chuyển phải lớn hơn 0'))

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        for line in self.lines:
            line.unlink()

    @api.onchange('account_analytic_dest_id')
    def _onchange_account_analytic_dest_id(self):
        for line in self.lines:
            line.account_analytic_dest_id = self.account_analytic_dest_id.id

    @api.onchange('date')
    def _onchange_date(self):
        for line in self.lines:
            line.date = self.date

    @api.onchange('name')
    def _onchange_name(self):
        for line in self.lines:
            line.name = self.name


    def action_set_to_draft(self):
        self.state = 'draft'
        for line in self.lines:
            line.state = 'draft'

    def unlink(self):
        for rc in self:
            if rc.state == 'draft':
                return super(AssetTransfer, rc).unlink()
            raise ValidationError(_('You can only delete when state is draft'))

    def action_cancel(self):
        self.state = 'cancel'
        for line in self.lines:
            line.state = 'cancel'

    def action_confirm(self):
        self._validate_data()
        self.state = 'confirmed'
        for line in self.lines:
            line.state = 'confirmed'

    def action_transfer(self):
        self._action_transfer()
        self.state = 'done'
        for line in self.lines:
            line.state = 'done'


    def _action_transfer(self):
        for line in self.lines:
            if line.asset_id.id == False:
                continue
            line._action_asset_transfer()


    def action_back(self):
        self.state = 'draft'
        for line in self.lines:
            line.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.transfer') or _('New')
        return super(AssetTransfer, self).create(vals)



class AssetTransferLine(models.Model):
    _name = 'asset.transfer.line'


    asset_transfer_id = fields.Many2one('asset.transfer','Transfer')
    date = fields.Datetime('Date')
    name = fields.Char('Name')
    asset_id = fields.Many2one('account.asset','Asset')
    qty = fields.Float('Qty')
    qty_done = fields.Float('Qty Transfer')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    account_analytic_dest_id = fields.Many2one('account.analytic.account', 'Analytic Account Dest')
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancel')], 'State',track_visibility='onchange', default='draft')


    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        for record in self:
            if record.asset_id.id != False:
                record.qty = record.asset_id.x_remaining_quantity
                record.qty_done = record.asset_id.x_remaining_quantity
                record.account_analytic_id = record.asset_transfer_id.account_analytic_id.id
                record.account_analytic_dest_id = record.asset_transfer_id.account_analytic_dest_id.id
                record.name = record.asset_transfer_id.name
                record.date = record.asset_transfer_id.date
            else:
                record.qty = 0
                record.qty_done = 0
                record.account_analytic_id = False
                record.account_analytic_dest_id = False

    def _action_asset_transfer(self):
        self.asset_id.account_analytic_id = self.asset_transfer_id.account_analytic_dest_id.id
        for line in self.asset_id.depreciation_move_ids:
            if line.state == 'posted' or line.state == 'cancel':
                continue
            for l in line.line_ids:
                l.analytic_account_id = self.asset_transfer_id.account_analytic_dest_id.id




class AccountAsset(models.Model):
    _inherit = 'account.asset'

    x_transfer_ids = fields.One2many('asset.transfer.line','asset_id', 'Asset Transfer', domain=[('state','=','done')])