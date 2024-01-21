# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class PosConfigOnline(models.Model):
    _inherit = 'pos.config'

    x_limit_partner = fields.Integer('Number of Customer downloaded', default=50)


class ResPartnerOnline(models.Model):
    _inherit = 'res.partner'


    @api.model
    def check_phone(self, data):
        if 'phone' not in data:
            return 'Số điện thoại bắt buộc nhập'
        phone = data['phone'].strip()
        if len(phone) > 15:
            return 'Số điện toại không được lớn hơn 15 ký tự'
        if len(phone) == 0:
            return 'Số điện thoại bắt buộc nhập'
        if phone.isdigit() is False:
            return 'Số điện thoại phải là số'
        query = """
                    SELECT
                        id
                    FROM res_partner WHERE active = true and phone = '%s'
                """ % (phone)
        self._cr.execute(query)
        fetched_data = self._cr.dictfetchall()
        if len(fetched_data) > 0:
            return 'Số điện thoại đã tồn tại trên hệ thống.'
        return True


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if limit == None:
            context = self.env.context
            if 'limit_partner' in context:
                limit = context['limit_partner']
                if limit == 0:
                    return []
        return super(ResPartnerOnline, self).search_read(domain, fields, offset, limit, order)


    @api.model
    def search_partner_by_phone(self, phone, fields=None, offset=0, limit=1, order=None):
        if fields == None:
            return []
        if 'barcode' in fields:
            fields.remove('barcode')
        if 'property_account_position_id' in fields:
            fields.remove('property_account_position_id')

        if 'property_product_pricelist' in fields:
            fields.remove('property_product_pricelist')
        if 'loyalty_points' in fields:
            fields.remove('loyalty_points')

        if 'partner_groups' in fields:
            fields.remove('partner_groups')

        listFields = ','.join([str(elem) for elem in fields])

        query = """
            SELECT
                id,
                %s,
                '' as barcode,
                false property_account_position_id,
                false property_product_pricelist,
                ARRAY(SELECT res_partner_group_id FROM res_partner_res_partner_group_rel WHERE res_partner_id = res_partner.id) as partner_groups,
                (SELECT value_float FROM ir_property WHERE name = 'loyalty_points' and res_id = concat('res.partner,', res_partner.id) LIMIT 1) loyalty_points
            FROM res_partner WHERE active = true and phone = '%s' LIMIT %s
        """ % (listFields,phone,limit)
        # query = """
        #             SELECT
        #                 id,
        #                 %s,
        #                 '' as barcode,
        #                 false property_account_position_id,
        #                 false property_product_pricelist,
        #                 0 loyalty_points
        #             FROM res_partner WHERE active = true and phone like '%s%%' LIMIT %s
        #         """ % (listFields, phone, limit)

        self._cr.execute(query)
        fetched_data = self._cr.dictfetchall()
        return fetched_data

    @api.model
    def search_partner_by_id(self, id, fields=None, offset=0, limit=5, order=None):
        if fields == None:
            return []
        if 'barcode' in fields:
            fields.remove('barcode')
        if 'property_account_position_id' in fields:
            fields.remove('property_account_position_id')

        if 'property_product_pricelist' in fields:
            fields.remove('property_product_pricelist')
        if 'loyalty_points' in fields:
            fields.remove('loyalty_points')

        if 'partner_groups' in fields:
            fields.remove('partner_groups')

        listFields = ','.join([str(elem) for elem in fields])

        query = """
                SELECT 
                    id,
                    %s,
                    '' as barcode,
                    false property_account_position_id,
                    false property_product_pricelist,
                    ARRAY(SELECT res_partner_group_id FROM res_partner_res_partner_group_rel WHERE res_partner_id = res_partner.id) as partner_groups,
                    (SELECT value_float FROM ir_property WHERE name = 'loyalty_points' and res_id = concat('res.partner,', res_partner.id) LIMIT 1) loyalty_points
                FROM res_partner WHERE active = true and id = %s LIMIT %s
            """ % (listFields, id, limit)

        self._cr.execute(query)
        fetched_data = self._cr.dictfetchall()
        return fetched_data

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # # image is a dataurl, get the data after the comma
        # if partner.get('image_1920'):
        #     partner['image_1920'] = partner['image_1920'].split(',')[1]
        # partner_id = partner.pop('id', False)
        # if partner_id:  # Modifying existing partner
        #     self.browse(partner_id).write(partner)
        # else:
        #     partner_id = self.create(partner).id

        if partner.get('image_1920'):
            partner['image_1920'] = partner['image_1920'].split(',')[1]
        partner_id = partner.pop('id', False)
        if partner_id:
            super(ResPartnerOnline, self).create_from_ui(partner)
        else:
            partner_result = self.search([('name','=', partner['name']),('phone','=', partner['phone'])], limit=1)
            if partner_result.id != False:
                partner_id = partner_result.id
            else:
                partner_id = super(ResPartnerOnline, self).create_from_ui(partner)
        return partner_id

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        # product_combo_child = []
        # product_loads = []
        # product_voucher_loads = []
        # if limit == None:
        #     context = self.env.context
        #     if 'limit_product' in context:
        #         product_ids = []
        #         product_combo_ids = []
        #         limit = context['limit_product']
        #         today = date.today()
        #         prod_promotion_ids = self.env['pos.promotion'].search(
        #             [('state', '=', 'active'), ('end_date', '>=', today), ('start_date', '<=', today)])
        #         for pro_promotion in prod_promotion_ids:
        #             if pro_promotion.product_id.id != False:
        #                 product_ids.append(pro_promotion.product_id.id)
        #         prod_loyalty_ids = self.env['loyalty.program'].search([('product_id', '!=', False)])
        #         for prod_loyalty_id in prod_loyalty_ids:
        #             if prod_loyalty_id.product_id.id != False:
        #                 product_ids.append(prod_loyalty_id.product_id.id)
        #         product_ids = list(set(product_ids))
        #         product_loads = self.search_read(
        #             [('id', 'in', product_ids), ('sale_ok', '=', True), ('available_in_pos', '=', True)], fields,
        #             offset, 80, order)
        #         product_voucher_loads = self.search_read(
        #             [('x_is_voucher', '=', True), ('sale_ok', '=', True), ('available_in_pos', '=', True)], fields,
        #             offset, 80, order)
        #         product_combo_loads = self.search_read(
        #             [('x_is_combo', '=', True), ('sale_ok', '=', True), ('available_in_pos', '=', True)], fields,
        #             offset, 80, order)
        #         for item in product_combo_loads:
        #             for it in item.get('x_product_combo_ids'):
        #                 combo_product = self.env['product.combo'].search([('id', '=', it)])
        #                 product_combo_ids.append(combo_product.product_ids.id)
        #         product_combo_ids = list(set(product_combo_ids))
        #         combo = self.search_read(
        #             [('id', 'in', product_combo_ids), ('sale_ok', '=', True),
        #              ('available_in_pos', '=', True)],
        #             fields, offset, 80, order)
        #         # for item in product_combo_loads:
        #         #     for it in item.get('x_product_combo_ids'):
        #         #         combo_product = self.env['product.combo'].search([('id', '=', it)])
        #         #         combo = self.search_read(
        #         #             [('id', '=', combo_product.product_ids.id), ('sale_ok', '=', True), ('available_in_pos', '=', True)],
        #         #             fields, offset, 80, order)
        #         #         product_combo_child.extend(combo)
        #         if limit == 0:
        #             return []
        # if len(product_loads) > 0 or len(product_voucher_loads) > 0:
        #     results = super(ProductProductInherit, self).search_read(domain, fields, offset, limit, order)
        #     # results = results + product_loads + product_voucher_loads + product_combo_child
        #     results = results + product_loads + product_voucher_loads + combo
        #     return results
        if limit == None:
            context = self.env.context
            if 'limit_product' in context:
                if 'qty_available' in fields:
                    fields.remove('qty_available')
        return super(ProductProductInherit, self).search_read(domain, fields, offset, limit, order)
