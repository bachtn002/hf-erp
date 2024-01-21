# -*- coding: utf-8 -*-
# Created by hoanglv at 6/1/2020

from odoo.http import request

import re
from html.parser import HTMLParser


class ImageHtmlParser(HTMLParser):

    image_src_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attr in attrs:
                if attr[0] != 'src' or attr[1] in self.image_src_data:
                    continue
                self.image_src_data.append(attr[1])


class Html(object):

    def __init__(self):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not base_url.endswith('/'):
            base_url += '/'
        self.URL_ROOT = base_url

    @staticmethod
    def clear_html_tag(text: str = ''):
        tag_pattern = r'<.*?>'
        return re.sub(tag_pattern, '', text)

    def remake_image_src(self, html_str: str = ''):
        """

        :param html_str:
        :type html_str:
        :return:
        :rtype:
        """
        # Khởi tạo class để lấy dữ liệu src trong tag img
        parser = ImageHtmlParser()
        parser.feed(html_str)
        # Bắt đầu vòng lặp để sử lý html_str
        for img_src in parser.image_src_data:
            if img_src.find('http') >= 0:
                continue
            # Tạo src mới
            if img_src[0:1] == '/':
                # Xóa dầu / đầu tiên tại url
                new_img_src = self.URL_ROOT + img_src[1:]
            else:
                new_img_src = self.URL_ROOT + img_src
            html_str = html_str.replace(img_src, new_img_src)
        return html_str
