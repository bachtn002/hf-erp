from odoo import fields, models


class CustomWeekdays(models.Model):
    _name = 'custom.weekdays'
    name = fields.Char(string='Thứ')
    code = fields.Integer(string='Code')

    def get_custom_week(self, id):
        query = f"""
                    select * from custom_weekdays_pos_promotion_rel where pos_promotion_id = {id}
                """
        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()
        return data
