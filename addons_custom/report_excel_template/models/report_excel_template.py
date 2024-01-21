# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api,_
import io
import os
import sqlparse
from datetime import date, datetime as dt
import base64
_logger = logging.getLogger(__name__)
try:
    from openpyxl import load_workbook
    from openpyxl.utils.exceptions import IllegalCharacterError
except ImportError:
    _logger.debug(
        'Cannot import "openpyxl". Please make sure it is installed.')

from odoo.exceptions import ValidationError

from random import randint
from . import common as co
from ast import literal_eval


class ReportExcelTemplate(models.Model):
    _name = 'report.excel.template'
    _description = "Report Excel Template"

    name = fields.Char('Name')
    parent_menu_id = fields.Many2one('ir.ui.menu','Parent Menu')
    menu_id = fields.Many2one('ir.ui.menu','Menu')
    act_window_id = fields.Many2one('ir.actions.act_window','Act Window')
    type = fields.Selection([('sql','Sql'),('model','Model')], 'Report Data', default='sql')
    sql = fields.Text('Sql')
    report_url = fields.Char('Url Report')
    model_id = fields.Many2one('ir.model', 'Model', domain=[('transient','=', False)])
    input_ids = fields.One2many('report.input','report_id', 'Report Input')
    label_ids = fields.One2many('report.label','report_id', 'Report Label')
    parameter_ids = fields.One2many('report.parameter', 'report_id', 'Parameter')
    groups_id = fields.Many2many('res.groups', 'rule_group_report_excel_template_rel', 'rule_group_id', 'group_id')
    state = fields.Selection([('draft','New'), ('settings','Settings'),('done','Done')], string='State', default='draft')
    field_ids = fields.One2many('report.field','report_id',' Field Data')
    file_excel_template = fields.Binary('Excel Template')
    print_menu = fields.Boolean('Print Menu', default=False)

    export_ids = fields.One2many('xlsx.report.export', 'report_id', 'Export')

    input_instruction = fields.Text(
        string='Instruction (Input)',
        help="This is used to construct instruction in tab Import/Export",
    )
    instruction = fields.Text(
        string='Instruction',
        compute='_compute_output_instruction',
        help="Instruction on how to import/export, prepared by system."
    )
    show_instruction = fields.Boolean(
        string='Show Output',
        default=False,
        help="This is the computed instruction based on tab Import/Export,\n"
             "to be used by xlsx import/export engine",
    )
    sheet_name = fields.Char('Sheet Name')
    model = fields.Char('Model')
    model_id2 = fields.Many2one('ir.model', 'Model 2', domain=[('transient', '=', False)])

    @api.onchange('model')
    def _onchange_model(self):
        if self.model != '':
            model_id = self.env['ir.model'].sudo().search([('model','=', self.model)], limit=1)
            if model_id.id == False:
                raise ValidationError(_('This model does not exist on the system.'))
            self.model_id2 = model_id.id

    @api.onchange('print_menu')
    def _onchange_print_menu(self):
        if self.print_menu:
            self.type = 'model'

    @api.onchange('model_id')
    def _onchange_print_model_id(self):
        if self.model_id.id:
            self.model = self.model_id.model
        else:
            self.model = ''

    def _get_template_export_excel(self, **kw):
        report_id = self.search([('id','=', kw['report_id'])])
        datas, inputs = self._get_data_report(**kw)
        content, file_name = self.env['xlsx.export'].export_report_excel(report_id, datas, inputs)
        return content,file_name


    def action_confirm(self):
        if self.state == 'draft':
            self._compute_parameter()
            self._compute_select_value()
            self.write({'state': 'settings'})

            return True

        if self.state == 'settings':
            if self.print_menu == False:
                action_id = self._create_action_report(self.name, self)
                menu_id = self._create_menu_report(self.name, self.parent_menu_id.id, self.groups_id.id, action_id)
                self.menu_id = menu_id.id
                self.act_window_id = action_id.id
            self.write({'state': 'done'})
            return True
    #Create Parameter
    def _compute_parameter(self):
        if self.type != 'sql':
            return True
        if self.state == 'draft':
            parameters = self.sql.count('%s')
            for i in range(parameters):
                self.env['report.parameter'].create({
                    'name': 'param_' + str(i),
                    'report_id': self.id
                })
        if self.state == 'settings':
            self.parameter_ids.unlink()
    #Create Column report
    def parse_sql_columns(self, sql):
        columns = []
        parsed = sqlparse.parse(sqlparse.format(sql, reindent=True))
        stmt = parsed[0]
        for token in stmt.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    columns.append(str(identifier))
                break
        return columns


    def _get_inserted_values(self, parsed):
        values = ''
        for item in parsed.tokens:
            if item.value != '':
                values += ' ' + item.value
        #values += ' OFFSET %s LIMIT %s'
        return values

    #Add Column in Sql
    def _add_sql_columns(self,sql):
        parsed = sqlparse.parse(sqlparse.format(sql, reindent=True))
        stmt = parsed[0]
        number = 0
        for token in stmt.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                stmt.tokens[number].tokens.insert(len(stmt.tokens[number].tokens) + 1,
                                          sqlparse.sql.Token('Identifier', ','))
                stmt.tokens[number].tokens.insert(len(stmt.tokens[number].tokens) + 2 , sqlparse.sql.Token('Identifier', 'count(*) OVER() AS total_count'))
                stmt.tokens[number].value += ', count(*) OVER() AS total_count'
                break
            number = number + 1
        return self._get_inserted_values(stmt)


    def _compute_select_value(self):
        if self.type != 'sql':
            return True
        if self.state == 'draft':
            if self.sql == False:
                return True
            try:
                columns = self.parse_sql_columns(self.sql)
                i = 0
                for column in columns:
                    col = column.split()
                    over = False
                    for c in col:
                        if c == 'OVER()' or c == 'over()':
                            over = True
                            break
                    if over == False:
                        self.env['report.label'].create({
                            'name': col[len(col)-1],
                            'report_id': self.id
                        })
                    i = i + 1
            except StopIteration:
                raise ValueError("Not enough parameters provided")
            return True
        if self.state == 'settings':
            self.label_ids.unlink()

    def action_back(self):
        if self.state == 'settings':
            self._compute_parameter()
            self._compute_select_value()
            self.act_window_id.sudo().unlink()
            self.menu_id.sudo().unlink()
            self.write({'state': 'draft'})

        if self.state == 'done':
            self.act_window_id.sudo().unlink()
            self.menu_id.sudo().unlink()
            self.write({'state': 'settings'})


    def _create_menu_report(self, name, parent_menu_id, groups_id,action_id):
        if action_id.id == False:
            raise ValidationError(_('Action does not exist'))
        action = 'ir.actions.act_window,' +  str(action_id.id)
        _args = {
            'name': name,
            'parent_id': parent_menu_id,
            'action': action,
            'groups_id': groups_id,
        }

        return self.env['ir.ui.menu'].create(_args)

    def _create_action_report(self, name, report_id):
        view_id = self.env['ir.ui.view'].search([('model', '=', 'report.excel.template.wizard')]).id
        act_window_args = {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'report.excel.template.wizard',
            'view_mode': 'form',
            'view_id':view_id,
            'target':'new',
            'context': {'model': 'report.excel.template', 'report_id': report_id.id},
        }
        return self.env['ir.actions.act_window'].create(act_window_args)


    @api.model
    def create(self, vals):
        record = super(ReportExcelTemplate, self).create(vals)
        if vals['print_menu'] and vals.get('input_instruction'):
            record._compute_input_export_instruction()
        return record

    def write(self, vals):
        record = super(ReportExcelTemplate, self).write(vals)
        if self.print_menu and vals.get('input_instruction'):
            record._compute_input_export_instruction()
        return record

    def _compute_input_export_instruction(self):
        self = self.with_context(compute_from_input=True)
        for rec in self:
            # Export Instruction
            input_dict = literal_eval(rec.input_instruction.strip())
            rec.export_ids.unlink()
            export_dict = input_dict.get('__EXPORT__')
            if not export_dict:
                continue
            export_lines = []
            sequence = 0
            # Sheet
            for sheet, rows in export_dict.items():
                sequence += 1
                vals = {'sequence': sequence,
                        'section_type': 'sheet',
                        'sheet': str(sheet),
                        }
                export_lines.append((0, 0, vals))
                # Rows
                for row_field, lines in rows.items():
                    sequence += 1
                    is_cont = False
                    if '_CONT_' in row_field:
                        is_cont = True
                        row_field = row_field.replace('_CONT_', '')
                    vals = {'sequence': sequence,
                            'section_type': (row_field == '_HEAD_' and
                                             'head' or 'row'),
                            'row_field': row_field,
                            'is_cont': is_cont,
                            }
                    export_lines.append((0, 0, vals))
                    for excel_cell, field_name in lines.items():
                        sequence += 1
                        vals = {'sequence': sequence,
                                'section_type': 'data',
                                'excel_cell': excel_cell,
                                'field_name': field_name,
                                }
                        export_lines.append((0, 0, vals))
            rec.write({'export_ids': export_lines})


    def _compute_output_instruction(self):
        """ From database, compute back to dictionary """
        for rec in self:
            inst_dict = {}
            prev_sheet = False
            prev_row = False
            # Export Instruction
            itype = '__EXPORT__'
            inst_dict[itype] = {}
            for line in rec.export_ids:
                if line.section_type == 'sheet':
                    sheet = co.isinteger(line.sheet) and \
                        int(line.sheet) or line.sheet
                    sheet_dict = {sheet: {}}
                    inst_dict[itype].update(sheet_dict)
                    prev_sheet = sheet
                    continue
                if line.section_type in ('head', 'row'):
                    row_field = line.row_field
                    if line.section_type == 'row' and line.is_cont:
                        row_field = '_CONT_%s' % row_field
                    row_dict = {row_field: {}}
                    inst_dict[itype][prev_sheet].update(row_dict)
                    prev_row = row_field
                    continue
                if line.section_type == 'data':
                    excel_cell = line.excel_cell
                    field_name = line.field_name or ''
                    field_name += line.field_cond or ''
                    field_name += line.style or ''
                    field_name += line.style_cond or ''
                    if line.is_sum:
                        field_name += '@{sum}'
                    cell_dict = {excel_cell: field_name}
                    inst_dict[itype][prev_sheet][prev_row].update(cell_dict)
                    continue

            rec.instruction = inst_dict


    def unlink(self):
        for rec in self:
            rec.act_window_id.sudo().unlink()
            rec.menu_id.sudo().unlink()
        res = super(ReportExcelTemplate, self).unlink()
        return res

    @api.model
    def _fetch_report_input(self, report_id):
        report_input_data = []
        report_input_ids = self.env['report.input'].search([('report_id','=', report_id)], order="sequence")
        for input in report_input_ids:
            input_args = {
                'sequence': input.sequence,
                'name': input.name,
                'label': input.label,
                'type': input.type,
                'model': input.model_id.model or '',
                'multiple': input.multiple,
                'required': input.required,
                'parameters': input.parameters,
                'format': input.format_value,
            }
            report_input_data.append(input_args)
        return report_input_data

    @api.model
    def _fetch_report_label(self, report_id):
        report_label_data = []
        report_id = self.browse(report_id)
        if report_id.type == 'sql':
            report_label_ids = self.env['report.label'].search([('report_id','=', report_id)], order="sequence")
            for label in report_label_ids:
                label_args = {
                    'name': label.name,
                    'label': label.label,
                    'pivot_default': label.pivot_default,
                }
                report_label_data.append(label_args)
        else:
            report_label_ids = self.env['report.field'].search([('report_id', '=', report_id)],
                                                                       order="sequence")
            for label in report_label_ids:
                label_args = {
                    'sequence': label.sequence,
                    'name': label.field_id.name,
                    'label': label.label,
                    'pivot_default': label.pivot_default,
                }
                report_label_data.append(label_args)
        return report_label_data

    @api.model
    def fetch_report(self, report_id):
        report_data = {
            'name': self.browse(report_id).name,
            'type': self.browse(report_id).type,
            'view_type': self.browse(report_id).view_type,
            'sql': self.browse(report_id).sql,
            'report_url': self.browse(report_id).report_url,
            'model': self.browse(report_id).model_id.model or '',
            'input': self._fetch_report_input(report_id),
            'label': self._fetch_report_label(report_id),
        }
        return report_data


    def _get_params_where(self, report_id, params):
        where = []
        if report_id.type == 'sql':
            for param in report_id.parameter_ids:
                if param.value != False and param.input.id == False:
                    where.append(param.value)
                elif params[param.input.name] == 'false' and param.input.type == 'model':
                    where.append(0)
                elif params[param.input.name] == '' and param.input.type == 'model':
                    if param.value == '0':
                        where.append(0)
                    else:
                        where.append(tuple([0,0]))
                else:
                    if param.input.type == 'many2many':
                        if param.value == '0':
                            where.append(1)
                        else:
                            p_array = params[param.input.name].split(',')
                            p_array.append(0)
                            where.append(tuple(p_array))
                    else:
                        where.append(params[param.input.name])
            return where
        else:
            for param in report_id.parameter_ids:
                args = []
                if param.input.id == False:
                    args.append(param.field_id.name)
                    args.append(param.operator)
                    try:
                        args.append(float(param.value))
                    except:
                        args.append(float(param.value))
                    where.append(args)
                    continue
                if params[param.input.name] != 'false' and params[param.input.name] != '0' and params[param.input.name] != '':
                    args.append(param.field_id.name)
                    args.append(param.operator)
                    if param.input.type == 'model':
                        args.append(int(params[param.input.name]))
                    else:
                        args.append(params[param.input.name])
                    where.append(args)
                    continue
                if param.input.format_value != False:
                    args.append(param.field_id.name)
                    args.append(param.operator)
                    args.append(param.input.formart_value)
                    where.append(args)
            return where

    def _get_field_data_read(self, report_id):
        fields = []
        field_ids = self.env['report.field'].search([('report_id','=', report_id.id)], order="sequence")
        for field in field_ids:
            if field.field_id.id != False:
                fields.append(field.field_id.name)
        return fields

    def _get_data_report(self, **params):
        inputs = params
        report_id = self.browse(int(params['report_id']))
        if report_id.type == 'sql':
            params_where = self._get_params_where(report_id, params)
            sql = self._add_sql_columns(report_id.sql)
            query = sql % tuple(params_where)
            self._cr.execute(query)
            report_data = self._cr.dictfetchall()
            return report_data,inputs
        else:
            params_where = self._get_params_where(report_id, params)
            colums = self._get_field_data_read(report_id)
            report_data = self.env[report_id.model].search_read(params_where, colums, order='id')
            return report_data,inputs

