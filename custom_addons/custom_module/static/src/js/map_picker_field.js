/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class MapPickerWidget extends Component {
    static template = "custom_module.MapPickerWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.mapRef = useRef("mapContainer");
        this.state = useState({
            latitude: this.props.record.data.latitude || -6.2,
            longitude: this.props.record.data.longitude || 106.8,
        });

        onMounted(() => {
            this.initializeMap();
        });
    }

    initializeMap() {
        const mapContainer = this.mapRef.el;
        if (!mapContainer || !window.L) {
            console.error("Map container or Leaflet not found");
            return;
        }

        // Initialize map
        this.map = window.L.map(mapContainer, {
            zoomControl: true,
            scrollWheelZoom: true
        }).setView([this.state.latitude, this.state.longitude], 13);

        // Add tile layer
        window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add existing marker if coordinates exist
        if (this.state.latitude && this.state.longitude) {
            this.marker = window.L.marker([this.state.latitude, this.state.longitude])
                .addTo(this.map)
                .bindPopup(`Lat: ${this.state.latitude.toFixed(6)}<br>Lng: ${this.state.longitude.toFixed(6)}`)
                .openPopup();
        }

        // Add click handler for map
        this.map.on('click', (e) => {
            this.onMapClick(e);
        });

        // Add geolocation control
        this.addGeolocationControl();
    }

    onMapClick(e) {
        const { lat, lng } = e.latlng;

        // Update state
        this.state.latitude = lat;
        this.state.longitude = lng;

        // Update marker
        if (this.marker) {
            this.marker.setLatLng(e.latlng);
        } else {
            this.marker = window.L.marker(e.latlng).addTo(this.map);
        }

        // Update popup
        this.marker.bindPopup(`Lat: ${lat.toFixed(6)}<br>Lng: ${lng.toFixed(6)}`).openPopup();

        // Update Odoo fields
        this.updateOdooFields(lat, lng);
    }

    updateOdooFields(lat, lng) {
        // Update latitude field
        this.props.record.update({
            latitude: lat,
            longitude: lng,
        });
    }

    onLatitudeChange(ev) {
        const lat = parseFloat(ev.target.value);
        if (!isNaN(lat) && lat >= -90 && lat <= 90) {
            this.state.latitude = lat;
            this.updateMapFromInputs();
        }
    }

    onLongitudeChange(ev) {
        const lng = parseFloat(ev.target.value);
        if (!isNaN(lng) && lng >= -180 && lng <= 180) {
            this.state.longitude = lng;
            this.updateMapFromInputs();
        }
    }

    updateMapFromInputs() {
        if (this.map && this.state.latitude && this.state.longitude) {
            const latlng = [this.state.latitude, this.state.longitude];

            // Update map view
            this.map.setView(latlng, this.map.getZoom());

            // Update marker
            if (this.marker) {
                this.marker.setLatLng(latlng);
            } else {
                this.marker = window.L.marker(latlng).addTo(this.map);
            }

            // Update popup
            this.marker.bindPopup(`Lat: ${this.state.latitude.toFixed(6)}<br>Lng: ${this.state.longitude.toFixed(6)}`).openPopup();

            // Update Odoo fields
            this.updateOdooFields(this.state.latitude, this.state.longitude);
        }
    }

    addGeolocationControl() {
        // Add geolocation button
        const GeolocationControl = window.L.Control.extend({
            onAdd: () => {
                const container = window.L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                container.style.backgroundColor = 'white';
                container.style.width = '30px';
                container.style.height = '30px';
                container.style.cursor = 'pointer';
                container.innerHTML = '<i class="fa fa-location-arrow" style="margin: 5px;"></i>';

                container.onclick = () => {
                    this.getCurrentLocation();
                };

                return container;
            },
        });

        this.map.addControl(new GeolocationControl({ position: 'topleft' }));
    }

    getCurrentLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                this.state.latitude = lat;
                this.state.longitude = lng;

                const latlng = [lat, lng];
                this.map.setView(latlng, 16);

                if (this.marker) {
                    this.marker.setLatLng(latlng);
                } else {
                    this.marker = window.L.marker(latlng).addTo(this.map);
                }

                this.marker.bindPopup(`Current Location<br>Lat: ${lat.toFixed(6)}<br>Lng: ${lng.toFixed(6)}`).openPopup();
                this.updateOdooFields(lat, lng);
            }, (error) => {
                console.error("Geolocation error:", error);
                alert("Unable to get current location. Please check your browser settings.");
            });
        }
    }

    clearLocation() {
        this.state.latitude = 0;
        this.state.longitude = 0;

        if (this.marker) {
            this.map.removeLayer(this.marker);
            this.marker = null;
        }

        this.updateOdooFields(0, 0);
    }

    centerOnLocation() {
        if (this.state.latitude && this.state.longitude) {
            this.map.setView([this.state.latitude, this.state.longitude], 16);
            if (this.marker) {
                this.marker.openPopup();
            }
        }
    }
}

// Register the widget
registry.category("fields").add("map_picker_v2", MapPickerWidget);