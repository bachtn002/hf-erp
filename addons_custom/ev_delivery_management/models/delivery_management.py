import re
import logging
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date

from ..helpers import APIGrab, GoogleMaps, APIInternal, APIAhamove

_logger = logging.getLogger(__name__)


class DeliveryManagement(models.Model):
    _name = 'delivery.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Delivery Management'
    _order = 'create_date desc'

    def _default_domain_sender(self):
        try:
            if self.env.uid == SUPERUSER_ID or self.env.user.has_group('base.group_system'):
                user = self.env['res.users'].sudo().search([])
                domain = [('id', 'in', user.partner_id.ids)]
            else:
                domain = [('id', 'in', self.env.user.partner_id.ids)]
            return domain
        except Exception as e:
            raise ValidationError(e)

    name = fields.Char('Name', required=True, default=lambda self: _('New'), readonly=True)
    origin = fields.Char('Origin', required=True)
    delivery_reference = fields.Char('Delivery Reference')
    description = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('waiting', 'Waiting'),
        ('pickup', 'pickUp'),
        ('delivering', 'Delivering'),
        ('failed', 'Failed'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], string='State', default='draft', track_visibility='onchange')

    delivery_fee = fields.Float('Delivery fee')
    cod = fields.Float('COD')
    qty = fields.Integer('Quantity', default=1)

    # Giao hàng grab
    height = fields.Integer('Height')
    width = fields.Integer('Width')
    depth = fields.Integer('Depth')
    weight = fields.Float('Weight')

    sender_id = fields.Many2one('res.partner', 'Sender ID', domain=_default_domain_sender)
    phone_sender = fields.Char('Phone')
    address_sender = fields.Char('Address')
    lat_sender = fields.Char('Lat')
    long_sender = fields.Char('Long')

    recipient_id = fields.Char('Recipient ID')
    phone_recipient = fields.Char('Phone')
    address_recipient = fields.Char('Address')
    lat_recipient = fields.Char('Lat')
    long_recipient = fields.Char('Long')

    track_url = fields.Char('Track URL')
    pickup_pin = fields.Char('Pickup Pin')
    failed_reason = fields.Char('Failed Reason', track_visibility='onchange')

    driver_name = fields.Char('Driver Name')
    driver_phone = fields.Char('Phone')
    license_plate = fields.Char('License Plate')

    # Giao hàng nội bộ
    store_id = fields.Many2one('pos.shop', 'Store ID')
    total_price = fields.Float('Total Price')
    is_delivery_internal = fields.Boolean('Is Delivery Internal', default=False)

    count_call_grab = fields.Integer('Count Call Grab', default=0)
    count_call_aha = fields.Integer('Count Call Aha', default=0)
    count_call_internal = fields.Integer('Count Call Internal', default=0)

    type_origin = fields.Selection([('order', 'Order'), ('transfer', 'Transfer')], 'Type Origin', default=None)
    state_delivery = fields.Char('State Delivery', track_visibility='onchange')

    delivery_partner_id = fields.Many2one('delivery.partner', 'Delivery Partner', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    distance = fields.Float('Distance', digits=(12, 3))

    # thêm trường liên kết
    order_id = fields.Many2one('pos.order', 'Order')
    transfer_id = fields.Many2one('stock.transfer', 'Transfer')

    # nội bộ hủy đơn hàng
    is_internal_cancel = fields.Boolean('Is Internal Cancel', default=False)

    @api.onchange('sender_id')
    def _onchange_sender_id(self):
        try:
            if self.sender_id:
                self.phone_sender = self.sender_id.phone
                self.address_sender = self.sender_id.street
            else:
                self.phone_sender = None
                self.address_sender = None
        except Exception as e:
            raise ValidationError(e)

    @api.constrains('height', 'width', 'depth', 'weight')
    def _check_dimensions(self):
        try:
            for rc in self:
                if rc.height > 50:
                    raise UserError(_('Height must be less than 50'))
                if rc.width > 50:
                    raise UserError(_('Width must be less than 50'))
                if rc.depth > 50:
                    raise UserError(_('Depth must be less than 50'))
                if rc.weight > 20.00:
                    raise UserError(_('Weight must be less than 20'))
        except Exception as e:
            raise ValidationError(e)

    @api.constrains('state')
    def send_mess_notification_state(self):
        try:
            if self.sender_id and self.state == 'draft':
                msg = _('Notification! Delivery %s (%s): %s.', self.name, self.origin, self.state)
                notification_ids = []
                notification_ids.append((0, 0, {
                    'res_partner_id': self.sender_id.id,
                    'notification_type': 'inbox'}))
                self.message_post(body=msg, message_type='notification', partner_id=self.sender_id.id,
                                  notification_ids=notification_ids)
        except Exception as e:
            raise ValidationError(e)

    @api.constrains('state')
    def algorithm_call_delivery(self):
        try:
            # nếu nội bộ hủy đơn hàng thì không tự động gọi ship
            if self.is_internal_cancel:
                return
            partner_ahamove = self.env['delivery.partner'].sudo().search(
                [('code', '=', 'ahamove'), ('active', '=', True)], limit=1)
            partner_grab = self.env['delivery.partner'].sudo().search(
                [('code', '=', 'grab'), ('active', '=', True)], limit=1)
            if self.state == 'failed' and not self.is_delivery_internal:
                if self.delivery_partner_id.code == 'grab':
                    if self.count_call_grab < 1:
                        self.send_grab()
                    elif self.count_call_aha < 1 and partner_ahamove:
                        self.delivery_partner_id = partner_ahamove
                        self.send_ahamove()
                elif self.delivery_partner_id.code == 'ahamove':
                    if self.count_call_aha < 1:
                        self.send_ahamove()
                    elif self.count_call_grab < 1 and partner_grab:
                        self.delivery_partner_id = partner_grab
                        self.send_grab()
                else:
                    self.state = 'cancel'
                    self.failed_reason = _('Can not call delivery')

        except Exception as e:
            raise ValidationError(e)

    def action_send(self):
        try:
            if self.is_delivery_internal and not self.delivery_partner_id:
                return
            if self.state == 'draft':
                self.state = 'queue'
                # self._action_done()
                self.sudo().with_delay(channel='root.action_send_delivery', max_retries=3)._action_done()
        except Exception as e:
            raise ValidationError(e)

    def _action_done(self):
        try:
            self.check_delivery()
            if self.state not in ('draft', 'queue'):
                return

            if not self.delivery_partner_id and not self.is_delivery_internal:
                self.action_call_delivery()
            else:
                if self.delivery_partner_id.code == 'internal':
                    self.send_internal()
                else:
                    if self.delivery_partner_id.code == 'grab':
                        self.send_grab()
                    elif self.delivery_partner_id.code == 'ahamove':
                        self.send_ahamove()
        except Exception as e:
            raise ValidationError(e)

    def action_get_delivery_detail(self):
        try:
            if self.delivery_reference and self.delivery_partner_id.code == 'internal':
                APIInternal.get_delivery_detail(self)
            else:
                if self.delivery_reference and self.delivery_partner_id.code == 'grab':
                    APIGrab.get_delivery_detail(self)
                elif self.delivery_reference and self.delivery_partner_id.code == 'ahamove':
                    self.get_detail_ahamove()
        except Exception as e:
            raise ValidationError(e)

    def get_delivery_internal_status(self):
        try:
            records = self.env['delivery.management'].sudo().search(
                [('delivery_partner_id.code', '=', 'internal'),
                 ('state', 'not in', ['draft', 'queue', 'done', 'cancel'])])
            for record in records:
                APIInternal.get_delivery_detail(record)
                # status = APIInternal.get_delivery_status(record)
                # if status == 'WAITING':
                #     record.state = 'waiting'
                # if status == 'PROCESSING':
                #     record.state = 'delivering'
                # if status in ('DELIVERY_SUCCESS', 'CLOSED'):
                #     record.state = 'done'
                # if status == 'CANCELLED':
                #     record.state = 'cancel'
                # if status == 'DELIVERY_FAIL':
                #     record.state = 'cancel'
        except Exception as e:
            raise ValidationError(e)

    def action_back(self):
        try:
            if not self.delivery_partner_id:
                self.state = 'draft'
                return
            if self.delivery_partner_id.code == 'internal':
                self.back_internal()
            else:
                if self.delivery_partner_id.code == 'grab':
                    self.back_grab()
                elif self.delivery_partner_id.code == 'ahamove':
                    self.back_ahamove()
        except Exception as e:
            raise ValidationError(e)

    def action_cancel(self):
        try:
            if not self.delivery_partner_id:
                self.state = 'cancel'
                return
            if self.delivery_partner_id.code == 'internal':
                self.cancel_internal()
            else:
                if self.delivery_partner_id.code == 'grab':
                    self.cancel_grab()
                elif self.delivery_partner_id.code == 'ahamove':
                    self.cancel_ahamove()

            # nội bộ hủy đơn hàng
            self.is_internal_cancel = True

        except Exception as e:
            raise ValidationError(e)

    def send_internal(self):
        try:
            delivery = APIInternal.create_delivery_request(self)
            self.is_delivery_internal = True
            self.count_call_internal += 1
            if delivery.get('isSuccess'):
                message = delivery.get('message')
                success = message.split(',')[0]
                duplicate = message.split(',')[1]
                failed = message.split(',')[2]
                code_success = re.sub(r"[^0-9]", "", success)
                code_duplicate = re.sub(r"[^0-9]", "", duplicate)
                code_failed = re.sub(r"[^0-9]", "", failed)
                if code_success == '1':
                    self.state = 'waiting'
                    self.failed_reason = None
                    APIInternal.get_delivery_detail(self)
                if code_duplicate == '1' or code_failed == '1':
                    self.state = 'failed'
                    self.failed_reason = delivery.get('errors')
            else:
                self.state = 'failed'
                self.failed_reason = delivery.get('errors')
        except Exception as e:
            raise ValidationError(e)

    def cancel_internal(self):
        try:
            if self.state == 'draft':
                self.state = 'cancel'
                return
            delivery = APIInternal.cancel_delivery(self)
            if delivery:
                self.state = 'cancel'
            else:
                raise UserError(_('Can not cancel when the parcel is processed'))
        except Exception as e:
            raise ValidationError(e)

    def back_internal(self):
        try:
            if self.state in ('cancel', 'failed'):
                self.state = 'draft'
                self.driver_name = None
                self.driver_phone = None
                self.license_plate = None
                self.delivery_fee = None
                self.failed_reason = None
        except Exception as e:
            raise ValidationError(e)

    def send_grab(self):
        try:
            delivery = APIGrab.create_delivery_request(self)
            self.count_call_grab += 1
            if 'deliveryID' in delivery:
                self.driver_name = None
                self.driver_phone = None
                self.driver_phone = None
                self.license_plate = None
                self.delivery_reference = delivery.get('deliveryID')
                self.delivery_fee = delivery.get('quote').get('amount')
                # update distance from order responsed
                self.distance = delivery.get('quote').get('distance')/1000
                self.state = 'waiting'
            else:
                self.state = 'failed'
        except Exception as e:
            raise ValidationError(e)

    def cancel_grab(self):
        try:
            if self.state == 'draft':
                self.state = 'cancel'
                return
            delivery = APIGrab.cancel_delivery(self)
            dict = {}
            boolean = True
            if type(delivery) == type(boolean):
                if delivery == boolean:
                    self.state = 'cancel'
            elif type(delivery) == type(dict):
                if 'arg' in delivery:
                    raise UserError(_('Can not cancel when the parcel is processed'))
        except Exception as e:
            raise ValidationError(e)

    def back_grab(self):
        try:
            if self.state in ('cancel', 'failed'):
                self.state = 'draft'
                self.driver_name = None
                self.driver_phone = None
                self.license_plate = None
                self.delivery_reference = None
                self.delivery_fee = None
                self.track_url = None
                self.pickup_pin = None
                self.failed_reason = None
        except Exception as e:
            raise ValidationError(e)

    def action_call_delivery(self):
        try:
            partner_ahamove = self.env['delivery.partner'].sudo().search(
                [('code', '=', 'ahamove'), ('active', '=', True)], limit=1)
            partner_grab = self.env['delivery.partner'].sudo().search(
                [('code', '=', 'grab'), ('active', '=', True)], limit=1)
            ahamove_fee = False
            grab_fee = False
            if partner_ahamove:
                ahamove_fee = APIAhamove.get_api_fee_order_ahahmove(self, partner_ahamove)
            if partner_grab:
                grab_fee = APIGrab.get_delivery_quotes(self, partner_grab)
            if ahamove_fee and grab_fee:
                if grab_fee <= ahamove_fee:
                    self.delivery_partner_id = partner_grab
                    self.send_grab()
                else:
                    self.delivery_partner_id = partner_ahamove
                    self.send_ahamove()
            elif ahamove_fee and not grab_fee:
                self.delivery_partner_id = partner_ahamove
                self.send_ahamove()
            elif not ahamove_fee and grab_fee:
                self.delivery_partner_id = partner_grab
                self.send_grab()
            else:
                return False
        except Exception as e:
            raise ValidationError(e)

    def send_ahamove(self):
        try:
            response = APIAhamove.create_order_ahamove(self)
            if not response:
                self.state = 'failed'
                self.failed_reason = _('An error occurred while pushing ahamove đơn')
            self.count_call_aha += 1
            self.delivery_reference = response.get('order_id')
            self.track_url = response.get('shared_link')
            self.delivery_fee = response.get('order').get('total_fee')
            # self.is_delivery_internal = True
            self.state_delivery = None
            self.failed_reason = None
            # update distance from order responsed
            self.distance = response.get('order').get('distance')
            self.state = 'waiting'
            return
        except Exception as e:
            raise ValidationError(e)

    def get_detail_ahamove(self):
        try:
            response = APIAhamove.get_order_detail(self)
            status = response.get('status')
            sub_status = response.get('path')[1].get('status') if response.get('path')[1].get('status') else ''
            status_type = response.get('sub_status') if response.get('sub_status') else ''
            driver_name = response.get('supplier_name')
            phone = response.get('supplier_id')
            state = self.set_state_ahamove(status, sub_status, status_type)
            self.state_delivery = status_type + ' | ' + status + ' | ' + sub_status
            self.driver_name = driver_name
            self.driver_phone = phone
            self.license_plate = phone
            if self.state != state:
                self.state = state
            self.state_delivery = status
            self.failed_reason = response.get('cancel_comment')
        except Exception as e:
            raise ValidationError(e)

    def set_state_ahamove(self, status, sub_status, status_type):
        try:
            state = self.state
            if status == 'ACCEPTED':
                state = 'pickup'
            elif status == 'IN PROCESS':
                state = 'delivering'
            elif status == 'COMPLETED' and sub_status == 'COMPLETED':
                state = 'done'
            # elif status == 'COMPLETED' and sub_status == 'FAILED' and status_type == 'BOARDED':
            #     state = 'cancel'
            elif status == 'COMPLETED' and sub_status == 'FAILED' and status_type == 'RETURNED':
                state = 'done'
            elif status == 'CANCELLED':
                state = 'failed'
                if self.is_internal_cancel:
                    state = 'cancel'
            return state
        except Exception as e:
            raise ValidationError(e)

    def cancel_ahamove(self):
        try:
            cancel = APIAhamove.cancel_order_api_ahamove(self)
            if cancel:
                self.state = 'cancel'
        except Exception as e:
            raise ValidationError(e)

    def back_ahamove(self):
        try:
            if self.state in ('cancel', 'failed'):
                self.track_url = None
                self.driver_name = None
                self.driver_phone = None
                self.state = 'draft'
        except Exception as e:
            raise ValidationError(e)

    def check_delivery(self):
        try:
            origin = self.search([('origin', '=', self.origin), ('id', '!=', self.id)], limit=1)
            if origin:
                raise UserError(_('You cannot submit a single origin with multiple deliveries'))
            if self.type_origin == 'transfer' and not self.company_id.x_call_ship:
                if not self.delivery_partner_id or not self.delivery_partner_id.internal:
                    raise UserError(_('The system does not allow calling to ship outside'))
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            res = super(DeliveryManagement, self).create(vals)
            month = date.today().month
            year = date.today().year
            day = date.today().day
            prefix = f'HOMEFARM-{year % 100}{month:02d}{day:02d}/'
            seq = self.env['ir.sequence'].next_by_code('delivery.management')
            res.name = f'{prefix}{seq}'
            return res
        except Exception as e:
            raise ValidationError(e)

    def unlink(self):
        try:
            if self.state not in ('draft', 'cancel'):
                raise UserError(_('You can delete with state is draft or cancel'))
            return super(DeliveryManagement, self).unlink()
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('name', operator, name)]
        access_delivery = []

        # Check user root
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group(
                'base.group_system') or self.env.user.x_view_all_shop:
            warehouse_ids = self._search(domain + args + access_delivery, limit=limit, access_rights_uid=name_get_uid)
            return self.browse(warehouse_ids).name_get()

        delivery_ids = self.env['delivery.management'].sudo().search(
            [('store_id', 'in', self.env.user.x_pos_shop_ids.ids)])
        if delivery_ids:
            access_delivery = [('id', 'in', delivery_ids.ids)]

        delivery_ids = self._search(domain + args + access_delivery, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(delivery_ids).name_get()

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.uid == SUPERUSER_ID or self.env.user.has_group(
                'base.group_system') or self.env.user.x_view_all_shop:
            domain = domain
        else:
            delivery_ids = self.env['delivery.management'].sudo().search(
                [('store_id', 'in', self.env.user.x_pos_shop_ids.ids)])
            ids = delivery_ids.ids
            domain_delivery = []
            domain_delivery.append('id')
            if len(ids) == 1:
                domain_delivery.append('=')
                listToStr = ' '.join(map(str, ids))
                delivery_id = int(listToStr)
                domain_delivery.append(delivery_id)
            else:
                domain_delivery.append('in')
                domain_delivery.append(ids)
            domain.append(domain_delivery)
        return super(DeliveryManagement, self).search_read(domain, fields, offset, limit, order)