class ReportInput(models.Model):
    _name = 'report.input'
    _description = 'Report Input'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Field Name')
    label = fields.Char('Label')
    type = fields.Selection([('many2many','Many2many'),('many2one','Many2one'),('date','Date'),('text','Text')],'Type')
    model_id = fields.Many2one('ir.model','Model')
    required = fields.Boolean('Required', default=True)
    report_id = fields.Many2one('report.excel.template','Report')
    field_id = fields.Many2one('ir.model.fields','Field')
    excel_cell = fields.Char('Excel Cell')
    field_cond = fields.Char('Field Cond.')
    style = fields.Char('Default Style')
    style_cond = fields.Char('Style w/Cond.')

    def _random_number(self):
        random_str = ''
        for i in range(6):
            random_str += str(randint(0, 9))
        return random_str

    @api.model
    def create(self, vals):
        record = super(ReportInput, self).create(vals)
        model_id = self.env['ir.model'].search([('model', '=', 'report.excel.template.wizard')]).id
        relation = self.env['ir.model'].search([('id','=',vals['model_id'])])
        field_arrgs = {
            'name': 'x_' + vals['name'] + '_' + self._random_number(),
            'field_description': vals['label'],
            'model_id': model_id,
            'ttype': vals['type'],
            'relation': relation.model,
        }
        field = self.env['ir.model.fields'].create(field_arrgs)
        record.field_id = field.id
        return record

    def write(self, vals):
        if 'model_id' in vals:
            relation = self.env['ir.model'].search([('id', '=', vals['model_id'])])
            self.field_id.write({'relation': relation.model})
        if 'label' in vals:
            self.field_id.write({'field_description': vals['label']})
        if 'type' in vals:
            self.field_id.write({'ttype': vals['type']})
        if 'name' in vals:
            self.field_id.write({'name': 'x_' + vals['name'] + '_' + self._random_number()})
        return super(ReportInput, self).write(vals)

    def unlink(self):
        self.field_id.unlink()
        return super(ReportInput, self).unlink()


