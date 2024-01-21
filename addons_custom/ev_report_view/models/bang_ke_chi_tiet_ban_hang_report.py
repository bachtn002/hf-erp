import pytz
from datetime import datetime
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import odoo.tools as tools


class SaleDetailReport(models.TransientModel):
    _name = 'sale.details.report'
    _description = 'Bang ke chi tiet ban hang'

    pos_shop_id = fields.Char('Shop ID')
    pos_shop_code = fields.Char('Shop Code')
    pos_name = fields.Char('Shop name')
    # pos_order_id = fields.Many2one('pos.order', 'Order ID')
    order_name = fields.Char('Order name')
    date_order = fields.Datetime('Date order')
    customer = fields.Char('Customer')
    default_code = fields.Char('Default code')
    full_product_name = fields.Char('Full Product Name')
    unit = fields.Char('Unit')
    category_name = fields.Char('Category name')
    qty = fields.Float('Quantiy')
    price_unit = fields.Float('Price Unit', digits=(14, 0))
    vat = fields.Float('VAT')
    price_promotion = fields.Float('Price Promotion', digits=(14, 0))
    amount_promotion = fields.Float('Amount Promotion', digits=(14, 0))
    discount = fields.Float('Discount')
    product_promotion = fields.Char('Promotion name')
    user_name = fields.Char('User name')
    report_id = fields.Char('Report ID')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_sale_details_report')
        self.env.cr.execute("""CREATE OR REPLACE VIEW v_sale_details_report AS
        SELECT 
            ps.id AS pos_shop_id,
            ps.code AS pos_shop_code, 
            ps.name AS pos_name, 
            po.name AS order_name, 
            to_char(po.date_order + INTERVAL '7 hours', 'dd/mm/yyyy') AS date_order,
            rp.name AS customer,
            pp.default_code AS default_code,
            pol.full_product_name AS full_product_name, 
            uu.name AS unit, 
            pc.name AS category_name, 
            pol.qty AS qty, 
            pol.price_unit AS price_unit, 
            at.amount / 100 AS vat, 
            pol.x_is_price_promotion AS price_promotion,
            pol.amount_promotion_loyalty + pol.amount_promotion_total AS amount_promotion, 
            pol.discount AS discount, 
            pol.x_product_promotion AS product_promotion, 
            rpt.name AS user_name   
        FROM pos_order_line pol
            left join pos_order po ON pol.order_id = po.id
            left join account_tax_pos_order_line_rel atpolr ON pol.id = atpolr.pos_order_line_id
            left join pos_shop ps ON po.x_pos_shop_id = ps.id
            left join res_partner rp ON po.partner_id = rp.id
            left join product_product pp ON pol.product_id = pp.id
            left join product_template pt ON pp.product_tmpl_id = pt.id
            join uom_uom uu ON uu.id = pt.uom_id
            join product_taxes_rel ptr ON ptr.prod_id = pt.id
            left join account_tax at ON ptr.tax_id = at.id
            left join product_category pc ON pt.categ_id = pc.id
            left join res_users ru ON po.user_id = ru.id
            left join res_partner rpt ON ru.partner_id = rpt.id
            left join pos_promotion pprt ON pol.promotion_id = pprt.id
        WHERE pol.price_unit >= 0 AND pol.is_combo_line = False
        """)


def format_properties_generate(format_update={}):
    format_properties = {'bold': True, 'border': 1, 'font_size': '11', 'font_color': 'black',
                         'align': 'center', 'text_wrap': True, 'valign': 'vcenter',
                         'font_name': 'SVN-Nissan Brand Light'}
    if format_update:
        format_properties.update(format_update)
    return format_properties


