from odoo import models, _


class PromotionCodePhoneReport(models.AbstractModel):
    _name = 'report.promotion.code.phone'
    _description = "Promotion Code PhoneReport"
    _inherit = 'report.report_xlsx.abstract'

    def get_selection_label(self, field_value):
        return _(dict(self.env['phone.promotion.list'].fields_get(allfields=['state'])['state']['selection'])[field_value])

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
            format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': False})
            format7 = workbook.add_format(
                {'num_format': 'DD-MM-YYYY', 'font_size': 10, 'align': 'center', 'bold': False})
            sheet = workbook.add_worksheet('Promotion Code')
            sheet.set_column(0, 2, 15)
            sheet.write('A1', 'Mã:', format1)
            sheet.write('B1', 'Số điện thoại', format1)
            sheet.write('C1', 'Trạng thái sử dụng', format1)
            row_num = 2
            for promotion_line in obj.x_phone_promotion_list_ids:
                sheet.write('A' + str(row_num), promotion_line.promotion_code, format2)
                sheet.write('B' + str(row_num), promotion_line.phone, format7)
                sheet.write('C' + str(row_num), self.get_selection_label(promotion_line.state), format7)
                row_num += 1
