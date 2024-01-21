# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/25/2019

import sqlite3
from operator import itemgetter
import json

from .Dispatch import Dispatch

from odoo import tools, _

# Source sẽ đươc tính từ vị trí của venv
DB_SOURCE = tools.config.options.get('api_base_filter_source') or 'addons_custom/ev_api_base/data/'
if not DB_SOURCE.endswith('/'):
    DB_SOURCE += '/'
DB_NAME = DB_SOURCE + 'store.db'


class Filter(object):

    conn = None
    cr = None
    store = {}

    def connect(self):
        if not self.conn:
            try:
                self.conn = sqlite3.connect(DB_NAME)
            except Exception as e:
                self.conn = sqlite3.connect(':memory:')
    
    def make_cr(self):
        self.connect()
        if not self.cr:
            self.cr = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def cr_close(self):
        if self.cr:
            self.cr.close()

    def create_table(self):
        self.cr.execute('''CREATE TABLE IF NOT EXISTS filter_store (id integer primary key, data text)''')
        self.conn.commit()

    def get_store(self):
        self.cr.execute('''SELECT data FROM filter_store ORDER BY id DESC LIMIT 1''')
        row = self.cr.fetchone()
        self.store = json.loads(row[0]) if row else {}

    def save_store(self):
        self.cr.execute('''INSERT INTO filter_store(data) VALUES (?)''', (json.dumps(self.store), ))
        self.conn.commit()
    
    def clear_old_data(self):
        self.cr.execute('''DELETE FROM filter_store WHERE id < SELECT (id FROM file_store ORDER BY id DESC LIMIT 1)''')
        self.conn.commit()

    def __init__(self):
        self.make_cr()
        self.create_table()

    def push(self, filter: dict, override=False):
        for key, value in filter.items():
            exists = self.store.get(key)
            if not exists or exists and override:
                self.store.update({key: value})
                continue
            if isinstance(value, dict):
                continue
            ss = []
            for val in value:
                if 'sequence' not in val:
                    val['sequence'] = 1
                check = False
                for exist in exists:
                    if val['key'] == exist['key']:
                        check = True
                        break
                if not check:
                    ss.append(val)
            self.store.update({key: exists + ss})
        self.save_store()

    def get(self, key, reverse=False):
        # self.get_store()
        result = self.store.get(key.upper(), {})
        if isinstance(result, dict):
            data_store = self.__get_callback(result)
            if len(data_store) > 0:
                self.store.update({key.upper(): data_store})
            result = data_store
        for item in result:
            for k, v in item.items():
                v = _(v)
        return sorted(result, key=itemgetter('sequence'), reverse=reverse)

    def get_key(self):
        self.get_store()
        result = [key for key, value in self.store.items()]
        return result

    @staticmethod
    def __get_callback(obj_callback):
        callback_data = Dispatch.dispatch(obj_callback['instance'], obj_callback['callback'])
        result = []
        if callback_data['code'] != 200:
            return result
        seq = 0
        map_key = obj_callback.get('map_key', {})
        for item in callback_data['data']:
            result.append({'key': item.get(map_key.get('key', 'key')),
                           'name': item.get(map_key.get('name', 'name')),
                           'sequence': item.get(map_key.get('id', 'id'), seq)})
            seq += 1

        return result + obj_callback.get('static_data', [])
