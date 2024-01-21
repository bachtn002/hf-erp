# -*- coding: utf-8 -*-
import copy
import json
import pandas as pd
import numpy as np
import tempfile
import base64
import math
from bs4 import BeautifulSoup

from odoo import models, fields, _
from odoo.exceptions import ValidationError

from odoo.addons.ev_report.ev_xlsx_writer import to_excel

DATA_NOT_FOUND_HTML = '''
    <h2 class="alert alert-danger text-center" role="alert">
        DATA NOT FOUND
    </h2>
'''
CSS_HIGHLIGHT = 'background-color: #eeeeee;color: #000000;font-weight: bold;'


def _money_format(num):
    _s = '' if num >= 0 else '-'
    num = abs(num)
    _x = f'{num:,.2f}'.replace('.', '|')\
                      .replace(',', '.')\
                      .replace('|', ',')
    return _s + _x


class ReportBase(models.AbstractModel):
    _name = 'report.base'
    _description = 'Report Base'
    _auto = False

    def _get_default_template_view_external_id(self):
        return ''

    def _default_report_template(self):
        view_id = self._get_default_template_view_external_id()
        if not view_id:
            return False
        return self.env.ref(view_id).id

    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    template_id = fields.Many2one('report.template',
                                  string='Template',
                                  default=_default_report_template)
    report_type = fields.Selection([('table', 'Table'), ('pivot', 'Pivot'),
                                    ('crosstab', 'Crosstab')],
                                   string='Report Type',
                                   default='table')
    html = fields.Html(string='Html')
    preview_html = fields.Html(string='Preview')
    has_data = fields.Boolean(string='Has Data', default=False)
    store = fields.Text(string='Store', default='[]')
    # Paging Fields
    item_per_page = fields.Integer(string='Item Per Page', default=80)
    current_page = fields.Integer(string='Current Page', default=1)
    total_page = fields.Integer(string='Total Page', default=1)
    hide_paging = fields.Boolean(string='Hide Paging', default=False)

    def read(self, fields=None, load='_classic_read'):
        fields += [
            'item_per_page', 'current_page', 'total_page', 'hide_paging'
        ]
        return super(ReportBase, self).read(fields=fields, load=load)

    def paging_config(self, configs):
        if configs:
            item_per_page = configs.get('item_per_page', self.item_per_page)
            current_page = configs.get('current_page', self.current_page)
            total_record = len(json.loads(self.store))
            total_page = math.ceil(total_record / item_per_page)
            if current_page > total_page:
                current_page = total_page
            vals = {
                'item_per_page': configs.get('item_per_page',
                                             self.item_per_page),
                'current_page': configs.get('current_page', self.current_page),
                'total_page': total_page
            }
            self.write(vals)
        self.with_context(no_paging=False).action_report()
        return {
            'item_per_page': self.item_per_page,
            'current_page': self.current_page,
            'total_page': self.total_page,
            'preview_html': self.preview_html
        }

    def name_get(self):
        result = []
        for row in self:
            _name = row._context.get('name', False) or self.report_name()
            result.append((row.id, _name))
        return result

    def report_name(self):
        return ''

    def get_download_file_name(self):
        return ''

    def get_sheet_name(self):
        return 'Sheet1'

    def action_export_excel(self):
        if not self.has_data:
            return
        if not self.html or not self.hide_paging:
            self.with_context(no_paging=True).action_report()
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file_name = temp.name + '.xlsx'
            writer = pd.ExcelWriter(file_name, engine='xlsxwriter')

            writer.book.add_worksheet(self.get_sheet_name())
            writer, row = self.export_header(writer)
            writer, row = self.export_html(writer, row)
            writer, row = self.export_footer(writer, row)

            writer.save()
            datas = None
            with open(file_name, 'rb') as f:
                datas = f.read()
            if not datas:
                return
            return self.env['file.download'].download(
                self.get_download_file_name(), base64.b64encode(datas))

    def export_header(self, writer, start_row=0):
        if not self.template_id or not self.template_id.header_html:
            return writer, start_row
        html = self._get_header_template()
        writer, row = to_excel(html, writer, start_row)
        return writer, row

    def export_html(self, writer, start_row=0):
        writer, row = to_excel(self.html, writer, start_row, set_column=True)
        return writer, row

    def export_footer(self, writer, start_row=0):
        if not self.template_id or not self.template_id.footer_html:
            return writer, start_row
        html = self._get_footer_template()
        writer, row = to_excel(html, writer, start_row)
        return writer, row

    def action_renew(self):
        #
        # TODO Renew data here
        #
        self.with_context(renew=True).action_report()

    def action_report(self):
        data = self._get_data_paging()
        if not data:
            self.write({
                'has_data': False,
                'html': '',
                'preview_html': DATA_NOT_FOUND_HTML
            })
            return
        self.has_data = True
        self._build_report(data)
        self._apply_template()

    def _get_data_paging(self):
        if self.hide_paging or self._context.get('no_paging', True):
            return self._get_data_store()
        # Paging
        store = json.loads(self.store or '[]')
        if not store or self._context.get('renew', False):
            store = self._get_data_store()
        start = (self.current_page - 1) * self.item_per_page
        end = self.current_page * self.item_per_page
        if end > len(store):
            end = len(store)
        return store[start:end]

    def _get_data_store(self):
        store = self._get_report_json()
        self.store = json.dumps(store)
        self.total_page = math.ceil(len(store) / self.item_per_page)
        return store

    def _get_report_json(self):
        # Trả về dữ liệu cho báo cáo dạng json
        return []

    def _build_report(self, data):
        # Sử dụng pandas build bào cáo dự vào data truyền vào
        df = self._build_report_pandas(data)
        self._style_dataframe(df)

    def _build_report_pandas(self, data):
        if self.report_type == 'pivot':
            return self._build_report_pandas_pivot(data)
        elif self.report_type == 'crosstab':
            return self._build_report_pandas_crosstab(data)
        return self._build_report_pandas_table(data)

    def _build_report_pandas_table(self, data):
        df = pd.json_normalize(data)
        df.index += 1
        return df

    def _build_report_pandas_pivot(self, data):
        df = pd.json_normalize(data)
        configs = self.prepare_report_pivot_configs()
        pv = pd.pivot_table(df, **configs)
        pv = pv.droplevel(0, 1)
        pv = pv.fillna(0)
        return pv

    def _build_report_pandas_crosstab(self, data):
        return pd.json_normalize(data)

    def prepare_report_pivot_configs(self):
        # With report_type == 'pivot'
        # Prepare config to build pivot report
        # Template:
        # {
        #   'index': ['field_1'],
        #   'columns': ['field_2'],
        #   'values': ['field_3'],
        #   **pandas_pivot_params
        # }
        # Note: pandas_pivot_params referenece to link below
        # https://pandas.pydata.org/docs/reference/api/pandas.pivot_table.html
        return {}

    def prepare_report_crosstab_configs(self):
        # With report_type == 'pivot'
        # Prepare config to build pivot report
        # Template:
        # {
        #   'index': ['field_1'],
        #   'columns': ['field_2'],
        #   'values': ['field_3'],
        #   **pandas_pivot_params
        # }
        # Note: pandas_pivot_params referenece to link below
        # https://pandas.pydata.org/docs/reference/api/pandas.crosstab.html
        return {}

    def _style_dataframe(self, df):
        html = df.to_html(float_format=_money_format)
        soup = BeautifulSoup(html, 'html.parser')
        self._cook_soup(soup)
        self._cook_soup_head(soup, df)
        self._cook_soup_body(soup, df)
        self._cook_soup_foot(soup, df)
        self._apply_template_style(soup)
        self.html = soup.prettify()

    def _cook_soup(self, soup):
        # TODO Do something here
        pass

    def _cook_soup_head(self, soup, df):
        self._apply_merge_header(soup)
        self._apply_columns(soup)

    def _cook_soup_body(self, soup, df):
        self._align_with_data_type(df, soup)

    def _cook_soup_foot(self, soup, df):
        self._apply_merge_footer(soup)

    def _apply_columns(self, soup):
        names = self._columns_name()
        widths = self._columns_width()
        thead = soup.find('thead')
        ths = thead.findAll('th')
        for i in range(0, len(ths)):
            if ths[i].string and ths[i].string.strip() in widths:
                ths[i]['style'] = ths[i].get(
                    'style', []) + ['width: ' + widths[ths[i].string]]
            if ths[i].string and ths[i].string.strip() in names:
                ths[i].string = names[ths[i].string]

    def _align_with_data_type(self, df, soup):
        # Reference: https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html
        col_types = []
        for i in df.dtypes:
            col_types.append(i.kind in ('i', 'u', 'f'))

        tbody = soup.find('tbody')
        trs = tbody.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            for i in range(0, len(tds)):
                if col_types[i]:
                    tds[i]['style'] = tds[i].get('style',
                                                 []) + [';text-align: right']

    def _apply_template_style(self, soup):
        if not self.template_id or not self.template_id.style_id:
            return
        self._apply_template_style_head(soup)
        self._apply_template_style_body(soup)
        self._apply_template_style_foot(soup)

    def _apply_template_style_head(self, soup):
        css_thead = self.template_id.style_id.get_css_thead()
        thead = soup.find('thead')
        if not thead:
            return
        for th in thead.findAll('th'):
            th['style'] = th.get('style', []) + [';' + css_thead]

    def _apply_template_style_body(self, soup):
        css_tbody = self.template_id.style_id.get_css_tbody()
        css_index = self.template_id.style_id.get_css_index()
        tbody = soup.find('tbody')
        if not tbody:
            return
        for tr in tbody.findAll('tr'):
            if 'highlight' in tr.get('class', []):
                for th in tr.findAll('th'):
                    th['style'] = th.get('style', []) + [';' + CSS_HIGHLIGHT]
                for td in tr.findAll('td'):
                    td['style'] = td.get('style', []) + [';' + CSS_HIGHLIGHT]
        for td in tbody.findAll('td'):
            td['style'] = td.get('style', []) + [';' + css_tbody]
            if 'total' in td.get('class', []):
                td['style'] = td.get('style', []) + [';' + css_index]
        for th in tbody.findAll('th'):
            th['style'] = th.get('style', []) + [';' + css_index]

    def _apply_template_style_foot(self, soup):
        # todo
        css_tfoot = self.template_id.style_id.get_css_tfoot()
        tfoot = soup.find('tfoot')
        if not tfoot:
            return
        for th in tfoot.findAll('th'):
            th['style'] = th.get('style', []) + [';' + css_tfoot]

    def _apply_template(self):
        if not self.template_id:
            self.preview_html = self.html
            return
        header_html = self._get_header_template()
        footer_html = self._get_footer_template()
        self.preview_html = header_html + self.html + footer_html

    def _get_header_template(self):
        if not self.template_id.header_html:
            return ''
        html = eval(f'''f"""{self.template_id.header_html}"""''')
        html = self._fixed_template_layout(html)
        return html

    def _get_footer_template(self):
        if not self.template_id.footer_html:
            return ''
        html = eval(f'''f"""{self.template_id.footer_html}"""''')
        html = self._fixed_template_layout(html)
        return html

    def _fixed_template_layout(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if table:
            table['style'] = table.get('style', []) + ['table-layout: fixed']
        return soup.prettify()

    def _columns_name(self):
        # Đoạn này đang dùng theo dạng cấu hình tên cho từng cột:
        # Template:
        # return {
        #   'column_a': _('Column A'),
        #   'column_b': _('Column B'),
        # }
        return {}

    def _columns_width(self):
        # Đoạn này đang dùng theo dạng đưa giá trị vào để câu hình style width:
        # Template:
        # return {
        #   'column_1': '100px',
        #   'column_2': '120px',
        # }
        # Tip Hacking:
        # Nếu muôn thêm style có thể hack hàm này để đưa thêm style vào cho
        # từng cột theo column name:
        # Template:
        # return {
        #   'column_1': '100px; font-size: Tahoma;...',
        #   'column_2': 'auto; font-width: bold;...',
        # }
        return {}

    def _header_merge(self):
        # Build lai header cho table theo cấu hình dạng ma trận theo mẫu sau
        # merge item template: [col_start:row_start, col_end:row_end, col]
        # [
        #   ['0:0', '0:2', 'column_a'], ['2:1', '4:5', 'column_b']
        # ]
        # | .   | 0   | 1   | 2   | 3   | 4   | 5   | 6   | 7   |
        # | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        # | 0   | 0:0 | --- | --- | --- | --- | --- | --- | --- |
        # | 1   |     | --- | 2:1 |     |     | --- | --- | --- |
        # | 2   | 0:2 | --- |     |     |     | --- | --- | --- |
        # | 3   | --- | --- |     |     |     | --- | --- | --- |
        # | 4   | --- | --- |     |     |     | --- | --- | --- |
        # | 5   | --- | --- |     |     | 4:5 | --- | --- | --- |
        # | 6   | --- | --- | --- | --- | --- | --- | --- | --- |
        # | 7   | --- | --- | --- | --- | --- | --- | --- | --- |
        # Note: Trường hợp muốn merge 2 cột mà ko cần thay đổi tên cột
        # thì không cần truyền trên cột vào nữa
        return []

    def _footer_merge(self):
        return []

    def _apply_merge_header(self, soup):
        merge = self._header_merge()
        if not merge:
            return
        max_row = self._find_max_row_in_merge_config(merge)
        thead = soup.find('thead')
        trs = thead.findAll('tr')
        miss_row = max_row - len(trs)
        for i in range(0, miss_row):
            row = copy.copy(thead.find('tr'))
            thead.append(row)
        trs = thead.findAll('tr')
        extract_cell = {}
        for row in merge:
            [bc, br] = row[0].split(':')
            [ec, er] = row[1].split(':')
            bc = int(bc)
            br = int(br)
            ec = int(ec)
            er = int(er) 
            for r in range(0, len(trs)):
                extract_cell[r] = extract_cell.get(r, [])
                ths = trs[r].findAll('th')
                max_col = self._find_max_col_at_row_in_merge_config(r)
                if len(ths) < max_col:
                    raise ValidationError(
                        _('Table not has column at %s' % max_col))
                for c in range(0, len(ths)):
                    if br == r and bc == c:
                        if len(row) == 3:
                            ths[c].string = row[2]
                        # Cộng 1 ở colspan, rowspan là khi trừ nó chỉ ra được
                        # là merge bao nhiêu cột/dòng phía sau chứ chưa
                        # tính cột, dòng hiện tại
                        colspan = ec - bc
                        if colspan:
                            ths[c]['colspan'] = colspan + 1
                        rowspan = er - br
                        if rowspan:
                            ths[c]['rowspan'] = rowspan + 1
                        continue
                    if br <= r <= er and bc <= c <= ec:
                        extract_cell[r].append(c)

        if extract_cell:
            for r, c in extract_cell.items():
                c.sort(reverse=True)
                for i in c:
                    trs[r].findAll('th')[i].extract()

    def _apply_merge_footer(self, soup):
        merge = self._footer_merge()
        if not merge:
            return
        tfoot = soup.find('tfoot')
        if not tfoot:
            tfoot = soup.new_tag("tfoot")
            soup.table.append(tfoot)

        min_row = len(tfoot.findAll('tr'))
        max_row = self._find_max_row_in_merge_config(merge)
        for i in range(max_row - min_row):
            tr = soup.new_tag("tr")
            soup.table.tfoot.append(tr)

        trs = tfoot.findAll('tr')
        max_col = len(soup.find('tbody').findAll('tr')[0].findAll('td')) + 1
        for r in range(0, len(trs)):
            for i in range(max_col):
                th = soup.new_tag("th")
                trs[r].append(th)

        extract_cell = {}
        for row in merge:
            [bc, br] = row[0].split(':')
            [ec, er] = row[1].split(':')
            bc = int(bc)
            br = int(br)
            ec = int(ec)
            er = int(er) 
            for r in range(0, len(trs)):
                extract_cell[r] = extract_cell.get(r, [])
                ths = trs[r].findAll('th')
                for c in range(0, len(ths)):
                    if br == r and bc == c:
                        if len(row) == 3:
                            ths[c].string = row[2]
                        # Cộng 1 ở colspan, rowspan là khi trừ nó chỉ ra được
                        # là merge bao nhiêu cột/dòng phía sau chứ chưa
                        # tính cột, dòng hiện tại
                        colspan = ec - bc
                        if colspan:
                            ths[c]['colspan'] = colspan + 1
                        rowspan = er - br
                        if rowspan:
                            ths[c]['rowspan'] = rowspan + 1
                        continue
                    if br <= r <= er and bc <= c <= ec:
                        extract_cell[r].append(c)

        if extract_cell:
            for r, c in extract_cell.items():
                c.sort(reverse=True)
                for i in c:
                    trs[r].findAll('th')[i].extract()

    def _find_max_row_in_merge_config(self, merge):
        max_row = []
        for item in merge:
            # Start merge
            max_row.append(int(item[0].split(':')[1]))
            # End merge
            max_row.append(int(item[1].split(':')[1]))
        # Vì dòng bắt đầu = 0 vậy lên phải cộng thêm 1 để ra số lượng
        return max(max_row) + 1

    def _find_max_col_at_row_in_merge_config(self, row):
        merge = self._header_merge()
        max_col_at_row = []
        max_col = []
        for item in merge:
            # Start merge
            if int(item[0].split(':')[1]) == row:
                max_col_at_row.append(int(item[0].split(':')[0]))
            max_col.append(int(item[0].split(':')[0]))
            # End merge
            if int(item[0].split(':')[1]) == row:
                max_col_at_row.append(int(item[1].split(':')[0]))
            max_col.append(int(item[1].split(':')[0]))
        # Vì cột bắt đầu = 0 vậy lên phải cộng thêm 1 để ra số lượng
        if not max_col_at_row:
            return max(max_col) + 1
        return max(max_col_at_row) + 1
