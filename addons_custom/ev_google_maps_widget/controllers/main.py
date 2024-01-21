# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import http
from odoo.http import request


class Google(http.Controller):
    @http.route("/google_maps/google_maps_api_key", type="json", auth="public", website=True)
    def google_maps_api_key(self):
        google_maps_api_key = request.env['ir.config_parameter'].sudo().get_param('ev_google_maps_widget.google_maps_api_key'),
        return json.dumps({"google_maps_api_key": google_maps_api_key or ""})
