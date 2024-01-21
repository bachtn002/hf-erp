# -*- coding: utf-8 -*-
import psycopg2
from odoo import models, fields, api


class ConnectionSlave(models.Model):
    _name = 'connection.slave'

    name = fields.Char('Connection')
    host = fields.Char('Host')
    port = fields.Char('Port')
    user = fields.Char('User')
    password = fields.Char('Password')
    database = fields.Char('Database')
    state = fields.Selection([('not_connect','Not Connect'), ('connect','Connect')], 'Connect', default='not_connect')

    def _connec_slave(self):
        try:
            # connect to the PostgreSQL server
            conn = psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password, port=self.port)
            # create a cursor
            cur = conn.cursor()
            # Execute a sql
            cur.execute('SELECT version()')
            # display the PostgreSQL database server version
            version = cur.fetchone()
            print(version)
            # close the communication with the PostgreSQL
            cur.close()
            return True
        except Exception as e:
            print('Unable to connect %s' % str(e))
            return False
        finally:
            if conn is not None:
                conn.close()
                return False

    def action_check_connection(self):
        if self._connec_slave():
            self.state = 'not_connect'
        else:
            self.state = 'connect'


