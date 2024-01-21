function initAutocomplete() {

    const map = new google.maps.Map(document.getElementById("map"), {
        center: {lat: 21.0282431, lng: 105.7807376},
        zoom: 13,
        mapTypeId: "roadmap",
    });
    const input = document.getElementById("pac-input");
    const searchBox = new google.maps.places.SearchBox(input);

    map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
    map.addListener("bounds_changed", () => {
        searchBox.setBounds(map.getBounds());
    });

    let markers = [];

    searchBox.addListener("places_changed", () => {
        const places = searchBox.getPlaces();

        if (places.length == 0) {
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
                console.log("Returned place contains no geometry");
                return;
            }
            const icon = {
                url: place.icon,
                size: new google.maps.Size(71, 71),
                origin: new google.maps.Point(0, 0),
                anchor: new google.maps.Point(17, 34),
                scaledSize: new google.maps.Size(25, 25),
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
            if (place.geometry.viewport) {
                bounds.union(place.geometry.viewport);
                lat = place.geometry.viewport.zb['h'];
                long = place.geometry.viewport.Ua['h'];

            } else {
                bounds.extend(place.geometry.location);
                var lat_b = place.geometry.location.lat;
                var long_b = place.geometry.location.lng;
            }

        });
        map.fitBounds(bounds);

        let href = window.location.href
        let url_parts = href.split('&')
        let id;
        let model;
        for (var i = 0; i < url_parts.length; i++) {
            if (url_parts[i].startsWith('id=') || url_parts[i].includes('#id=')) {
                id = url_parts[i].substring(url_parts[i].indexOf('id=') + 3)
            }
            if (url_parts[i].startsWith('model=')) {
                model = url_parts[i].substring(6)
            }
        }
        $.ajax({
            type: "POST",
            dataType: 'json',
            url: '/maps/lat_long',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                'jsonrpc': "2.0",
                'method': "call",
                "params": {'id': id, 'model': model, 'lat': lat, 'long': long, 'address': address}
            }),
        });
    });
}
