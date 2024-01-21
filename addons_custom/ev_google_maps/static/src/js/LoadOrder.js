odoo.define('ev_google_maps.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models("pos.order", ['x_home_delivery', 'x_address_delivery', 'x_lat', 'x_long', 'x_ship_type','x_ship_note','x_partner_phone','x_receiver','x_cod','x_distance']);

    var OrderSupper = models.Order;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            // console.log(options)
            this.x_home_delivery = options.x_home_delivery || '';
            this.x_address_delivery = options.x_address_delivery || '';
            this.x_lat = options.x_lat || '';
            this.x_long = options.x_long || '';
            this.x_ship_type = options.x_ship_type || '';
            this.x_ship_note = options.x_ship_note || '';
            this.x_partner_phone = options.x_partner_phone || '';
            this.x_receiver = options.x_receiver || '';
            this.x_cod = options.x_cod || '';
            this.x_distance = options.x_distance || '';
            OrderSupper.prototype.initialize.apply(this, arguments);
            return this;
        },
        init_from_JSON: function (json) {
            // console.log(json)
            this.x_home_delivery = json.x_home_delivery;
            this.x_address_delivery = json.x_address_delivery;
            this.x_lat = json.x_lat;
            this.x_long = json.x_long;
            this.x_ship_type = json.x_ship_type;
            this.x_ship_note = json.x_ship_note;
            this.x_partner_phone = json.x_partner_phone;
            this.x_receiver = json.x_receiver;
            this.x_cod = json.x_cod;
            this.x_distance = json.x_distance;
            OrderSupper.prototype.init_from_JSON.call(this, json);
        },
        export_as_JSON: function () {
            var data = OrderSupper.prototype.export_as_JSON.apply(this, arguments);
            data.x_home_delivery = this.get_x_home_delivery();
            data.x_address_delivery = this.get_x_address_delivery();
            data.x_lat = this.get_x_lat();
            data.x_long = this.get_x_long();
            data.x_ship_type = this.get_x_ship_type();
            data.x_ship_note = this.get_x_ship_note();
            data.x_partner_phone = this.get_x_partner_phone();
            data.x_receiver = this.get_x_receiver();
            data.x_cod = this.get_x_cod();
            data.x_distance = this.get_x_distance();
            return data;
        },
        export_for_printing: function () {
            let res = OrderSupper.prototype.export_for_printing.apply(this, arguments);
            res.x_home_delivery = this.get_x_home_delivery();
            res.x_address_delivery = this.get_x_address_delivery();
            res.x_lat = this.get_x_lat();
            res.x_long = this.get_x_long();
            res.x_ship_type = this.get_x_ship_type();
            res.x_ship_note = this.get_x_ship_note();
            res.x_partner_phone = this.get_x_partner_phone();
            res.x_receiver = this.get_x_receiver();
            res.x_cod = this.get_x_cod();
            res.x_distance = this.get_x_distance();
            return res;
        },
        set_x_home_delivery: function (x_home_delivery) {
            this.x_home_delivery = x_home_delivery;
        },
        set_x_address_delivery: function (x_address_delivery) {
            this.x_address_delivery = x_address_delivery;
        },
        set_x_lat: function (x_lat) {
            this.x_lat = x_lat;
        },
        set_x_long: function (x_long) {
            this.x_long = x_long;
        },
        set_x_ship_type: function (x_ship_type) {
            this.x_ship_type = x_ship_type;
        },
        set_x_ship_note: function (x_ship_note) {
            this.x_ship_note = x_ship_note;
        },
        set_x_partner_phone: function (x_partner_phone) {
            this.x_partner_phone = x_partner_phone;
        },
        set_x_receiver: function (x_receiver) {
            this.x_receiver = x_receiver;
        },
        set_x_cod: function (x_cod) {
            this.x_cod = x_cod;
        },
        set_x_distance: function (x_distance) {
            this.x_distance = x_distance;
        },

        get_x_home_delivery: function () {
            return this.x_home_delivery;
        },
        get_x_address_delivery: function () {
            return this.x_address_delivery;
        },
        get_x_lat: function () {
            return this.x_lat;
        },
        get_x_long: function () {
            return this.x_long;
        },
        get_x_ship_type: function () {
            return this.x_ship_type;
        },
        get_x_ship_note: function () {
            return this.x_ship_note;
        },
        get_x_partner_phone: function () {
            return this.x_partner_phone;
        },
        get_x_receiver: function () {
            return this.x_receiver;
        },
        get_x_cod: function () {
            return this.x_cod;
        },
        get_x_distance: function () {
            return this.x_distance;
        },
    });

    //Load pos.shop domain based on session related
    models.load_fields('pos.session',['x_pos_shop_id']);
    models.load_models([{

        model:  'pos.shop',
        fields: ['id', 'name', 'lat', 'long', 'address'],
        domain: function(self){
            return self.pos_session.id
                ? [['id', '=', self.pos_session.x_pos_shop_id[0]]]
                : [['id', 'in', []]];
        },
        loaded: function(self, shops) {
            if(shops.length > 0) {
                self.shop_address = shops[0].address
                self.shop_lat = shops[0].lat
                self.shop_long = shops[0].long
            }
        }
    }], {after: 'pos.session'});

});
