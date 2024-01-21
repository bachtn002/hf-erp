odoo.define("widget_google_maps", function (require) {
    "use strict";

    var Widget = require("web.Widget");
    var widgetRegistry = require("web.widget_registry");

    var map = {};
    var GMapMarker = {};

    GMapMarker = Widget.extend({
        jsLibs: [],
        template: "ev_gmap_marker",
        custom_events:{
            change_pos_config: '_onMyCustomEvent'
        },

        _onMyCustomEvent: function (ev) {
            console.log('event triggred', ev.data)
        },

        init: function (view, record, node) {
            this._super.apply(this, arguments);

            this.field_lat = node.attrs.lat;
            this.field_lng = node.attrs.lng;
            this.shown = $.Deferred();
            this.data = record.data;
            this.mode = view.mode || "readonly";
            this.record = record;
            this.view = view;
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (typeof google !== "object" || typeof google.maps !== "object") {
                    self._rpc({
                        route: "/google_maps/google_maps_api_key",
                    }).then(function (data) {
                        var data_json = JSON.parse(data);
                        self.key = data_json.google_maps_api_key;
                        var google_url = "https://maps.googleapis.com/maps/api/js?key=" + self.key;
                        window.google_on_ready = self.on_ready;
                        $.getScript(google_url + "&callback=google_on_ready&libraries=places");
                    });
                }
            });
        },

        start: function () {
            var self = this;
            return this._super().then(function () {
                if (typeof google === "object") {
                    self.on_ready();
                }
            });
        },

        get_condition_searchbox: async function () {
            return await this._rpc({
                model: this.record.model,
                method: 'get_condition_searchbox',
                args: [[this.record.data['id']]]
            })
        },


        on_ready: async function () {
            var self = this;
            //add event listener for search box
            const input_navigate = this.$el[0];
            const input = this.$el[2];
            //if record allow search address
            if (this.record.data['id']) {
                var get_condition = await self.get_condition_searchbox();
                if (!get_condition) {
                    if(document.getElementById("pac-input")){
                        document.getElementById("pac-input").style.setProperty('display', 'none')
                    }
                    if(document.getElementById("input_navigate")){
                        document.getElementById("input_navigate").style.setProperty('display', 'none')
                    }
                }
            }
            // Create the search box and link it to the UI element.
            const searchBox = new google.maps.places.SearchBox(input);
            input_navigate.addEventListener("keyup", function (evt) {
                var charCode = evt.keyCode || evt.which;

                //use enter key to call autocomplete service to get address suggestion
                if (charCode === 13) {
                    input.value = input_navigate.value;
                    input.focus();
                } else {
                    input.value = "";
                    input.focus();
                    input_navigate.focus();
                }
            });

            // navigate between 2 inputs
            input.addEventListener("keydown", function (evt) {
                var charCode = evt.keyCode || evt.which;

                // enter, up, down
                if (![13, 38, 40].includes(charCode)) {
                    input_navigate.focus();
                }

                // right, left
                if ([37, 39].includes(charCode)) {
                    input_navigate.focus();
                }

                // up, down
                if ([38, 40].includes(charCode)) {
                    evt.preventDefault();
                }
            });

            input.addEventListener("keyup", function (evt) {
                input_navigate.value = input.value;
            })

            //get lat long default based on shop
            var lat = this.data[this.field_lat];
            var long = this.data[this.field_lng];
            var x_lat_long = document.getElementsByName("is_pos_config_changed")[0]
            if (x_lat_long && !lat) {
                let lat_long_parts = x_lat_long.innerText.split(',')
                lat = lat_long_parts[0] || 20.99738757010727;
                long = lat_long_parts[1] || 105.8191792201073;
            }

            var myLatlng = new google.maps.LatLng(lat, long);

            var mapOptions = {
                zoom: 15,
                center: myLatlng,
                mapTypeId: "roadmap",
            };

            var div_gmap = this.$el[4];
            map = new google.maps.Map(div_gmap, mapOptions);

            this.marker = new google.maps.Marker({
                position: myLatlng,
                map: map,
                draggable: this.mode === "edit",
            });

            //Listen config changes
            $('span[name="is_pos_config_changed"]').on('DOMSubtreeModified', function () {
                var x_lat_long = document.getElementsByName("is_pos_config_changed")[0]
                if (x_lat_long) {
                    let lat_long_parts = x_lat_long.innerText.split(',')
                    var lat = lat_long_parts[0] || 0;
                    var lng = lat_long_parts[1] || 0;
                    var latlngPos = new google.maps.LatLng(lat, lng);
                    self.marker.setPosition(latlngPos);
                    map.panTo(latlngPos);
                    self.marker.setMap(map);
                }
            })

            map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
            map.controls[google.maps.ControlPosition.TOP_LEFT].push(input_navigate);
            map.addListener("bounds_changed", () => {
                searchBox.setBounds(map.getBounds());
            });

            let markers = [];

            searchBox.addListener("places_changed", () => {
                const places = searchBox.getPlaces();

                if (places.length === 0) {
                    return;
                }

                markers.forEach((marker) => {
                    marker.setMap(null);
                });
                markers = [];

                const bounds = new google.maps.LatLngBounds();
                var lat;
                var long;
                var address;

                places.forEach((place) => {
                    if (!place.geometry || !place.geometry.location) {
                        return;
                    }
                    // place.icon
                    const icon = {
                        url: '/ev_google_maps_widget/static/src/image/icon_maps.png',
                        // size: new google.maps.Size(71, 71),
                        origin: new google.maps.Point(0, 0),
                        anchor: new google.maps.Point(17, 34),
                        scaledSize: new google.maps.Size(50, 50),
                    };

                    markers.push(
                        new google.maps.Marker({
                            map,
                            icon,
                            title: place.name,
                            position: place.geometry.location,
                        })
                    );
                    address = place.formatted_address
                    lat = place.geometry.location.lat();
                    long = place.geometry.location.lng();
                    if (place.geometry.viewport) {
                        bounds.union(place.geometry.viewport);
                    } else {
                        bounds.extend(place.geometry.location);
                    }

                });
                map.fitBounds(bounds);
                var changes = {
                    x_pos_lat: lat,
                    x_pos_long: long,
                    address_delivery: input.value
                }
                this.update_latlng(changes);
                // update maps marker when save changes
                this.view.on("field_changed:" + this.field_lat, this, this.display_result);
                this.view.on("field_changed:" + this.field_lng, this, this.display_result);
                $("input[name='address_delivery']").val(input.value)
                $(input_navigate).val(input.value)
                $("input[name='x_pos_lat']").val(lat)
                $("input[name='x_pos_long']").val(long)
            })
        },

        update_latlng: function (vals_changes) {
            if(this.record.model === 'sale.online'){
                this.data['address_delivery'] = vals_changes['address_delivery'];
            }else{
                 delete vals_changes['address_delivery']
            }
            this.data['x_pos_lat'] = vals_changes['x_pos_lat'];
            this.data['x_pos_long'] = vals_changes['x_pos_long'];



            var def = $.Deferred();

            this.trigger_up("field_changed", {
                dataPointID: this.record.id,
                changes: vals_changes,
                onSuccess: def.resolve.bind(def),
                onFailure: def.reject.bind(def),
            });
        },

        display_result: function () {
            var lat = this.data[this.field_lat];
            var lng = this.data[this.field_lng];
            var myLatlng = new google.maps.LatLng(lat, lng);
            map.setCenter(myLatlng);
            this.marker.setPosition(myLatlng);
            google.maps.event.trigger(map, "resize");
        },
    });

    widgetRegistry.add("ev_gmap_marker", GMapMarker);


    return {
        ev_gmap_marker: GMapMarker,
    };
});
