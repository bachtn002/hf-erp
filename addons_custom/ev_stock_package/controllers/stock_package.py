# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.stock_barcode.controllers.main import StockBarcodeController

class StockPackage(StockBarcodeController):

    @http.route()
    def main_menu(self, barcode, **kw):
        stock_transfer = request.env['stock.transfer'].search([('name', '=', barcode)], limit=1)
        if stock_transfer:
            if request.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
                return self._get_action(stock_transfer)
            warehouse_source = stock_transfer.warehouse_id.id in request.env.user.warehouse_ids.ids
            warehouse_dest = stock_transfer.warehouse_dest_id.id in request.env.user.warehouse_ids.ids
            if not warehouse_source and not warehouse_dest:
                return {'warning': _('No transfer corresponding to barcode %(barcode)s') % {'barcode': barcode}}
            if stock_transfer.state in ('draft', 'confirmed', 'ready') and not warehouse_source:
                return {'warning': _('No transfer corresponding to barcode %(barcode)s') % {'barcode': barcode}}
            if stock_transfer.state in ('done', 'transfer') and not warehouse_dest:
                return {'warning': _('No transfer corresponding to barcode %(barcode)s') % {'barcode': barcode}}
            return self._get_action(stock_transfer)
        return super().main_menu(barcode)

    def _get_allowed_company_ids(self):
        """ Return the allowed_company_ids based on cookies.

        Currently, request.env.company returns the current user's company when called within a controller
        rather than the selected company in the company switcher and request.env.companies lists the
        current user's allowed companies rather than the selected companies.

        :returns: List of active companies. The first company id in the returned list is the selected company.
        """
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        return [int(cid) for cid in cids.split(',')]

    @http.route('/ev_stock_package/get_set_barcode_view_state', type='json', auth='user')
    def get_transfer_barcode_view_state(self, model_name, record_id, mode, write_field=None, write_vals=None):
        if mode != 'read':
            request.env[model_name].browse(record_id).write({write_field: write_vals})
        res = request.env[model_name].browse(record_id).with_context(
            company_id=self._get_allowed_company_ids()[0]).get_barcode_view_state()
        return res

    def _get_action(self, transfer):
        """
        return the action to display the picking. We choose between the traditionnal
        form view and the new client action
        """
        if transfer.state == 'transfer':
            view_id = request.env.ref('ev_stock_transfer.stock_transfer_to_form_view').id
        else:
            view_id = request.env.ref('ev_stock_transfer.stock_transfer_from_form_view').id
        return {
            'action': {
                'name': _('Open Transfer form'),
                'res_model': 'stock.transfer',
                'view_mode': 'form',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'res_id': transfer.id,
                'context': {'active_id': transfer.id}
            }
        }


