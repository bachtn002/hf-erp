from odoo import http
from odoo.http import request
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class StockPickingStampPrint(http.Controller):
    @http.route('/report/pdf/ev_stock_picking.stock_production_lot_temp_printing/<lot_id>', type='http', auth='public',
                website=True)
    def stamp_print_production_lot(self, lot_id, **kwargs):
        lot_id = request.env['stock.production.lot'].browse(int(lot_id))
        return http.request.render('ev_stock_picking.stock_production_lot_temp_printing',
                                   {'lot_id': lot_id})

    @http.route('/report/pdf/ev_stock_picking.stamp_printing_product_product_lot/<product_id>', type='http',
                auth='public', website=True)
    def stamp_printing_product_product_lot(self, product_id, **kwargs):
        product_id = request.env['product.template'].browse(int(product_id))
        return http.request.render('ev_stock_picking.stamp_printing_product_product_lot',
                                   {'product_id': product_id})

    @http.route('/report/pdf/ev_stock_picking.production_lot_print_stamp/<production_lot_id>', type='http',
                auth='public',
                website=True)
    def production_lot_print_stamp(self, production_lot_id, **kwargs):
        production_lots = request.env['production.lot.print.stamp'].browse(int(production_lot_id))
        lot_ids = production_lots.production_lot_ids
        return http.request.render('ev_stock_picking.stock_production_lots_temps_printing',
                                   {'lot_ids': lot_ids})

    @http.route('/report/pdf/ev_stock_picking.product_product_print_stamp/<product>', type='http', auth='public',
                website=True)
    def product_product_print_stamp(self, product, **kwargs):
        products = request.env['product.product.print.stamp'].browse(int(product))
        lot_ids = products.product_ids
        return http.request.render('ev_stock_picking.stamp_printing_product_product_lots',
                                   {'lot_ids': lot_ids})


class AccountJournalGeneralController(http.Controller):
    @http.route('/account/journal_general/create_update', type='http', auth='public', website=True)
    def create_update_account_journal_general(self, **kwargs):
        # create_new_journal_general
        self._create_update_journal_general()

    def _create_update_journal_general(self):
        account_move_ids = request.env['account.move'].search([('state', '=', 'posted')])
        stt = 1
        _logger.info(f'start: {datetime.now()}')
        for move in account_move_ids:
            start_time = datetime.now()
            query = f"""DELETE FROM account_journal_general WHERE account_move_id = {move.id}"""
            request._cr.execute(query)
            move._update_contra_account_id()
            stt += 1
            _logger.info(f'move_{stt} time: {datetime.now() - start_time}')
