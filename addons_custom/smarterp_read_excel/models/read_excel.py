# -*- coding: utf-8 -*-
# Copyright 2017 BMS GROUP GLOBAL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import ValidationError
import base64
import platform
import codecs
try:
    import tempfile
    import xlrd
except Exception:
    raise ValidationError(_('xlrd is required to install this module'))


class ReadExcel(models.Model):
    _name = 'read.excel'
    _auto = False


    def read_file(self, data, sheet, path=False):
        return read_file(data, sheet, path)


def read_file(data, sheet, path=False):
    if not path:
        path = '/file.xlsx'
    try:
        # file_path_temp = tempfile.gettempdir() + path
        # file_path = file_path_temp.replace("\\",'/')
        # f = open(file_path, 'wb')
        # f.write(base64.b64decode(data))
        # f.close()

        file_path = tempfile.gettempdir() + path
        f = open(file_path, 'wb')
        f.write(codecs.decode(data, 'base64'))
        f.close()

        workbook = xlrd.open_workbook(file_path)
    except Exception:
        raise ValidationError(
            _('File format incorrect, please upload file *.xls format'))

    try:
        worksheet = workbook.sheet_by_name(sheet)
    except Exception:
        try:
            worksheet = workbook.sheet_by_index(0)
        except Exception:
            raise ValidationError(_('Sheet name incorrect, please upload file '
                                    'has sheet name {}').format(sheet))
    # data= worksheet.iter_rows()
    res = []
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = -1
    while curr_row < num_rows:
        curr_row += 1
        row = []
        curr_cell = -1
        while curr_cell < num_cells:
            curr_cell += 1
            row.append(worksheet.cell_value(curr_row, curr_cell))
        res.append(row)

    return res
