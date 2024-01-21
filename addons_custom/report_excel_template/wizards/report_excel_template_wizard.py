# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api,_
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')
_unlink = logging.getLogger(__name__ + '.unlink')
from lxml import etree
from lxml.builder import E
import ast
from odoo.tools.misc import get_lang
from odoo.tools import pycompat

class ReportExcelTemplate(models.TransientModel):
    _name = 'report.excel.template.wizard'

    report_description = fields.Char('Report Description')
    report_name = fields.Char('Report Name')

    def export_excel(self):
        report_id = self.env['report.excel.template'].sudo().search([('id','=',self.env.context['report_id'])])
        url_export = '/report_excel_template/?report_id=' + str(self.env.context['report_id'])
        for input in report_id.input_ids:
            if input.type == 'many2one':
                field_input = getattr(self, input.field_id.name)
                url_export += '&' + input.name + '=' + str(field_input.id)
            elif input.type == 'many2many':
                field_input = getattr(self, input.field_id.name)
                list_field_input = ",".join(str(x) for x in field_input.ids)
                url_export += '&' + input.name + '=' + list_field_input
            else:
                to_text = pycompat.to_text
                field_input = getattr(self, input.field_id.name)
                date_str = to_text(field_input.strftime('%Y-%m-%d'))
                url_export += '&' + input.name + '=' + date_str
        return {
            'name': 'Excel Report',
            'type': 'ir.actions.act_url',
            'url': url_export,
        }

    @api.model
    def load_views(self, views, options=None):
        options = options or {}
        result = {}
        toolbar = options.get('toolbar')
        view_default = {
            v_type: self.fields_view_get(v_id, v_type if v_type != 'list' else 'tree',
                                         toolbar=toolbar if v_type != 'search' else False,action_id=options.get('action_id'))
            for [v_id, v_type] in views
        }
        result['fields_views'] = view_default
        result['fields'] = self.fields_get()

        if options.get('load_filters'):
            result['filters'] = self.env['ir.filters'].get_filters(self._name, options.get('action_id'))

        return result


    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False, action_id=None):
        View = self.env['ir.ui.view'].sudo()
        result = {
            'model': self._name,
            'field_parent': False,
        }

        # try to find a view_id if none provided
        if not view_id:
            # <view_type>_view_ref in context can be used to overrride the default view
            view_ref_key = view_type + '_view_ref'
            view_ref = self._context.get(view_ref_key)
            if view_ref:
                if '.' in view_ref:
                    module, view_ref = view_ref.split('.', 1)
                    query = "SELECT res_id FROM ir_model_data WHERE model='ir.ui.view' AND module=%s AND name=%s"
                    self._cr.execute(query, (module, view_ref))
                    view_ref_res = self._cr.fetchone()
                    if view_ref_res:
                        view_id = view_ref_res[0]
                else:
                    _logger.warning('%r requires a fully-qualified external id (got: %r for model %s). '
                                    'Please use the complete `module.view_id` form instead.', view_ref_key, view_ref,
                                    self._name)

            if not view_id:
                # otherwise try to find the lowest priority matching ir.ui.view
                view_id = View.default_view(self._name, view_type)

        if view_id:
            # read the view with inherited views applied
            root_view = View.browse(view_id).read_combined(['id', 'name', 'field_parent', 'type', 'model', 'arch'])
            if view_type == 'form':
                root_view_arch_tree = ET.fromstring(root_view['arch'])
                node_group = root_view_arch_tree.find('group')
                action_obj = self.env['ir.actions.act_window'].sudo().search([('id','=', action_id)])
                context = ast.literal_eval(action_obj.context)
                excel_report_template_id = self.env[context['model']].sudo().search([('id','=', context['report_id'])])
                input_ids = sorted(excel_report_template_id.input_ids, key=lambda k: k['sequence'])
                for input in input_ids:
                    if input.required:
                        if input.type == 'many2many':
                            el = ET.Element('field', {'name': input.field_id.name, 'required': '1','widget': 'many2many_tags'})
                        else:
                            el = ET.Element('field', {'name': input.field_id.name, 'required': '1'})
                    else:
                        if input.type == 'many2many':
                            el = ET.Element('field', {'name': input.field_id.name,'widget': 'many2many_tags'})
                        else:
                            el = ET.Element('field',{'name': input.field_id.name})
                    node_group.append(el)
                result['arch'] = ET.tostring(root_view_arch_tree, encoding='utf8', method='xml')
            else:
                result['arch'] = root_view['arch']
            result['name'] = root_view['name']
            result['type'] = root_view['type']
            result['view_id'] = root_view['id']
            result['field_parent'] = root_view['field_parent']
            result['base_model'] = root_view['model']
        else:
            # fallback on default views methods if no ir.ui.view could be found
            try:
                arch_etree = getattr(self, '_get_default_%s_view' % view_type)()
                result['arch'] = etree.tostring(arch_etree, encoding='unicode')
                result['type'] = view_type
                result['name'] = 'default'
            except AttributeError:
                raise UserError(_("No default view of type '%s' could be found !", view_type))
        return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False, action_id=None):
        self.check_access_rights('read')
        view = self.env['ir.ui.view'].sudo().browse(view_id)

        # Get the view arch and all other attributes describing the composition of the view
        result = self._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu,action_id=action_id)

        # Override context for postprocessing
        if view_id and result.get('base_model', self._name) != self._name:
            view = view.with_context(base_model_name=result['base_model'])

        # Apply post processing, groups and modifiers etc...
        xarch, xfields = view.postprocess_and_fields(etree.fromstring(result['arch']), model=self._name)
        result['arch'] = xarch
        result['fields'] = xfields

        # Add related action information if aksed
        if toolbar:
            vt = 'list' if view_type == 'tree' else view_type
            bindings = self.env['ir.actions.actions'].get_bindings(self._name)
            resreport = [action
                         for action in bindings['report']
                         if vt in (action.get('binding_view_types') or vt).split(',')]
            resaction = [action
                         for action in bindings['action']
                         if vt in (action.get('binding_view_types') or vt).split(',')]

            result['toolbar'] = {
                'print': resreport,
                'action': resaction,
            }
        return result