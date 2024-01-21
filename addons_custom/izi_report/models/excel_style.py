# -*- encoding: utf-8 -*-

def get_style(wb):
    style_14_bold_center = wb.add_format(
        {'bold': True, 'font_size': '14', 'font_color': 'black', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': False})

    style_12_bold_left = wb.add_format(
        {'bold': True, 'font_size': '12', 'font_color': 'black', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': False})

    style_12_bold_center_border = wb.add_format(
        {'bold': True, 'font_size': '12', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'bg_color': '#3C5E2C',
         'text_wrap': True,
         'border': True})

    style_12_left = wb.add_format(
        {'bold': False, 'font_size': '12', 'font_color': 'black', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})

    style_12_right = wb.add_format(
        {'bold': False, 'font_size': '12', 'font_color': 'black', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})

    style_12_center_data = wb.add_format(
            {'bold': False, 'font_size': '10', 'font_color': 'black', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})

    style_12_left_data = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'black', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})

    # tiennq
    style_12_left_data_blue = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'blue', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_left_data_red = wb.add_format(
        {'bold': True, 'font_size': '10',
         'font_color': 'red', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_left_data_text_bold = wb.add_format(
        {'bold': True, 'font_size': '10',
         'font_color': 'black', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_left_data_green = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'green', 'align': 'left', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_center_data_red = wb.add_format(
        {'bold': False, 'font_size': '10', 'font_color': 'red', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_center_data_green = wb.add_format(
        {'bold': False, 'font_size': '10', 'font_color': 'green', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_center_data_blue = wb.add_format(
        {'bold': False, 'font_size': '10', 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_right_data_blue = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'blue', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_right_data_blue_number = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'blue', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True, 'num_format': '#,##0',
         'border': True})
    style_12_right_data_red = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'red', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_right_data_red_number = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'red', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True, 'num_format': '#,##0',
         'border': True})
    style_12_right_data_green = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'green', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    style_12_right_data_green_number = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'green', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True, 'num_format': '#,##0',
         'border': True})
    ########

    style_12_right_data = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'black', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True,
         'border': True})
    #tuuh
    style_12_right_data_number = wb.add_format(
        {'bold': False, 'font_size': '10',
         'font_color': 'black', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True, 'num_format': '#,##0',
         'border': True})
    style_12_right_data_number_bold = wb.add_format(
        {'bold': True, 'font_size': '10',
         'font_color': 'black', 'align': 'right', 'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'text_wrap': True, 'num_format': '#,##0',
         'border': True})

    style_11_left = wb.add_format(
        {
            'font_size': '10',
            'font_color': 'black',
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'text_wrap': True
        }
    )

    style_11_right = wb.add_format(
        {
            'font_size': '10',
            'font_color': 'black',
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'text_wrap': True
        }
    )

    style_11_center = wb.add_format(
        {
            'font_size': '10',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'text_wrap': True
        }
    )

    style_11_right_footer = wb.add_format(
        {'bold': True,
         'font_size': '10',
         'font_color': 'black',
         'align': 'right',
         'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'bg_color': '#F3FD9F',
         'text_wrap': True,
         'border': True})
    style_11_right_footer_number = wb.add_format(
        {'bold': True,
         'font_size': '10',
         'font_color': 'black',
         'align': 'right',
         'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'bg_color': '#F3FD9F',
         'text_wrap': True,
         'border': True,
         'num_format': '#,##0'})
    style_11_center_footer = wb.add_format(
        {'bold': True,
         'font_size': '10',
         'font_color': 'black',
         'align': 'center',
         'valign': 'vcenter',
         'font_name': 'Times New Roman',
         'bg_color': '#F3FD9F',
         'text_wrap': True,
         'border': True})

    return {
        'style_14_bold_center': style_14_bold_center,
        'style_12_bold_left': style_12_bold_left,
        'style_12_center_data': style_12_center_data,
        'style_12_center_data_red': style_12_center_data_red,
        'style_12_center_data_green': style_12_center_data_green,
        'style_12_center_data_blue': style_12_center_data_blue,
        'style_12_left': style_12_left,
        'style_12_right': style_12_right,
        'style_12_right_data_blue': style_12_right_data_blue,
        'style_12_left_data': style_12_left_data,
        'style_12_left_data_blue': style_12_left_data_blue,
        'style_12_left_data_red': style_12_left_data_red,
        'style_12_left_data_green': style_12_left_data_green,
        'style_12_right_data': style_12_right_data,
        'style_12_right_data_number': style_12_right_data_number,
        'style_12_right_data_number_bold': style_12_right_data_number_bold,
        'style_12_right_data_red': style_12_right_data_red,
        'style_12_right_data_green': style_12_right_data_green,
        'style_12_right_data_blue_number': style_12_right_data_blue_number,
        'style_12_right_data_green_number': style_12_right_data_green_number,
        'style_12_right_data_red_number': style_12_right_data_red_number,
        'style_12_bold_center_border': style_12_bold_center_border,
        'style_11_left': style_11_left,
        'style_11_right': style_11_right,
        'style_11_center': style_11_center,
        'style_11_right_footer': style_11_right_footer,
        'style_11_right_footer_number': style_11_right_footer_number,
        'style_11_center_footer': style_11_center_footer,
        'style_12_left_data_text_bold': style_12_left_data_text_bold,
    }


def write_roman(num):
    from collections import OrderedDict
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num > 0:
                roman_num(num)
            else:
                break

    return "".join([a for a in roman_num(num)])
