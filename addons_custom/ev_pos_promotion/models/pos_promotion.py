# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from odoo.osv import osv
from odoo.tools import ustr

import base64
import xlrd


class PosPromotion(models.Model):
    _name = 'pos.promotion'
    _inherit = ['mail.thread']
    _description = 'Pos promotion'
    _order = 'name ASC'

    def _get_product_id_domain(self):
        return [('type', '=', 'service')]

    name = fields.Char(string=_('Name'),
                       required=True)
    product_id = fields.Many2one('product.product',
                                 string=_("Product"),
                                 domain=_get_product_id_domain,
                                 help=_("Use to calculate promotion value. Type is service"), required=0, readonly=1)
    company_id = fields.Many2one('res.company',
                                 string=_('Company'),
                                 default=False)
    state = fields.Selection([
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('cancel', _('Cancel'))],
        string=_('State'),
        default='draft',
        required=True,
        tracking=True,
        copy=False)
    type = fields.Selection([], string=_('Type'))
    start_date = fields.Date(string=_('Start date'),
                             default=fields.Date.today(),
                             required=True,
                             tracking=True)
    end_date = fields.Date(string=_('End date'),
                           default=fields.Date.today(),
                           required=True,
                           tracking=True)
    pos_configs = fields.Many2many('pos.config',
                                   string=_('Pos config'),
                                   required=False,
                                   help='If not setting, apply promotion for all pos')
    start_time = fields.Float(string=_('Start time'),
                              default=0.0,
                              required=True,
                              tracking=True)
    end_time = fields.Float(string=_('End time'),
                            default=0.0,
                            required=True,
                            tracking=True)
    partner_groups = fields.Many2many('res.partner.group',
                                      string=_('Res partner groups'))
    partner_groups_not = fields.Many2many('res.partner.group', 'promotion_not_partner_group_rel',
                                          string=_('Res partner groups Not'))
    partner_ids_not = fields.Many2many('res.partner', 'promotion_not_partner_from_group_rel', string="Partners")
    partner_ids = fields.Many2many('res.partner', string="Partners")
    partner_ids_without_group = fields.Many2many('res.partner', 'promotion_res_partner_group_rel', string="Partners")
    partner_domain = fields.Char("Partner domain", help="Alternative to a list of partners")
    priority = fields.Integer(string=_('Priority'), default=0)
    x_partner_not_ids = fields.Many2many('res.partner', 'res_partner_rel', string="Partners")
    vaction_ids = fields.Many2many('custom.weekdays', string=_('Days'))
    note = fields.Char(string='Hướng dẫn sử dụng CTKM theo thứ',
                       default='Code 1 - Thứ 2, code 2- Thứ 3, code 3-Thứ 4, code 4-Thứ 5, code 5-Thứ6, code 6-Thứ 7, code 7- Chủ Nhật',
                       required=True, readonly=1)
    import_file = fields.Boolean('Import file')
    field_binary_import = fields.Binary(string="Field Binary Import", copy=False)
    field_binary_import_partner = fields.Binary(string="Field Binary Import", copy=False)
    field_binary_import_not_partner = fields.Binary(string="Field Binary Import", copy=False)
    field_binary_name = fields.Char(string="Field Binary Name")
    time_add = fields.Boolean('Time add')
    weekday_add = fields.Boolean('Weekdays')
    rule_apply_promotion = fields.Boolean(string=_('Rule apply promotion'), default=True)
    apply_all_pos_config = fields.Boolean(string=_('Apply all pos config'), default=True)
    apply_manual_pos_config = fields.Boolean(string=_('Apply manual pos config'), default=False)
    apply_all_res_partner_apply = fields.Boolean(string=_('Apply all res partner apply'))
    apply_manual_res_partner_apply = fields.Boolean(string=_('Apply manual res partner apply'))
    apply_all_res_partner_not_apply = fields.Boolean(string=_('Apply all res partner not apply'))
    apply_manual_res_partner_not_apply = fields.Boolean(string=_('Apply manual res partner not apply'))

    @api.constrains('start_time')
    def _check_start_time(self):
        if self.start_time < 0 or self.start_time > 24:
            raise UserError(_('Start time error!'))

    @api.constrains('end_time')
    def _check_end_time(self):
        if self.end_time < 0 or self.end_time > 24:
            raise UserError(_('End time error!'))

    @api.constrains('start_time', 'end_time', 'time_add')
    def _check_start_end_time(self):
        if self.start_time > self.end_time and self.time_add == True:
            raise UserError(_('Time start not than time end'))
        elif self.start_time == 0 and self.end_time == 0 and self.time_add == True and self.weekday_add and len(
                self.vaction_ids) == 0:
            raise UserError(_('Time add and weekday not input'))
        elif self.start_time == 0 and self.end_time == 0 and self.time_add == True:
            raise UserError(_('Time add not input'))
        elif self.start_time == self.end_time and self.time_add == True:
            raise UserError(_('Time start and time and not same'))

    @api.constrains('time_add')
    def _check_time_add(self):
        if not self.time_add:
            self.start_time = 0.0
            self.end_time = 0.0

    @api.constrains('partner_groups', 'partner_groups_not')
    def check_constrains_partner_group(self):
        for group in self.partner_groups_not:
            if group in self.partner_groups:
                raise UserError(_('Group partner not apply and apply promotion not same '))

    @api.constrains('weekday_add')
    def _check_weekday_add(self):
        if not self.weekday_add:
            self.vaction_ids = False
        elif self.weekday_add and len(self.vaction_ids) == 0:
            raise UserError(_('Weekday error!'))

    @api.model
    def create(self, vals):
        vals = self.vals_factory(vals)
        product_km = self.env['product.product'].search([('name', '=', 'KM')], limit=1)
        if len(product_km) > 0:
            for pr in product_km:
                vals['product_id'] = pr.id
        else:
            self.env['product.product'].create({
                'name': 'KM',
                'type': 'service',
                'sale_ok': True,
                'purchase_ok': True,
                'default_code': 'KM',
                'available_in_pos': True,
            })
            self.env.cr.commit()
            product_km_add = self.env['product.product'].search([('name', '=', 'KM')], limit=1)
            vals['product_id'] = product_km_add.id
        apply_and_not_apply_list = []
        for apply in vals['partner_ids_without_group'][0][2]:
            if apply in vals['x_partner_not_ids'][0][2]:
                apply_and_not_apply_list.append(apply)
        if apply_and_not_apply_list:
            name_list = []
            partner_ids = self.env['res.partner'].browse(apply_and_not_apply_list)
            for partner_id in partner_ids:
                name_list.append(partner_id.name)
            name = ','.join([str(name) for name in name_list])
            raise UserError(_('Have customer in list apply and list not apply together\n (%s)' %
                              name))

        return super(PosPromotion, self).create(vals)

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def download_template_pos_config(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion/static/template/mẫu phiếu import điểm bán lẻ áp dụng.xls',
            "target": "_parent",
        }

    def download_template_res_partner(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion/static/template/mẫu phiếu import khách hàng áp dụng.xls',
            "target": "_parent",
        }

    def download_template_not_res_partner(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion/static/template/mẫu phiếu import khách hàng áp dụng.xls',
            "target": "_parent",
        }

    def action_import_line_pos_config(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise ValidationError(_(
                    "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            name_shop = self._get_name_shop_from_sheet(sheet)
            checked_name_shop = self.check_name_shop(name_shop)
            if not checked_name_shop:
                raise ValidationError(
                    _("Name shop not exist. Please check those again.\n {}").format(checked_name_shop))
            self._cr.execute(f"""DELETE FROM pos_config_pos_promotion_rel WHERE pos_promotion_id = '{self.id}'""")
            self._create_name_shop(name_shops=name_shop)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _create_name_shop(self, name_shops):
        for name in name_shops:
            shop_id = self.env['pos.config'].search([('name', '=', name)]).id
            if not shop_id:
                raise UserError(_('\nPos name does not exist in the system or have more space, name (%s)') % str(name))
            self._cr.execute(
                f"""INSERT INTO pos_config_pos_promotion_rel(pos_promotion_id,pos_config_id) VALUES ('{self.id}','{shop_id}')""")

    def _get_name_shop_from_sheet(self, sheet):
        index = 1
        name_shop = []
        while index < sheet.nrows:
            lot_name = sheet.cell(index, 0).value
            if lot_name not in name_shop:
                name_shop.append(lot_name)
            index = index + 1
        return name_shop

    def check_name_shop(self, name_shop):
        lots = []
        line_pos_config_not_exist_db = []
        self._cr.execute(f"""SELECT name FROM pos_config""")
        name_shops = self._cr.fetchall()
        for item in name_shops:
            lots.append(item[0])
        check = []
        data = []
        for name in name_shops:
            name_add = name[0].replace(' ', '')
            check.append(name_add)
        for name_data in name_shop:
            name_add_data = name_data.replace(' ', '')
            if name_add_data in check:
                data.append(name_add_data)
            else:
                line_pos_config_not_exist_db.append(name_shop.index(name_data) + 2)

        if line_pos_config_not_exist_db:
            line_pos_config_error = ' , '.join([str(line) for line in line_pos_config_not_exist_db])
            raise UserError(_('\nPos name does not exist in the system, line (%s)') % str(line_pos_config_error))
        if len(data) == len(name_shop):
            return True
        else:
            return False

    def action_import_line_partner(self):
        try:
            data = base64.decodebytes(self.field_binary_import_partner)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            phone_number = self._get_phone_number_from_sheet(sheet)
            checked_phone_number = self.check_phone_number(phone_number)
            if not checked_phone_number:
                raise ValidationError(
                    _("Customer shop not exist. Please check those again.\n {}").format(checked_phone_number))
            self._cr.execute(f"""DELETE FROM promotion_res_partner_group_rel WHERE pos_promotion_id = '{self.id}'""")
            self._create_res_partner(phone_numbers=phone_number)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_phone_number_from_sheet(self, sheet):
        try:
            index = 1
            phone_number = []
            while index < sheet.nrows:
                lot_name = sheet.cell(index, 1).value
                # if lot_name not in phone_number:
                phone_number.append(lot_name)
                index = index + 1
            return phone_number
        except ValueError:
            raise UserError(_("Phone in excel file not is number !"))

    # def check_phone_number(self, phone_number):
    #     try:
    #         lots = []
    #         checks = []
    #         line_phone_not_exist_db = []
    #         self._cr.execute(f"""SELECT phone FROM res_partner""")
    #         phone_numbers = self._cr.fetchall()
    #         for item in phone_numbers:
    #             lots.append(item[0])
    #         for phone in phone_number:
    #             phone_replace = str(phone).replace('.0', '')
    #             if phone_replace in lots:
    #                 checks.append(phone)
    #             else:
    #                 line_phone_not_exist_db.append(phone_number.index(phone) + 2)
    #         if len(checks) < len(phone_number):
    #             line_phone_error = ' , '.join([str(line) for line in line_phone_not_exist_db])
    #             raise UserError(_('\nPhone does not exist in the system, line (%s)') % str(line_phone_error))
    #             # return False
    #         return True
    #     except ValueError:
    #         raise UserError(_("Phone in excel file not is number !"))
    # def check_phone_number(self, phone_number):
    #     try:
    #         checks = []
    #         phone_not_exist_db = []
    #         line_phone_not_exist_db = []
    #         for phone in phone_number:
    #             phone_str = str(phone).replace('.0', '')
    #             self._cr.execute(f"""SELECT * FROM res_partner WHERE phone = '{phone_str}'""")
    #             phone_numbers = self._cr.fetchall()
    #             if not phone_numbers:
    #                 line_phone_not_exist_db.append(phone_number.index(phone) + 2)
    #
    #         if line_phone_not_exist_db:
    #             line_phone_error = ' , '.join([str(line) for line in line_phone_not_exist_db])
    #             raise UserError(_('\nPhone does not exist in the system, line (%s)') % str(line_phone_error))
    #         return True
    #     except ValueError:
    #         raise UserError(_("Phone in excel file not is number !"))

    def check_phone_number(self, phone_number):
        try:
            line_phone_not_exist_db = []
            arr_phone_in_db = []
            if len(phone_number) == 0:
                raise UserError(_("File excel not have phone number !"))
            self._cr.execute(f"""SELECT phone FROM res_partner WHERE phone IN {tuple(phone_number)}""")
            phone_numbers_test = self._cr.fetchall()
            for number in phone_numbers_test:
                arr_phone_in_db.append(number[0])
            for phone in phone_number:
                if phone not in arr_phone_in_db:
                    line_phone_not_exist_db.append(phone_number.index(phone) + 2)
            if line_phone_not_exist_db:
                line_phone_error = ' , '.join([str(line) for line in line_phone_not_exist_db])
                raise UserError(_('\nPhone does not exist in the system, line (%s)') % str(line_phone_error))
            return True
        except ValueError:
            raise UserError(_("Phone in excel file not is number !"))

    def _create_res_partner(self, phone_numbers):
        try:
            for phone in phone_numbers:
                phone_str = str(phone)
                try:
                    customer_id = self.env['res.partner'].search([('phone', '=', phone_str)], limit=1).id
                    if not customer_id:
                        raise UserError(_('\nPhone does not exist in the system, phone (%s)') % phone_str)
                    self._cr.execute(
                        f"""SELECT * FROM promotion_res_partner_group_rel WHERE pos_promotion_id = '{self.id}'""")
                    phone_number_in_db = self._cr.fetchall()
                    arr_res_in_db = []
                    for res in phone_number_in_db:
                        for re in res:
                            arr_res_in_db.append(re)
                    if customer_id in arr_res_in_db:
                        raise UserError(_("File excel same phone %s!", phone_str))
                except ValueError:
                    raise UserError(_("Customer in database have same phone %s!", phone_str))
                self._cr.execute(
                    f"""SELECT res_partner_id FROM res_partner_rel WHERE pos_promotion_id = '{self.id}' AND res_partner_id='{customer_id}' """)
                group_check_partner = self._cr.fetchall()
                if len(group_check_partner) == 0:
                    self._cr.execute(
                        f"""INSERT INTO promotion_res_partner_group_rel(pos_promotion_id,res_partner_id) VALUES ('{self.id}','{customer_id}')""")
                else:
                    raise UserError(_("Customer is existed in not res partner, phone %s!", phone_str))
        except ValueError:
            raise UserError(_("Phone in excel must start number 0 !"))

    def action_import_line_not_partner(self):
        try:
            data = base64.decodebytes(self.field_binary_import_not_partner)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            phone_number = self._get_phone_number_from_sheet(sheet)
            checked_phone_number = self.check_phone_number(phone_number)
            if not checked_phone_number:
                raise ValidationError(
                    _("Customer shop not exist. Please check those again.\n {}").format(checked_phone_number))
            self._cr.execute(f"""DELETE FROM res_partner_rel WHERE pos_promotion_id = {self.id}""")
            self._create_not_res_partner(phone_numbers=phone_number)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _create_not_res_partner(self, phone_numbers):
        try:
            for phone in phone_numbers:
                phone_str = str(phone)
                try:
                    customer_id = self.env['res.partner'].search([('phone', '=', phone_str)], limit=1).id
                    if not customer_id:
                        raise UserError(_('\nPhone does not exist in the system, phone (%s)') % phone_str)
                    self._cr.execute(
                        f"""SELECT * FROM res_partner_rel WHERE pos_promotion_id = {self.id}""")
                    phone_number_in_db = self._cr.fetchall()
                    arr_res_in_db = []
                    for res in phone_number_in_db:
                        for re in res:
                            arr_res_in_db.append(re)
                    if customer_id in arr_res_in_db:
                        raise UserError(_("File excel same phone %s!", phone_str))
                except ValueError:
                    raise UserError(_("Customer in database have same phone %s!", phone_str))
                self._cr.execute(
                    f"""SELECT res_partner_id FROM promotion_res_partner_group_rel WHERE pos_promotion_id = '{self.id}' AND res_partner_id='{customer_id}' """)
                group_check_partner = self._cr.fetchall()
                if len(group_check_partner) == 0:
                    self._cr.execute(
                        f"""INSERT INTO res_partner_rel(pos_promotion_id,res_partner_id) VALUES ('{self.id}','{customer_id}')""")
                else:
                    raise UserError(_("Customer is existed in res partner apply, phone %s!", phone_str))
        except ValueError:
            raise UserError(_("Phone in excel must start number 0 !"))
        # try:
        #     for phone in phone_numbers:
        #         phone_str = '0' + str(phone)
        #         customer_id = self.env['res.partner'].search([('phone', '=', phone_str)], limit=1).id
        #         self._cr.execute(
        #             f"""SELECT res_partner_id FROM pos_promotion_res_partner_rel WHERE pos_promotion_id = '{self.id}' """)
        #         res_partner_exist_apply = self._cr.fetchall()
        #         for resr_part in res_partner_exist_apply:
        #             if customer_id == resr_part[0]:
        #                 raise ValidationError(
        #                     _("Customer shop is existed in customer apply promotion. Please check those again.\n {}"))
        #         self._cr.execute(
        #             f"""INSERT INTO res_partner_rel(pos_promotion_id,res_partner_id) VALUES ('{self.id}','{customer_id}')""")
        # except ValueError:
        #     raise UserError(_("Phone in excel must start number 0 !"))

    def write(self, vals):

        vals = self.vals_factory(vals)
        # # calculate partner_ids in pos
        partner_ids = self.get_partner_ids(vals)
        partner_group = vals.get('partner_groups')
        partner_ids_get = vals.get('partner_ids')
        # if partner_ids:
        #     vals['partner_ids'] = [(6, 0, partner_ids.ids)]
        # # elif self.import_file is False or partner_group is None or partner_ids_get is None:
        # #     vals['partner_ids'] = [(5, 0, partner_ids.ids)]
        # elif partner_group is None and len(self.partner_ids) > 0 and partner_ids_get is None:
        #     vals['partner_ids'] = [(5, 0, partner_ids.ids)]
        arr_partner_apply = []
        for val in self.partner_ids_without_group:
            arr_partner_apply.append(val.id)
        values = vals.get('x_partner_not_ids')
        if values:
            values_x_partner_not_ids = values[0][2]
            for val in values_x_partner_not_ids:
                if val in arr_partner_apply:
                    raise ValidationError(
                        _("Customer shop is existed in customer apply promotion. Please check those again.\n"))
        arr_partner_not_apply = []
        for val in self.x_partner_not_ids:
            arr_partner_not_apply.append(val.id)
        values = vals.get('partner_ids_without_group')
        if values:
            values_partner_ids = values[0][2]
            for val in values_partner_ids:
                if val in arr_partner_not_apply:
                    raise ValidationError(
                        _("Customer shop is existed in customer not apply promotion. Please check those again.\n"))
        apply_and_not_apply_list = []
        name_list = []
        if 'partner_ids_without_group' in vals and 'x_partner_not_ids' in vals:
            for apply in vals['partner_ids_without_group'][0][2]:
                if apply in vals['x_partner_not_ids'][0][2] or apply in self.x_partner_not_ids.ids:
                    if apply not in apply_and_not_apply_list:
                        apply_and_not_apply_list.append(apply)
            for apply in vals['x_partner_not_ids'][0][2]:
                if apply in self.partner_ids_without_group.ids:
                    if apply not in apply_and_not_apply_list:
                        apply_and_not_apply_list.append(apply)
        if apply_and_not_apply_list:
            partner_ids = self.env['res.partner'].browse(apply_and_not_apply_list)
            for partner_id in partner_ids:
                name_list.append(partner_id.name)
            name = ','.join([str(name) for name in name_list])
            raise UserError(_('Have customer in list apply and list not apply together\n (%s)' %
                              name))
        return super(PosPromotion, self).write(vals)

    # @api.constrains('partner_groups')
    # def test(self):
    #     self.partner_ids = self.partner_groups.x_partner_ids

    # # chuyển partner từ nhóm KH không áp dụng
    # @api.constrains('partner_groups_not')
    # def add_partner_from_group_not_aply(self):
    #     # self.partner_ids_not = self.partner_groups_not.x_partner_ids

    def get_partner_ids(self, vals):
        # case 1: using partner group
        partner_groups_ids = self.get_partner_with_groups(vals)

        # case 2: using domain
        partner_domain_ids = self.get_partner_with_domain(vals)

        # Combine partner ids
        return partner_groups_ids | partner_domain_ids

    def get_partner_with_groups(self, vals):
        partner_group = []
        if 'partner_groups' in vals and vals.get('partner_groups'):
            partner_group = vals.get('partner_groups')[0][-1]
        elif self.partner_groups:
            partner_group = self.partner_groups.ids
        if not partner_group:
            return self.env['res.partner']
        partner_id = []
        for pn in partner_group:
            group = self.env['res.partner.group'].search([('id', '=', pn)])
            for partner in group.x_partner_ids:
                partner_id.append(partner.id)
        # self.partner_ids = self.env['res.partner'].search([('id', 'in', partner_id)])
        return self.env['res.partner'].search([('id', 'in', partner_id)])
        # return self.env['res.partner'].search([('partner_groups', 'in', partner_group)])

    def get_partner_with_domain(self, vals):
        domain = []
        if 'partner_domain' in vals and vals.get('partner_domain'):
            domain = eval(vals.get('partner_domain'))
        elif self.partner_domain:
            domain = eval(self.partner_domain)
        if not domain:
            return self.env['res.partner']
        return self.env['res.partner'].search(domain)

    def unlink(self):
        if self.state in ['active']:
            raise ValidationError(_('Can not delete promotion in state "Active"'))
        return super(PosPromotion, self).unlink()

    @staticmethod
    def vals_factory(vals):
        if 'name' in vals:
            vals.update({'name': vals.get('name').strip()})
        return vals

    def action_draft(self):
        for row in self:
            row.state = 'draft'

    def action_active(self):
        for row in self:
            row.state = 'active'

    def action_deactive(self):
        for row in self:
            row.state = 'inactive'

    def action_auto_deactive(self):
        active_promotion = self.env['pos.promotion'].search(
            [('state', 'in', ['active']), ('end_date', '<', fields.Date.today())])
        for promotion in active_promotion:
            promotion.action_deactive()

    def action_cancel(self):
        for row in self:
            row.state = 'cancel'

    @api.constrains('apply_all_pos_config', 'apply_manual_pos_config')
    def check_not_true_pos_config(self):
        if self.apply_all_pos_config == True and self.apply_manual_pos_config == True:
            raise UserError(_('Apply all pos config and manual not true!'))

    @api.constrains('apply_all_res_partner_apply', 'apply_manual_res_partner_apply')
    def check_not_true_res_partner(self):
        if self.apply_all_res_partner_apply == True and self.apply_manual_res_partner_apply == True:
            raise UserError(_('Apply all res partner and manual not true!'))

    @api.constrains('apply_all_res_partner_not_apply', 'apply_manual_res_partner_not_apply')
    def check_not_true_not_res_partner(self):
        if self.apply_all_res_partner_not_apply == True and self.apply_manual_res_partner_not_apply == True:
            raise UserError(_('Apply all not res partner and manual not true!'))

    @api.constrains('apply_all_res_partner_not_apply', 'apply_all_res_partner_apply')
    def check_not_true_not_all_res_partner(self):
        if self.apply_all_res_partner_not_apply == True and self.apply_all_res_partner_apply == True:
            raise UserError(_('Apply all res partner not apply and apply all test partner apply same true!'))
    # @api.onchange('apply_all_pos_config')
    # def on_change_apply_all_pos_config(self):
    #     if self.apply_all_pos_config:
    #         self.apply_manual_pos_config = False
    #     else:
    #         self.apply_manual_pos_config = True
    #
    # @api.onchange('apply_manual_pos_config')
    # def on_change_apply_manual_pos_config(self):
    #     if self.apply_manual_pos_config:
    #         self.apply_all_pos_config = False
    #     else:
    #         self.apply_all_pos_config = True
    #
    # # khách hàng áp dụng
    # @api.onchange('apply_all_res_partner_apply')
    # def on_change_apply_all_res_partner_apply(self):
    #     if self.apply_all_res_partner_apply:
    #         self.apply_manual_res_partner_apply = False
    #     else:
    #         self.apply_manual_res_partner_apply = True
    #
    # @api.onchange('apply_manual_res_partner_apply')
    # def on_change_apply_manual_res_partner_apply(self):
    #     if self.apply_manual_res_partner_apply:
    #         self.apply_all_res_partner_apply = False
    #     else:
    #         self.apply_all_res_partner_apply = True
    #
    # # khách hàng không áp dụng
    # @api.onchange('apply_all_res_partner_not_apply')
    # def on_change_apply_apply_all_res_partner_not_apply(self):
    #     if self.apply_all_res_partner_not_apply:
    #         self.apply_manual_res_partner_not_apply = False
    #     else:
    #         self.apply_manual_res_partner_not_apply = True
    #
    # @api.onchange('apply_manual_res_partner_not_apply')
    # def on_change_apply_manual_res_partner_not_apply(self):
    #     if self.apply_manual_res_partner_not_apply:
    #         self.apply_all_res_partner_not_apply = False
    #     else:
    #         self.apply_all_res_partner_not_apply = True
    # TODO HERE: upload from excel
    # def download_template(self):
    #     return {
    #         "type": "ir.actions.act_url",
    #         "url": '/ev_pos_promotion/static/template/mau_san_pham_ban_hang.xls',
    #         "target": "_parent",
    #     }
    #
    # def _check_format_excel(self, file_name):
    #     if file_name is False:
    #         return False
    #     if file_name.lower().endswith('.xls') is False and file_name.lower().endswith('.xlsx') is False:
    #         return False
    #     return True
    #
    # def action_import_line(self):
    #     try:
    #         if not self._check_format_excel(self.field_binary_name):
    #             raise ValidationError(
    #                 _("File not found or in incorrect format. Please check the .xls or .xlsx file format"))
    #         data = base64.decodebytes(self.field_binary_import)
    #         excel = xlrd.open_workbook(file_contents=data)
    #         sheet = excel.sheet_by_index(0)
    #         index = 1
    #         lines = []
    #
    #         while index < sheet.nrows:
    #
    #             index = index + 1
    #
    #         self.order_line = lines
    #         self.field_binary_import = None
    #         self.field_binary_name = None
    #
    #     except ValueError as e:
    #         raise osv.except_osv(_("Warning!"), (e))

    @api.onchange('type')
    def _onchange_type(self):
        pass
