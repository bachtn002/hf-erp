import odoo
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.safe_eval import safe_eval
import ast


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def read(self, fields=None, load='_classic_read'):
        result = super(IrActionsActWindow, self).read(fields, load=load)
        # User root
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            return result

        result = self._get_domain_access_right(result)
        if not fields or 'help' in fields:
            for values in result:
                model = values.get('res_model')
                if model in self.env:
                    eval_ctx = dict(self.env.context)
                    try:
                        ctx = safe_eval(values.get('context', '{}'), eval_ctx)
                    except:
                        ctx = {}
                    values['help'] = self.with_context(**ctx).env[model].get_empty_list_help(values.get('help', ''))
        return result

    def _get_domain_access_right(self, result):
        for values in result:
            model = values.get('res_model')
            if model == 'stock.picking' or model == 'stock.move' or model == 'stock.move.line':
                values['domain'] = self._get_location_access_right(fields=['location_id', 'location_dest_id'],
                                                                   operator='|', domain=values.get('domain'))
            if model == 'stock.inventory':
                values['domain'] = self._get_location_access_right(fields=['location_ids'], operator=False,
                                                                   domain=values.get('domain'))
            if model == 'stock.warehouse':
                values['domain'] = self._get_warehouse_access_right(domain=values.get('domain'))
            if model == 'stock.picking.type':
                values['domain'] = self._get_warehouse_access_right(field='warehouse_id', domain=values.get('domain'))
            if model == 'stock.location':
                values['domain'] = self._get_location_access_right(fields=['id'], operator=False,
                                                                   domain=values.get('domain'))
            if model == 'stock.quant':
                values['domain'] = self._get_location_access_right(fields=['location_id'], operator=False,
                                                                   domain=values.get('domain'))
            if model == 'stock.scrap':
                values['domain'] = self._get_location_access_right(fields=['location_id'], operator=False,
                                                                   domain=values.get('domain'))
            if model == 'stock.rule':
                values['domain'] = self._get_location_access_right(fields=['location_id'], operator=False,
                                                                   domain=values.get('domain'))
        return result

    def _get_warehouse_access_right(self, field='id', domain=False):
        warehouse_ids = self.env['stock.warehouse']._get_warehouse_by_access_right()
        if domain == False:
            domain = []
        else:
            if domain == '':
                domain = []
            else:
                domain = ast.literal_eval(domain)
        warehouse_id = []
        warehouse_id.append(field)
        warehouse_id.append('in')
        if warehouse_ids == False:
            warehouse_id.append(False)
        else:
            warehouse_id.append(warehouse_ids.ids)
        domain.append(warehouse_id)
        return str(domain)

    def _get_location_access_right(self, fields=[], operator=False, domain=False):
        location_ids = self.env['stock.warehouse']._get_location_by_warehouse_access_right()
        if domain == False:
            domain = []
        else:
            if domain == '':
                domain = []
            else:
                domain = domain.replace('\n', '')
                domain = domain.replace('\t', '')
                domain = ast.literal_eval(domain)
        if operator != False:
            domain.append(operator)
        for field in fields:
            args = []
            args.append(field)
            args.append('in')
            args.append(location_ids)
            domain.append(args)
        return str(domain)
