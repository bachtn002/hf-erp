function initMapPos() {
    var show = $("#x_home_delivery")[0]
    // console.log(show)
    if (show.checked){
        $("#map_in_pos").show();
        $("#div_ship_type").show();
        $("#x_ship_type").show();
        $("#x_ship_distance").show();
    }
    show.onclick = function () {
        if (show.checked){
            $("#map_in_pos").show();
            $("#div_ship_type").show();
            $("#x_ship_type").show();
            $("#x_ship_distance").show();
        }else {
            $("#map_in_pos").hide();
            $("#div_ship_type").hide();
            $("#x_ship_type").hide();
            $("#x_ship_distance").hide();
        }
    };

    // get shop lat - lon
    var shop_lat = parseFloat($('#shop_lat')[0].value);
    var shop_long = parseFloat($('#shop_long')[0].value);
    if(!shop_lat || !shop_long){
        document.getElementById('home_delivery').style.setProperty('display', 'none')
        // Case can't get shop lat - long then use company location by default
        shop_lat = 20.99738757010727;
        shop_long = 105.8191792201073;
    }

    var latLng = {
        lat: shop_lat,
        lng: shop_long,
    }

    const map = new google.maps.Map(document.getElementById("map_pos"), {
        center: latLng,
        zoom: 15,
        mapTypeId: "roadmap",
    });
    new google.maps.Marker({
        position: latLng,
        map,
    });
    const input = document.getElementById("pac-input");
    const input_navigate = document.getElementById("input_navigate");
    const searchBox = new google.maps.places.SearchBox(input);
    input_navigate.addEventListener("keyup", function (evt) {
        var charCode = evt.keyCode || evt.which;

        if (charCode === 13) {
            input.value = input_navigate.value;
            input.focus();
        } else {
            input.value = "";
            input.focus();
            input_navigate.focus();
        }
    });

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
            lat = place.geometry.location.lat();
            long = place.geometry.location.lng();
            if (place.geometry.viewport) {
                bounds.union(place.geometry.viewport);

            } else {
                bounds.extend(place.geometry.location);
            }

        });
        if(!lat || !long || !address){
            alert("Could not connect to the Google API, please check your internet connection and try again.");
        }else{
            document.getElementsByName("x_lat")[0].innerText = lat
            document.getElementsByName("x_long")[0].innerText = long
            document.getElementsByName("x_address_delivery")[0].innerText = input.value
            //assigned back value to input navigation when user click on suggestion item
            $(input_navigate).val(input.value)
            // call google distance api instead of call back to server
            const address_1 = $('#shop_address')[0].value;
            const address_2 = $('#x_address_delivery')[0].innerHTML;

            if(address_1 !== "" && address_2 !== ""){
                //Find the distance
                var originA = new google.maps.LatLng(shop_lat, shop_long);
                var destinationB = new google.maps.LatLng(lat, long);
                var distanceService = new google.maps.DistanceMatrixService();// instantiate Distance Matrix service
                const matrixOptions = {
                    origins: [originA],
                    destinations: [destinationB],
                    travelMode: google.maps.TravelMode.DRIVING,
                    unitSystem: google.maps.UnitSystem.METRIC,
                    durationInTraffic: true,
                    avoidHighways: false,
                    avoidTolls: false
                }
                // Call Distance Matrix service
                distanceService.getDistanceMatrix(matrixOptions, callback);

                // Callback function used to process Distance Matrix response
                function callback(response, status) {
                    if (status !== "OK") {
                        alert("Không thể tính khoảng cách - " + status);
                        document.getElementsByName("x_ship_distance")[0].innerText = ''
                    }
                    else{
                        if (!response.rows[0].elements[0].distance){
                            alert("Không thể tính khoảng cách - " + response.rows[0].elements[0].status) ;
                            document.getElementsByName("x_ship_distance")[0].innerText = ''
                        }else{
                            //convert m to km and get format a number with 1 decimals
                            var distance = (response.rows[0].elements[0].distance.value / 1000).toFixed(1)
                            document.getElementsByName("x_ship_distance")[0].innerText = distance
                                $("#x_ship_distance").text(distance).show();
                        }
                    }
                }
            }
        }
        map.fitBounds(bounds);
    })
}

