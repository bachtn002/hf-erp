# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/20/2019


class Pager(object):
    items_per_page = 15
    page = 1

    def __init__(self, page=1, items_per_page=15):
        try:
            self.page = int(page) or 1 if page else 1
            self.items_per_page = int(items_per_page) or 15 if items_per_page else 15
        except Exception as e:
            self.page = 1
            self.items_per_page = 15

    def get_offset(self):
        page = self.page - 1 if self.page - 1 >= 0 else 0
        return page * self.items_per_page

    def get_limit(self):
        if self.page <= 0:
            return None
        return self.items_per_page

    def get_meta_data(self, total_record):
        next_page = self.page + 1 if total_record > self.page * self.items_per_page else self.page
        return {
            'total_record': total_record,
            'current_page': self.page,
            'next_page': next_page,
            'items_per_page': self.items_per_page
        }
