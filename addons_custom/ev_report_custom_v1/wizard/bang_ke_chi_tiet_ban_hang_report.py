from odoo import fields, models, _
import pandas as pd

class BangKeChiTietBanHangReport(models.TransientModel):
    _name = "bang.ke.chi.tiet.ban.hang.report"
    _inherit = "report.base"
    _auto = True
    _description = "Bang Ke Chi Tiet Ban Hang"

    from_date = fields.Date()
    to_date = fields.Date()

    def _get_default_template_view_external_id(self):
        return 'ev_report_custom_v1.bang_ke_chi_tiet_ban_hang_data'

    def _get_report_json(self):
        params = self.copy_data()[0]
        data = self.env['bang.ke.chi.tiet.ban.hang.store'].get_data(**params)
        return data

    def get_download_file_name(self):
        return _('bang_ke_chi_tiet_ban_hang.xlsx')

    def _build_report_pandas_table(self, data):
        df = pd.json_normalize(data)
        #tạo 1 df mới 2 cột 'order_name', 'tongthanhtoan' : tổng của 'doanhthuthuc' group theo cột 'order_name'
        df_sum = df.groupby('order_name').agg({'doanhthuthuc': 'sum'})
        new_rows = df_sum.reset_index().rename(columns={'doanhthuthuc': 'tongthanhtoan'})

        #merge bảng cũ và bảng tổng vừa tạo
        df = pd.concat([new_rows, df])[list(df.columns)]
        # merged_df = df.groupby('order_name').apply(
        #     lambda x: x.reset_index(drop=True))
        df = df.sort_values(by=['order_name', 'tongthanhtoan'], ascending=[True, True]).reset_index(drop=True)
        return df.fillna('')

    def _columns_name(self):
        return {
            '.no': _('STT'),
            'code_shop': 'Mã cửa hàng',
            'shop_name': 'Tên cửa hàng',
            'order_name': 'Số chứng từ',
            'date_order': 'Ngày chứng từ',
            'partner': 'Mã khách',
            'customer': 'Tên khách',
            'default_code': 'Mã hàng',
            'full_product_name': 'Tên hàng',
            'dvt': 'Đơn vị tính',
            'category_name': 'Nhóm hàng',
            'qty': 'Số lượng',
            'price_unit': 'Đơn giá bán',
            'tienvat': 'Thành tiền có VAT',
            'khuyenmai': 'Km theo mặt hàng',
            'discount': 'Km phân bổ',
            'doanhthuthuc': 'Doanh thu thực(sau chiết khấu)',
            'tt_chua_vat': 'Thành tiền chưa VAT',
            'tienvatthuc': 'VAT',
            'dd_chua_vat': 'Đơn giá chưa VAT sau chiết khấu',
            'tongthanhtoan': 'Tổng tiền thanh toán',
            'promotion_name': 'Chương trình CTKM(chiến dịch)',
            'user_name': 'User thực hiện',
        }

    def _header_merge(self):
        return [['0:0', '0:0', '.no']]

    def action_report(self):
        return super(BangKeChiTietBanHangReport, self.with_context(renew=True)).action_report()

    def _align_with_data_type(self, df, soup):
        tbody = soup.find('tbody')
        trs = tbody.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            for i in range(10, 20):
                # từ cột qty -> tongthanhtoan
                tds[i]['style'] = tds[i].get('style', []) + [';text-align: right']
