from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_product_lot_rule = fields.Many2one('product.lot.rule','Product Lot Rule', default = None)

    # Check quyền sửa mã nội bộ
    @api.onchange('default_code')
    def _check_group_write_default_code(self):
        # Bỏ check group khi tạo mới sản phẩm
        if self.default_code != False:
            if not self.env.user.has_group('ev_product_lot_rule.group_edit_defaut_code'):
                # self.default_code = self._origin.default_code
                raise UserError(_('You do not have permission to edit this default code'))
        
    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if vals.get('x_is_voucher') == True or vals.get('x_is_blank_card') == True:
            return res
        else:
            rule_id = vals.get('x_product_lot_rule')
            lot_rule_id = self.env['product.lot.rule'].search([('id','=',rule_id)], limit=1)
            code = lot_rule_id.action_generate_product_code()
            res.default_code = code       
            return res
            
    def write(self, vals):
        if vals.get('x_is_voucher') == True or vals.get('x_is_blank_card') == True:
            return super().write(vals)
        else:
            default_code_old = self.default_code
            rule_id = self.x_product_lot_rule
            rule_id_id = rule_id.id
            # rule_id_id 
            # Check quyền chọn lại quy tắc khi sửa danh mục sản phẩm
            if vals.get('x_product_lot_rule') != self.x_product_lot_rule and vals.get('x_product_lot_rule') != None:
                if not self.env.user.has_group('ev_product_lot_rule.group_edit_defaut_code'):
                    raise UserError(_('You do not have permission to edit this product lot rule again'))
            # Check bỏ trống mã nội bộ
            if vals.get('default_code') == False:
                vals['default_code'] = default_code_old

            # Nếu không thay đổi quy tắc, cập nhật mã nội bộ sửa
                            # if rule_present == None:
            if vals.get('default_code') != default_code_old and vals.get('default_code') != None:
                vals['default_code'] = vals.get('default_code')
                # Xử lý và lấy MAX VALUE từ default_code tự sửa nếu có:
                max_old_rule = self.x_product_lot_rule.max_value_from_default_code
                max_current = vals.get('default_code')

            # ------------------------------
                # Check sửa mã nội bộ theo quy tắc
                # rule_len = self.x_product_lot_rule.rule_len
                # vals_get_rule = vals.get('x_product_lot_rule')
                # if not vals_get_rule:
                #     if len(max_current) != rule_len:
                #         raise UserError(_('Length of default code {} is not equal length of this rule {}').format(len(max_current), rule_len))
                # else:
                #     lot_rule_id = self.env['product.lot.rule'].search([('id','=',vals_get_rule)], limit=1)
                #     if len(max_current) != lot_rule_id.rule_len:
                #         raise UserError(_('Length of default code {} is not equal length of this rule {}').format(len(max_current), lot_rule_id.rule_len))
            # ------------------------------
                
                rule_len = self.x_product_lot_rule.rule_len
                vals_get_rule = vals.get('x_product_lot_rule')
                check_max_value = False
                # print('not vals_get_rule','current: ', len(max_current), 'rule len ', rule_len)

                if not vals_get_rule:
                    if len(max_current) == rule_len:
                        check_max_value = True
                        vals_get_rule = self.x_product_lot_rule.id
                else:
                    print('else 1')
                    lot_rule_id = self.env['product.lot.rule'].search([('id','=',vals_get_rule)], limit=1)
                    rule_id_id = vals_get_rule
                    max_old_rule = lot_rule_id.max_value_from_default_code
                    # print(len(max_current) ,'and ',lot_rule_id.rule_len)
                    if len(max_current) == lot_rule_id.rule_len:
                        check_max_value = True
                        
                # Nếu len(default code sửa) = len(quy tắc), Lấy theo max value 
                if check_max_value == True:
                    print(' value max:', check_max_value)
                    rule_line_ids = self.env['product.lot.rule.line'].search([('product_lot_rule_id', '=', rule_id_id)], order='type')
                    # Nếu quy tắc là Tự tăng
                    if len(rule_line_ids.ids) == 1:
                        print('if 2:')
                        if rule_line_ids.type == 'increment':
                            # print(max_current)
                            max_current = int(max_current)
                            # print(max_current)
                            # print(max_old_rule)
                            if max_current > max_old_rule:
                                lot_rule_id = self.env['product.lot.rule'].search([('id','=',vals_get_rule)], limit=1)
                                lot_rule_id.max_value_from_default_code = max_current
                                # self.x_product_lot_rule.max_value_from_default_code = max_current
                    else:
                        print('else 2:')
                        fix_value = (rule_line_ids[0].fix_value)
                        print(max_current)
                        max_current_incre = int(max_current[len(fix_value):])
                        fix_current = max_current[:len(fix_value)]
                        print('fix current',fix_current,'fix value: ', fix_value)
                        print(max_current_incre)
                        print(max_old_rule)
                        if max_current_incre > max_old_rule and fix_current == fix_value:
                            lot_rule_id = self.env['product.lot.rule'].search([('id','=',vals_get_rule)], limit=1)
                            lot_rule_id.max_value_from_default_code = max_current_incre
                            # self.x_product_lot_rule.max_value_from_default_code = max_current_incre

                # Nếu len(max current) != len(rule), sửa tự do
                else:
                    vals['default_code'] = max_current

            # else:
            # # Nếu chọn quy tắc mới, sinh ra mã nội bộ mới
            #     # print('create save')
            #     code = self.x_product_lot_rule.action_generate_product_code(rule_present)
            #     vals['default_code'] = code
            #     # print('code gen: ', code)
            return super().write(vals)
    