class SaleDetailReportWizard(models.TransientModel):
    _name = 'report.sale.detail.report.wizard'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Bảng kê chi tiết bán hàng'

    from_date = fields.Date('From Date', default=lambda self: fields.Date.context_today(self))
    to_date = fields.Date('To Date', default=lambda self: fields.Date.context_today(self))

    def create_report(self):
        self.ensure_one()
        pos_shop_ids = self.env.user.x_pos_shop_ids
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = self.from_date

        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User does not have access pos shop'))

        sql = """     
        INSERT INTO sale_details_report ( pos_shop_code, pos_name, order_name, date_order, customer, default_code, full_product_name, unit, category_name,
        qty, price_unit, vat, price_promotion, amount_promotion, discount, product_promotion, user_name, 
        report_id, create_date , write_date, create_uid , write_uid )
        SELECT pos_shop_code, pos_name, order_name, to_date(date_order,'dd/mm/yyyy'), customer, default_code, full_product_name, unit, category_name,
        qty, price_unit, vat, price_promotion, amount_promotion, discount, product_promotion, user_name, 
        %s as report_id, now(), now(), %d, %d
        FROM v_sale_details_report 
        WHERE (pos_shop_id = ANY (string_to_array('%s', ',')::integer[])
            or '%s' = '0')
            AND to_date(date_order, 'dd/mm/yyyy') + INTERVAL '7 hours' >= to_date('%s', 'dd/mm/yyyy')
            AND to_date(date_order, 'dd/mm/yyyy')  + INTERVAL '7 hours' <= to_date('%s', 'dd/mm/yyyy')
        ORDER BY date_order
        """
        self.env.cr.execute(
            sql % (report_id, self.env.user.id, self.env.user.id, pos_shop_ids, pos_shop_ids, from_date, to_date))
        self.env.cr.commit()
        action = self.env['ir.actions.act_window']._for_xml_id('ev_report_view.sale_detail_report_action')
        print(action)
        action['domain'] = [('report_id', '=', report_id)]
        return action

    def action_print_excel(self):
        if self.from_date > self.to_date:
            raise UserError(_('Start date must be less than end date'))
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/xlsx/sale.detail.report.wizard/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def generate_xlsx_report(self, workbook, data, record):
        workbook.formats[0].font_name = 'Arial'
        header_yellow = workbook.add_format(format_properties_generate({'bg_color': 'yellow'}))
        header_green = workbook.add_format(format_properties_generate({'bg_color': 'green'}))

        no_bold = workbook.add_format({'bold': False, 'text_wrap': True, 'border': 1})
        date_format = workbook.add_format(
            {'bold': False, 'border': 1, 'text_wrap': True, 'num_format': 'dd-mm-yyyy HH:mm'})
        date_format_filter = workbook.add_format(
            {'bold': False, 'border': 1, 'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
        ws = workbook.add_worksheet("Sheet1")
        ws.set_column(0, 0, 5)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 30)
        ws.set_column(3, 3, 40)
        ws.set_column(4, 4, 20)
        ws.set_column(5, 4, 20)
        ws.set_column(6, 4, 20)
        ws.set_column(7, 4, 30)
        ws.set_column(8, 4, 20)
        ws.set_column(9, 4, 20)
        ws.set_column(10, 4, 20)
        ws.set_column(11, 4, 20)
        ws.set_column(12, 4, 20)
        ws.set_column(13, 4, 20)
        ws.set_column(14, 4, 20)
        ws.set_column(15, 4, 20)
        ws.set_column(16, 4, 40)
        ws.set_column(17, 4, 30)

        ws.write(0, 1, u"Từ ngày", no_bold)
        ws.write(0, 3, u"Đến ngày", no_bold)
        ws.write(0, 2, record.from_date, date_format_filter)
        ws.write(0, 4, record.to_date, date_format_filter)

        ws.write(2, 0, u"STT", header_yellow)
        ws.write(2, 1, u"Mã cửa hàng", header_yellow)
        ws.write(2, 2, u"Tên cửa hàng", header_yellow)
        ws.write(2, 3, u"Đơn hàng", header_yellow)
        ws.write(2, 4, u"Ngày tạo", header_yellow)
        ws.write(2, 5, u"Khách hàng", header_yellow)
        ws.write(2, 6, u"Mã sản phẩm", header_yellow)
        ws.write(2, 7, u"Tên sản phẩm", header_yellow)
        ws.write(2, 8, u"Đơn vị", header_yellow)
        ws.write(2, 9, u"Danh mục", header_yellow)
        ws.write(2, 10, u"Số lượng", header_yellow)
        ws.write(2, 11, u"Price Unit", header_yellow)
        ws.write(2, 12, u"VAT", header_yellow)
        ws.write(2, 13, u"Khuyến mãi", header_yellow)
        ws.write(2, 14, u"Discount", header_yellow)
        ws.write(2, 15, u"Chiết khấu", header_yellow)
        ws.write(2, 16, u"CTKM", header_yellow)
        ws.write(2, 17, u"Nhân viên", header_yellow)

        result = record.get_data()
        index = 3
        stt = 0
        local_tz = pytz.timezone('Asia/Bangkok')
        for item in result:
            ws.set_row(index, cell_format=no_bold)
            ws.write(index, 0, stt + 1)
            ws.write(index, 1, item.get('pos_shop_code'))
            ws.write(index, 2, item.get('pos_name'))
            ws.write(index, 3, item.get('order_name'))
            ws.write(index, 4, item.get('to_date'), date_format_filter)
            ws.write(index, 5, item.get('customer'))
            ws.write(index, 6, item.get('default_code'))
            ws.write(index, 7, item.get('full_product_name'))
            ws.write(index, 8, item.get('unit'))
            ws.write(index, 9, item.get('category_name'))
            ws.write(index, 10, item.get('qty'))
            ws.write(index, 11, item.get('price_unit'))
            ws.write(index, 12, item.get('vat'))
            ws.write(index, 13, item.get('price_promotion'))
            ws.write(index, 14, item.get('amount_promotion'))
            ws.write(index, 15, item.get('discount'))
            ws.write(index, 16, item.get('product_promotion'))
            ws.write(index, 17, item.get('user_name'))

            index += 1
            stt += 1

    def get_data(self):
        self.ensure_one()
        pos_shop_ids = self.env.user.x_pos_shop_ids
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = self.from_date

        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'
        if self.env.user.x_view_all_shop:
            pos_shop_ids = '0'
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User does not have access pos shop'))
        sql = """
                SELECT pos_shop_code, pos_name, order_name, to_date(date_order,'dd/mm/yyyy'), customer, default_code, full_product_name, unit, category_name,
                qty, price_unit, vat, price_promotion, amount_promotion, discount, product_promotion, user_name, 
                %s as report_id, now(), now(), %d, %d
                FROM v_sale_details_report 
                WHERE (pos_shop_id = ANY (string_to_array('%s', ',')::integer[])
                    or '%s' = '0')
                    AND to_date(date_order, 'dd/mm/yyyy') + INTERVAL '7 hours' >= to_date('%s', 'dd/mm/yyyy')
                    AND to_date(date_order, 'dd/mm/yyyy')  + INTERVAL '7 hours' <= to_date('%s', 'dd/mm/yyyy')
                ORDER BY date_order
                """
        self._cr.execute(
            sql % (report_id, self.env.user.id, self.env.user.id, pos_shop_ids, pos_shop_ids, from_date, to_date))
        query_res = self._cr.dictfetchall()
        return query_res
