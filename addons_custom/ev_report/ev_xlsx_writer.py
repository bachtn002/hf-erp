import re
from bs4 import BeautifulSoup, NavigableString

COL_MAX_WIDTH = 150
COL_MIN_WIDTH = 10

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def get_xlsxwriter_format(html):
    styles = export_template_style(html)
    _format = []
    for tr_styles in styles:
        tr_format = []
        for cell_styles in tr_styles:
            tr_format.append(transform_css_to_xlsxwriter_style(cell_styles))
        _format.append(tr_format)
    return _format


def _get_row_children(soup_row):
    return [
        child for child in soup_row.children
        if not isinstance(child, NavigableString)
    ]


def export_template_style(html):
    # todo
    soup = BeautifulSoup(html)
    table = soup.find('table')
    thead = table.find('thead')
    tbody = table.find('tbody')
    tfoot = table.find('tfoot')
    styles = []
    if thead:
        for tr in thead.findAll('tr'):
            tr_styles = []
            tr_style = [tr.get('style')] if tr.get('style') else []
            for cell in _get_row_children(tr):
                cell_styles = [cell.get('style')] if cell.get('style') else []
                for child in cell.children:
                    if isinstance(child, NavigableString):
                        continue
                    cell_styles.append(child.get('style'))
                tr_styles.append(cell_styles + tr_style)
            styles.append(tr_styles)
    if tbody:
        for tr in tbody.findAll('tr'):
            tr_styles = []
            tr_style = [tr.get('style')] if tr.get('style') else []
            for cell in _get_row_children(tr):
                cell_styles = [cell.get('style')] if cell.get('style') else []
                for child in cell.children:
                    if isinstance(child, NavigableString):
                        continue
                    cell_styles.append(child.get('style'))
                tr_styles.append(cell_styles + tr_style)
            styles.append(tr_styles)
    if tfoot:
        for tr in tfoot.findAll('tr'):
            tr_styles = []
            tr_style = [tr.get('style')] if tr.get('style') else []
            for cell in _get_row_children(tr):
                cell_styles = [cell.get('style')] if cell.get('style') else []
                for child in cell.children:
                    if isinstance(child, NavigableString):
                        continue
                    cell_styles.append(child.get('style'))
                tr_styles.append(cell_styles + tr_style)
            styles.append(tr_styles)
    return styles


def transform_css_to_xlsxwriter_style(data_styles):
    xlsxwriter_style = {}
    for line in data_styles:
        styles = line.split(';') if line else []
        for style in styles:
            if not style:
                continue
            xlsxwriter_style.update(tranform(style.strip()))
    return xlsxwriter_style


def tranform(style):
    try:
        key, value = style.split(':')
    except Exception:
        return {}
    value = value.strip()
    # Font
    if key == 'font-family':
        return {'font_name': value.replace('"', '').replace("'", '')}
    elif key == 'font-size':
        fonts = find_int_in_str(value)
        font_size = int(float(fonts[0]))
        return {'font_size': font_size}
    elif key == 'color':
        if value.startswith('rgb'):
            return {'font_color': rgb_to_hex(value)}
        return {'font_color': value}
    elif key == 'font-style':
        if value == 'italic':
            return {'italic': True}
        elif value == 'underline':
            return {'underline': True}
    elif key == 'font-weight':
        if value == 'bold':
            return {'bold': True}
        elif value.isnumeric() and int(value) > 500:
            return {'bold': True}
    # Alignment
    elif key == 'text-align':
        if value == 'right':
            #mặc định text-align right với dạng số nên format
            return {'align': value, 'num_format': '#,##0'}
        return {'align': value}
    elif key == 'vertical-align':
        return {'vertical': value}
    # Pattern
    elif key == 'background-color':
        if value.startswith('rgb'):
            return {'bg_color': rgb_to_hex(value)}
        return {'bg_color': value}
    return {}


def find_int_in_str(str):
    find = re.findall(r'[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?',
                      str)
    if find:
        return find
    return []


def rgb_to_hex(color):
    colors = find_int_in_str(color)
    r = int(float(colors[0]))
    g = int(float(colors[1]))
    b = int(float(colors[2]))
    return '#%02x%02x%02x' % (r, g, b)


def _to_excel(soup, writer, xlsx_formats=[], fi=0, start_row=0, **kwargs):
    set_column = kwargs.get('set_column', False)
    merges = []
    total_cols = 0
    row = start_row

    workbook = writer.book
    worksheet = workbook.get_worksheet_by_name('Sheet1')

    def is_merge_cell(_row, _col):
        for merge in merges:
            if merge[0] <= _row <= merge[2] and merge[1] <= _col <= merge[3]:
                return True
        return False

    first_tr = soup.find('tr')
    for item in first_tr.children:
        if isinstance(item, NavigableString):
            continue
        colspan = item.get('colspan')
        if not colspan:
            total_cols += 1
        else:
            total_cols += int(colspan)

    tr_list = soup.findAll('tr')
    columns_width = {}
    for tr_item in tr_list:
        col = 0
        html_col = 0
        cell_list = _get_row_children(tr_item)
        for col in range(0, total_cols):
            if is_merge_cell(row, col):
                continue
            item = cell_list[html_col]
            # Start compute Max column width
            ltext = len(item.text)
            if columns_width.get(col, 0) < ltext:
                w = min(COL_MAX_WIDTH, max(COL_MIN_WIDTH, ltext))
                columns_width[col] = w
            # End compute Max column width
            cell_format = workbook.add_format(xlsx_formats[fi][html_col])
            html_col += 1
            rowspan = item.get('rowspan')
            merge = []
            if rowspan:
                rowspan = int(rowspan)
                merge = [row, col, row + rowspan - 1, col]
            colspan = item.get('colspan')
            if colspan:
                colspan = int(colspan)
                if merge:
                    merge[4] += colspan - 1
                else:
                    merge = [row, col, row, col + colspan - 1]
            item_value = item.text.strip()
            if ',' in item_value:
                if is_float(item_value.replace(
                        '.', '').replace(',', '.')):
                    item_value = float(item_value.replace(
                        '.', '').replace(',', '.'))
            if merge:
                merges.append(merge)
                worksheet.merge_range(merge[0], merge[1], merge[2], merge[3],
                                      item_value, cell_format)
            else:
                worksheet.write(row, col, item_value, cell_format)
        row += 1
        fi += 1

    # Set column width
    if set_column:
        for c, w in columns_width.items():
            worksheet.set_column(c, c, w)

    return writer, row, fi


def to_excel(html, writer, start_row=0, **kwargs):
    if not html:
        return writer, start_row
    soup = BeautifulSoup(html)
    s_btl = soup.find('table')
    if not s_btl:
        return writer, start_row
    s_thead = s_btl.find('thead')
    s_tbody = s_btl.find('tbody')
    s_tfoot = s_btl.find('tfoot')

    elsx_formats = get_xlsxwriter_format(html)
    row = start_row
    fi = 0
    if s_thead:
        writer, row, fi = _to_excel(s_thead, writer, elsx_formats, fi,
                                    start_row, **kwargs)

    if s_tbody:
        writer, row, fi = _to_excel(s_tbody, writer, elsx_formats, fi, row,
                                    **kwargs)
    
    if s_tfoot:
        writer, row, fi = _to_excel(s_tfoot, writer, elsx_formats, fi, row,
                                    **kwargs)
    return writer, row