class ReportGroup(models.Model):
    _name = 'report.group'
    _description = 'Report Group'

    name = fields.Char('Name')


class ReportLabel(models.Model):
    _name = 'report.label'
    _description = 'Report Label'

    name = fields.Char('Name', translate=True)
    label = fields.Char('Label', translate=True)
    report_id = fields.Many2one('report.excel.template', 'Report')
    group_id = fields.Many2one('report.group', 'Group')
    pivot_default = fields.Selection([('row','Rows'), ('col', 'Cols')],'Pivot Default')
    excel_cell = fields.Char('Excel Cell')
    field_cond = fields.Char('Field Cond.')
    style = fields.Char('Default Style')
    style_cond = fields.Char('Style w/Cond.')
    numerical_order = fields.Boolean('Numerical Order')
    sum = fields.Boolean('Sum')

class ReportParameter(models.Model):
    _name = 'report.parameter'
    _description = 'Report Parameter'

    name = fields.Char('Parameter')
    input = fields.Many2one('report.input','Input')
    report_id = fields.Many2one('report.excel.template', 'Report')
    field_id = fields.Many2one('ir.model.fields', 'Field')
    operator = fields.Selection([('>', '>'), ('>=', '>='), ('<=', '<='), ('<', '<'), ('=', '='),('in','in')], 'Operator')
    model_id = fields.Many2one('ir.model', 'Model', related='report_id.model_id')
    value = fields.Char('Value')

