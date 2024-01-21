function initAutocomplete() {

    var lat = 20.99738757010727;
    var long = 105.8191792201073;

    document.getElementById("pac-input").addEventListener('click', updateLatLongPos)

    if (Number(document.getElementsByName("lat")[0].innerText)) {
        lat = Number(document.getElementsByName("lat")[0].innerText);

    }
    if (Number(document.getElementsByName("long")[0].innerText)) {
        long = Number(document.getElementsByName("long")[0].innerText);
    }

    var latLng = {
        lat: lat,
        lng: long,
    }

    var map = new google.maps.Map(document.getElementById("map"), {
        center: latLng,
        zoom: 15,
        mapTypeId: "roadmap",
    });
    var mark = new google.maps.Marker({
        position: latLng,
        map,
    });

    function updateLatLongPos() {
        var x_lat = document.getElementsByName("x_pos_lat")[0]
        var x_long = document.getElementsByName("x_pos_long")[0]

        if (x_lat) {
            lat = Number(x_lat.innerText)
            long = Number(x_long.innerText)
            if (!document.getElementsByName("lat")[0].innerText) {
                var latlngPos = new google.maps.LatLng(lat, long);
                mark.setPosition(latlngPos);
                map.panTo(latlngPos);
                mark.setMap(map);
            }
        }
    }

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
            lat = place.geometry.location.lat();
            long = place.geometry.location.lng();
            if (place.geometry.viewport) {
                bounds.union(place.geometry.viewport);

            } else {
                bounds.extend(place.geometry.location);

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
        if (id && model) {
            $.ajax({
                type: "POST",
                dataType: 'json',
                url: '/maps/lat_long',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({
                    'jsonrpc': "2.0",
                    'method': "call",
                    "params": { 'id': id, 'model': model, 'lat': lat, 'long': long, 'address': address }
                }),
                // success: function() {
                //     document.getElementsByName("lat")[0].innerText = lat
                //     document.getElementsByName("long")[0].innerText = long
                //     document.getElementsByName("lat")[0].value = lat
                //     document.getElementsByName("long")[0].value = long
                //     document.getElementsByName("lat")[0].innerHTML = lat
                //     document.getElementsByName("long")[0].innerHTML = long
                // },
            });
            setTimeout(window.location.reload(), 200000)
        }


    });
}
