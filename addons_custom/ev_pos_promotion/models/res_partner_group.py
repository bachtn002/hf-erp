# -*- coding: utf-8 -*-
import base64

import xlrd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv.osv import osv
from odoo.osv import osv
from odoo.exceptions import UserError


class ResPartnerGroup(models.Model):
    _name = 'res.partner.group'
    _inherit = ['mail.thread']
    _description = 'Res partner group'
    _order = 'name asc'

    name = fields.Char(string='Name', required=True)
    x_partner_ids = fields.Many2many('res.partner','res_partner_res_partner_group_rel', string=_("Partners"))
    import_file = fields.Boolean('Import file')
    field_binary_import_promotion_partner = fields.Binary(string="Field Binary Import")
    field_binary_name_promotion_partner = fields.Char(string="Field Binary Name")

    def download_template_res_partner_group(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion/static/template/mẫu phiếu import khách hàng áp dụng.xls',
            "target": "_parent",
        }

    def action_import_line_promotion_partner_group(self):
        try:
            data = base64.decodebytes(self.field_binary_import_promotion_partner)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            phone_number = self._get_phone_number_from_sheet(sheet)
            checked_phone_number = self.check_phone_number(phone_number)
            if not checked_phone_number:
                raise ValidationError(
                    _("Customer shop not exist. Please check those again.\n {}").format(checked_phone_number))
            self._cr.execute(
                f"""DELETE FROM res_partner_res_partner_group_rel WHERE res_partner_group_id='{self.id}'""")
            self._create_res_partner(phone_numbers=phone_number)
            self.import_file = None
            self.field_binary_import_promotion_partner = None

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_phone_number_from_sheet(self, sheet):
        try:
            index = 1
            phone_number = []
            phone_duplicate = []
            while index < sheet.nrows:
                lot_name = sheet.cell(index, 1).value
                lot_name = str(lot_name).split('.')[0]
                if lot_name in phone_number:
                    phone_duplicate.append(index + 1)
                else:
                    phone_number.append(lot_name)
                index = index + 1
            if phone_duplicate:
                line_phone_duplicate = ' , '.join([str(line) for line in phone_duplicate])
                raise UserError(_("Phone in excel file is duplicate! line: (%s)") % str(line_phone_duplicate))
            return phone_number
        except ValueError:
            raise UserError(_("Phone in excel file not is number !"))

    # def check_phone_number(self, phone_number):
    #     try:
    #         checks = []
    #         phone_not_exist_db = []
    #         line_phone_not_exist_db = []
    #         for phone in phone_number:
    #             phone_str = str(phone)
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
                count_number_excel = phone_numbers.count(phone)
                if count_number_excel > 1:
                    raise UserError(_("File excel same phone %s!", phone))
            for phone in phone_numbers:
                phone_str = str(phone)
                try:
                    customer_id = self.env['res.partner'].search([('phone', '=', phone_str)], limit=1).id
                    if not customer_id:
                        raise UserError(_('\nPhone does not exist in the system, phone (%s)') % phone_str)
                except ValueError:
                    raise UserError(_("Customer in database have same phone %s!", phone_str))
                self._cr.execute(
                    f"""INSERT INTO res_partner_res_partner_group_rel(res_partner_group_id,res_partner_id) VALUES ('{self.id}','{customer_id}')""")
                # self._cr.execute(
                #     f"""SELECT * FROM res_partner_res_partner_group_rel WHERE res_partner_id = '{customer_id}'""")
                # group_check_partner = self._cr.fetchall()
                # if len(group_check_partner) == 0:
                #     self._cr.execute(
                #         f"""INSERT INTO res_partner_res_partner_group_rel(res_partner_group_id,res_partner_id) VALUES ('{self.id}','{customer_id}')""")
                # else:
                #     raise UserError(_("File excel same phone %s!", phone_str))
        except ValueError:
            raise UserError(_("Phone in excel must start number 0 !"))

    @api.model
    def create(self, vals):
        """Inherit method create.

        :param vals: dict - create data
        :return res.partner.group object
        """
        # vals = self.vals_factory(vals)
        # for value in vals['x_partner_ids']:
        #     for partner_id in value[2]:
        #         print(partner_id)
        return super(ResPartnerGroup, self).create(vals)

    def write(self, vals):
        """Inherit method write.

        :param vals:
        :returns bool
        """
        # vals = self.vals_factory(vals)
        return super(ResPartnerGroup, self).write(vals)

    # @staticmethod
    # def vals_factory(vals):
    #     """Rebuild params(vals) of create or write method used
    #     + Remove space before/after of field name.
    #     :param vals:
    #     :returns vals:
    #     """
    #     vals.update({'name': vals.get('name')})
    #     return vals
    def unlink(self):
        for rc in self:
            self._cr.execute(
                f"""SELECT pos_promotion_id FROM pos_promotion_res_partner_group_rel WHERE res_partner_group_id = {rc.id}""")
            pos_promotions = self._cr.fetchall()
            for pos_promotion in pos_promotions:
                promotion_record = self.env['pos.promotion'].search([('id', '=', pos_promotion[0]),
                                                                    ('state', '=', 'active')])
                if promotion_record:
                    raise UserError(_("You cannot delete record if the promotion (%s) is 'Active'") % str(promotion_record.name))
        return super(ResPartnerGroup, self).unlink()

    @api.constrains('x_partner_ids')
    def add_partner_to_group(self):
        for partner in self.x_partner_ids:
            partner.partner_groups = self

        # xử lý khách hàng thêm ở CTKM
        self._cr.execute(
            f"""SELECT pos_promotion_id FROM pos_promotion_res_partner_group_rel where res_partner_group_id = {self.id}""")
        promotion_with_self_groups = self._cr.fetchall()
        for promotion_with_self_group in promotion_with_self_groups:
            sql_line = """
                        DELETE FROM pos_promotion_res_partner_rel
                        WHERE pos_promotion_id = %d;
                        """
            self._cr.execute(sql_line % (promotion_with_self_group[0]))
            for pn in self.x_partner_ids:
                self._cr.execute(
                    f"""INSERT INTO pos_promotion_res_partner_rel(pos_promotion_id,res_partner_id)
                    VALUES ('{promotion_with_self_group[0]}','{pn.id}')""")

            # insert khách hàng ở nhóm KH khác self
            self._cr.execute(
                f"""SELECT res_partner_group_id FROM pos_promotion_res_partner_group_rel where pos_promotion_id = {promotion_with_self_group[0]}""")
            groups = self._cr.fetchall()
            groups_without_self = []
            for gr in groups:
                if gr[0] != self.id:
                    groups_without_self.append(gr[0])
            for gr in groups_without_self:
                group = self.env['res.partner.group'].search([('id', '=', gr)])
                for pn in group.x_partner_ids:
                    self._cr.execute(
                        f"""INSERT INTO pos_promotion_res_partner_rel(pos_promotion_id,res_partner_id)
                        VALUES ('{promotion_with_self_group[0]}','{pn.id}')""")
