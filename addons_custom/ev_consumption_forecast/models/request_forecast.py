# -*- coding: utf-8 -*-
import os
import json
import tempfile

from google.cloud import bigquery
from odoo import models, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class RequestForecast(models.Model):
    _name = 'request.forecast'
    _description = 'Request forecast API Google BigQuery'

    shop_id = fields.Many2one(comodel_name='pos.shop', string='Shop ID', required=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    date = fields.Date('Date', required=True)
    predicted_qty = fields.Float('Predicted Quantity', required=True)

    def _get_predicted_qty(self):
        try:
            request_forecast = self.env['google.bigquery.config'].sudo().search([('name', '=', 'request_forecast')],
                                                                                limit=1)
            file = tempfile.mktemp('key_api_bigquery.json')
            fo = open(file, 'w')
            fo.write(request_forecast.json_key)
            fo.close()

            # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath('key_api_bigquery.json')
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = file

            # BigQuery client object.
            client = bigquery.Client()
            today = datetime.today() + timedelta(hours=7)
            today_get = datetime.strftime(today, '%Y-%m-%d')
            # today_get = '2021-10-31'
            query = """
                   SELECT x_pos_shop_id, product_id, date, predicted_qty
                   FROM `homefarm-dwh.forecast.resquest_forecast`
                   WHERE date = '%s'
                   and predicted_qty > 0
                """ % (today_get)

            query_job = client.query(query)  # API request.

            for row in query_job:
                shop_id = self.env['pos.shop'].search([('id', '=', row['x_pos_shop_id'])], limit=1)
                if not shop_id:
                    continue
                product_id = self.env['product.product'].search([('id', '=', row['product_id'])], limit=1)
                if not product_id:
                    continue
                request_forecast_id = self.search([('shop_id','=',row['x_pos_shop_id']),('product_id','=',row['product_id']),('date','=',row['date'])], limit=1)
                if request_forecast_id:
                    request_forecast_id.predicted_qty = row['predicted_qty']
                else:
                    vals = {
                        'shop_id': row['x_pos_shop_id'],
                        'product_id': row['product_id'],
                        'date': row['date'],
                        'predicted_qty': row['predicted_qty'],
                    }
                    self.create(vals)
            self.env.cr.commit()
            os.remove(file)
        except Exception as e:
            raise ValidationError(e)
