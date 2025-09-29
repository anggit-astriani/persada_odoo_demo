/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class CustomerMapDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.mapRef = useRef("mapContainer");

        this.state = useState({
            loading: true,
            customerCount: 0,
            errorMessage: null,
        });

        window.customerMapDashboard = {
            openCustomerForm: (id) => this.openCustomerForm(id),
        };

        onMounted(async () => {
            await this.loadLeafletAndInitialize();
        });

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
            }
            delete window.customerMapDashboard;
        });
    }

    async loadLeafletAndInitialize() {
        try {
            if (!window.L) {
                await loadJS("https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.js");
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.css';
                document.head.appendChild(link);
            }

            if (!window.L.markerClusterGroup) {
                try {
                    await loadJS("https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.4.1/leaflet.markercluster.min.js");
                    const clusterCSS = document.createElement('link');
                    clusterCSS.rel = 'stylesheet';
                    clusterCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.4.1/MarkerCluster.Default.min.css';
                    document.head.appendChild(clusterCSS);
                } catch (e) {
                    console.warn("MarkerCluster plugin not loaded:", e);
                }
            }

            await this.initializeMapDashboard();
        } catch (error) {
            console.error("Error loading Leaflet:", error);
            this.state.errorMessage = "Failed to load map components";
            this.state.loading = false;
        }
    }

    async initializeMapDashboard() {
        const mapContainer = this.mapRef.el;
        if (!mapContainer || !window.L) {
            console.error("Map container or Leaflet not found");
            this.state.errorMessage = "Map container not available";
            this.state.loading = false;
            return;
        }

        try {
            this.map = window.L.map(mapContainer, {
                center: [-2.5, 118.0],
                zoom: 5,
                zoomControl: true,
                scrollWheelZoom: true,
                doubleClickZoom: true,
                dragging: true,
            });

            window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.map);

            const loadingControl = window.L.control({ position: 'topright' });
            loadingControl.onAdd = () => {
                const div = window.L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                div.innerHTML = '<div id="map-loading" style="padding: 5px; background: white; display: none;"><i class="fa fa-spinner fa-spin"></i> Loading...</div>';
                return div;
            };
            loadingControl.addTo(this.map);

            await this.loadCustomerData();
            this.state.loading = false;
            this.addRefreshControl();
        } catch (error) {
            console.error("Error initializing map dashboard:", error);
            this.state.errorMessage = error.message || "Failed to initialize map";
            this.state.loading = false;
            this.notification.add("Failed to load map dashboard", { type: "danger" });
        }
    }

    async loadCustomerData() {
        const loadingDiv = document.getElementById('map-loading');
        if (loadingDiv) loadingDiv.style.display = 'block';

        try {
            const records = await this.orm.searchRead(
                "stock.picking",
                [
                    ['active', '=', true],
                    '|',
                    '&', ['delivered_latitude', '!=', false], ['delivered_longitude', '!=', false],
                    '&', ['delivered_latitude', '!=', 0], ['delivered_longitude', '!=', 0]
                ],
                ["id", "name", "street", "street2", "city", "state_id", "country_id",
                 "delivered_latitude", "delivered_longitude", "location_display", "active"]
            );

            if (!records || records.length === 0) {
                this.notification.add("No customer locations found. Please add some customers with coordinates.", { type: "info" });
                this.state.customerCount = 0;
                return;
            }

            this.state.customerCount = records.length;

            let markers = window.L.markerClusterGroup
                ? window.L.markerClusterGroup({ chunkedLoading: true, maxClusterRadius: 50 })
                : window.L.layerGroup();

            const validMarkers = [];

            records.forEach((record) => {
                const marker = this.addCustomerMarker(record);
                if (marker) {
                    markers.addLayer(marker);
                    validMarkers.push([record.delivered_latitude, record.delivered_longitude]);
                }
            });

            if (markers.getLayers && markers.getLayers().length > 0) {
                this.map.addLayer(markers);
                if (validMarkers.length > 0) {
                    const group = new window.L.featureGroup(markers.getLayers());
                    this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
                }
                this.notification.add(
                    `Successfully loaded ${validMarkers.length} customer location${validMarkers.length !== 1 ? 's' : ''}`,
                    { type: "success" }
                );
            } else {
                this.notification.add("No valid customer coordinates found", { type: "warning" });
            }
        } catch (error) {
            console.error("Error loading customer data:", error);
            this.state.errorMessage = "Failed to load customer data";
            this.notification.add(`Failed to load customer data: ${error.message}`, { type: "danger" });
        } finally {
            if (loadingDiv) loadingDiv.style.display = 'none';
        }
    }

    addCustomerMarker(record) {
        const lat = parseFloat(record.delivered_latitude);
        const lng = parseFloat(record.delivered_longitude);

        if (isNaN(lat) || isNaN(lng)) {
            console.warn(`Invalid coordinates for ${record.name}`);
            return null;
        }
        if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
            console.warn(`Out of range coordinates for ${record.name}`);
            return null;
        }

        const iconHtml = `
            <div style="
                background-color: ${record.active ? '#1f77b4' : '#6c757d'};
                border: 3px solid white;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                color: white;
                font-weight: bold;
                font-size: 14px;
            ">
                ${record.name.charAt(0).toUpperCase()}
            </div>
        `;

        const customIcon = window.L.divIcon({
            className: 'custom-customer-marker',
            html: iconHtml,
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });

        const marker = window.L.marker([lat, lng], {
            icon: customIcon,
            title: record.name
        });

        const popupContent = `
            <div class="customer-popup" style="min-width: 250px;">
                <h4 style="margin: 0 0 15px 0; color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 8px;">
                    <i class="fa fa-user" style="margin-right: 8px;"></i>${record.name}
                </h4>
                <p style="margin: 8px 0;"><strong><i class="fa fa-map-marker"></i> Coordinates:</strong><br>
                ${lat.toFixed(6)}, ${lng.toFixed(6)}</p>
                <p style="margin: 8px 0;"><strong>Status:</strong>
                <span class="badge ${record.active ? 'badge-success' : 'badge-secondary'}">
                    ${record.active ? 'Active' : 'Inactive'}
                </span></p>
                <div style="margin-top: 15px; text-align: center;">
                    <button onclick="window.customerMapDashboard.openCustomerForm(${record.id})"
                            class="btn btn-primary btn-sm" style="margin-right: 5px;">
                        <i class="fa fa-edit"></i> Edit
                    </button>
                    <button onclick="window.open('https://www.google.com/maps?q=${lat},${lng}', '_blank')"
                            class="btn btn-secondary btn-sm">
                        <i class="fa fa-external-link"></i> Google Maps
                    </button>
                </div>
            </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 300, className: 'customer-popup-container' });
        return marker;
    }

    addRefreshControl() {
        const refreshControl = window.L.control({ position: 'topright' });
        refreshControl.onAdd = () => {
            const div = window.L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
            div.innerHTML = `
                <a href="#" title="Refresh Data" style="
                    background: white;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                    color: #333;
                    border-radius: 2px;
                ">
                    <i class="fa fa-refresh"></i>
                </a>
            `;
            div.onclick = (e) => {
                e.preventDefault();
                this.refreshData();
            };
            return div;
        };
        refreshControl.addTo(this.map);
    }

    async openCustomerForm(customerId) {
        try {
            await this.action.doAction({
                name: "Customer Details",
                type: "ir.actions.act_window",
                res_model: "stock.picking",
                res_id: customerId,
                view_mode: "form",
                view_type: "form",
                views: [[false, "form"]],
                target: "current",
            });
        } catch (error) {
            console.error("Error opening customer form:", error);
            this.notification.add("Failed to open customer form", { type: "danger" });
        }
    }

    async refreshData() {
        this.state.loading = true;
        try {
            this.map.eachLayer((layer) => {
                if (layer instanceof window.L.MarkerClusterGroup ||
                    layer instanceof window.L.LayerGroup ||
                    layer instanceof window.L.Marker) {
                    this.map.removeLayer(layer);
                }
            });
            await this.loadCustomerData();
            this.notification.add("Map data refreshed successfully", { type: "success" });
        } catch (error) {
            console.error("Error refreshing data:", error);
            this.notification.add("Failed to refresh data", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async addNewCustomer() {
        try {
            await this.action.doAction({
                name: "New Customer",
                type: "ir.actions.act_window",
                res_model: "stock.picking",
                view_mode: "form",
                view_type: "form",
                views: [[false, "form"]],
                target: "current",
            });
        } catch (error) {
            console.error("Error creating new customer:", error);
            this.notification.add("Failed to create new customer", { type: "danger" });
        }
    }
}

CustomerMapDashboard.template = "custom_module.CustomerMapDashboard";
registry.category("actions").add("custom_module.map_dashboard", CustomerMapDashboard);