class ReportField(models.Model):
    _name = 'report.field'
    _description = 'Report Field'

    sequence = fields.Integer('Sequence', default=10)
    field_id = fields.Many2one('ir.model.fields','Field')
    label = fields.Char('Label')
    report_id = fields.Many2one('report.excel.template', 'Report')
    model_id = fields.Many2one('ir.model', 'Model', related='report_id.model_id2')
    pivot_default = fields.Selection([('row', 'Rows'), ('col', 'Cols')], 'Pivot Default')
    format_value = fields.Char('Format Value')
    model = fields.Char('Model', related='report_id.model')
    excel_cell = fields.Char('Excel Cell')
    field_cond = fields.Char('Field Cond.')
    style = fields.Char('Default Style')
    style_cond = fields.Char('Style w/Cond.')
    numerical_order = fields.Boolean('Numerical Order')
    sum = fields.Boolean('Sum')

    @api.onchange('field_id')
    @api.depends('field_id')
    def _onchange_field_id(self):
        if self.field_id.id != False:
            self.label = self.field_id.name

class XLSXReportExport(models.Model):
    _name = 'xlsx.report.export'
    _description = 'Detailed of how excel data will be exported'
    _order = 'sequence'

    report_id = fields.Many2one('report.excel.template', 'Report')
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    sheet = fields.Char(
        string='Sheet',
    )
    section_type = fields.Selection(
        [('sheet', 'Sheet'),
         ('head', 'Head'),
         ('row', 'Row'),
         ('data', 'Data')],
        string='Section Type',
        required=True,
    )
    row_field = fields.Char(
        string='Row Field',
        help="If section type is row, this field is required",
    )
    is_cont = fields.Boolean(
        string='Continue',
        default=False,
        help="Continue data rows after last data row",
    )
    excel_cell = fields.Char(
        string='Cell',
    )
    field_name = fields.Char(
        string='Field',
    )
    field_cond = fields.Char(
        string='Field Cond.',
    )
    is_sum = fields.Boolean(
        string='Sum',
        default=False,
    )
    style = fields.Char(
        string='Default Style',
    )
    style_cond = fields.Char(
        string='Style w/Cond.',
    )

    @api.model
    def create(self, vals):
        new_vals = self._extract_field_name(vals)
        return super(XLSXReportExport, self).create(new_vals)

    @api.model
    def _extract_field_name(self, vals):
        if self._context.get('compute_from_input') and vals.get('field_name'):
            field_name, field_cond = co.get_field_condition(vals['field_name'])
            field_cond = field_cond or 'value or ""'
            field_name, style = co.get_field_style(field_name)
            field_name, style_cond = co.get_field_style_cond(field_name)
            field_name, func = co.get_field_aggregation(field_name)
            vals.update({'field_name': field_name,
                         'field_cond': '${%s}' % (field_cond or ''),
                         'style': '#{%s}' % (style or ''),
                         'style_cond': '#?%s?' % (style_cond or ''),
                         'is_sum': func == 'sum' and True or False,
                         })
        return vals
