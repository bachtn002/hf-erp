# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/21/2019


import logging
LOGGER = logging.getLogger(__name__)


class Query(object):

    SELECT = 'SELECT'
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'

    __QUERY_GET = '''SELECT {columns} FROM {tables} {joins} {wheres} {groups} {havings} {orders} {offset} {limit}'''

    def __init__(self):
        self.__sql = ''
        self.__columns = []
        self.__tables = []
        self.__joins = []
        self.__wheres = []
        self.__groups = []
        self.__havings = []
        self.__orders = []
        self.__offset = -1
        self.__limit = -1
        self.__query_params = []
        self.__cr = None

    def set_cr(self, cr):
        self.__cr = cr
        return self

    def add_columns(self, columns: list):
        self.__columns += [item for item in columns if item not in self.__columns]
        return self

    def add_tables(self, tables: list):
        self.__tables += [item for item in tables if item not in self.__tables]
        return self

    def add_joins(self, joins: list):
        self.__joins += [item for item in joins if item not in self.__joins]
        return self

    def add_wheres(self, wheres: list):
        self.__wheres += wheres
        return self

    def add_groups(self, groups: list):
        self.__groups += [item for item in groups if item not in self.__groups]
        return self

    def add_havings(self, havings: list):
        self.__havings += [item for item in havings if item not in self.__havings]
        return self

    def add_orders(self, orders: list):
        self.__orders += [item for item in orders if item not in self.__orders]
        return self

    def set_offset(self, offset):
        self.__offset = offset
        return self

    def set_limit(self, limit):
        self.__limit = limit
        return self

    def add_query_params(self, params):
        self.__query_params += params
        return self

    def set_sql(self, sql):
        self.__sql = sql
        return self

    def to_sql(self):
        (column_clause, table_clause, join_clause, where_clause, group_clause, having_clause,
         order_clause, offset_clause, limit_clause) = self.__query_factory_fragment()
        return self.__QUERY_GET.format(columns=column_clause,
                                       tables=table_clause,
                                       joins=join_clause,
                                       wheres=where_clause,
                                       groups=group_clause,
                                       havings=having_clause,
                                       orders=order_clause,
                                       offset=offset_clause,
                                       limit=limit_clause)

    def execute_one(self):
        query = self.__sql if self.__sql else self.to_sql()
        self.__cr.execute(query, tuple(self.__query_params))
        return self.__cr.dictfetchone()

    def execute_all(self):
        query = self.__sql if self.__sql else self.to_sql()
        self.__cr.execute(query, tuple(self.__query_params))
        return self.__cr.dictfetchall()

    def __query_factory_fragment(self):
        column_clause = self.__get_column_clause()
        table_clause = self.__get_table_clause()
        join_clause = self.__get_join_clause()
        where_clause = self.__get_where_clause()
        group_clause = self.__get_group_clause()
        having_clause = self.__get_having_clause()
        order_clause = self.__get_order_clause()
        offset_clause = self.__get_offset_clause()
        limit_clause = self.__get_limit_clause()

        return (column_clause, table_clause, join_clause, where_clause, group_clause, having_clause,
                order_clause, offset_clause, limit_clause)

    def __get_column_clause(self):
        return ',\n'.join([cl for cl in self.__columns])

    def __get_table_clause(self):
        return ',\n'.join([tb for tb in self.__tables])

    def __get_join_clause(self):
        return '\n'.join([j for j in self.__joins])

    def __get_where_clause(self):
        if len(self.__wheres) > 0:
            where = ' AND '.join([wh for wh in self.__wheres])
            return '''\nWHERE %s''' % where
        return ''

    def __get_group_clause(self):
        if len(self.__groups) > 0:
            group = ', '.join([gr for gr in self.__groups])
            return '''\nGROUP BY %s''' % group
        return ''

    def __get_having_clause(self):
        if len(self.__havings) > 0:
            having = 'and '.join([hv for hv in self.__havings])
            return '''\nHAVING %s''' % having
        return ''

    def __get_order_clause(self):
        if len(self.__orders) > 0:
            order = ', '.join([od for od in self.__orders])
            return '''\nORDER BY %s ''' % order
        return ''

    def __get_offset_clause(self):
        if self.__offset >= 0:
            self.__query_params += [self.__offset]
            return '''\nOFFSET %s'''
        return ''

    def __get_limit_clause(self):
        if self.__limit >= 0:
            self.__query_params += [self.__limit]
            return '''\nLIMIT %s'''
        return ''
