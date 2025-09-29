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

        // Expose method for popup buttons
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
            // Clean up global reference
            delete window.customerMapDashboard;
        });
    }

    async loadLeafletAndInitialize() {
        try {
            // Load Leaflet if not already loaded
            if (!window.L) {
                await loadJS("https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.js");

                // Also load Leaflet CSS
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.min.css';
                document.head.appendChild(link);
            }

            // Load MarkerCluster plugin if available
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
            // Initialize map centered on Indonesia
            this.map = window.L.map(mapContainer, {
                center: [-2.5, 118.0], // Center of Indonesia
                zoom: 5,
                zoomControl: true,
                scrollWheelZoom: true,
                doubleClickZoom: true,
                dragging: true,
            });

            // Add tile layer with proper attribution
            window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                maxZoom: 19,
                attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.map);

            // Add loading control
            const loadingControl = window.L.control({ position: 'topright' });
            loadingControl.onAdd = () => {
                const div = window.L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                div.innerHTML = '<div id="map-loading" style="padding: 5px; background: white; display: none;"><i class="fa fa-spinner fa-spin"></i> Loading...</div>';
                return div;
            };
            loadingControl.addTo(this.map);

            // Load and display customer data
            await this.loadCustomerData();

            this.state.loading = false;

            // Add refresh control
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
            // Use a safer domain that doesn't trigger PostGIS operator errors
            // Avoid using != with PostGIS geometry fields
            const records = await this.orm.searchRead(
                "customer.map",
                [
                    ['active', '=', true],
                    '|',
                    '&', ['latitude', '!=', false], ['longitude', '!=', false],
                    '&', ['latitude', '!=', 0], ['longitude', '!=', 0]
                ],
                ["id", "name", "description", "phone", "email", "latitude", "longitude", "location_display", "active"]
            );

            console.log("Loaded customer records:", records);

            if (!records || records.length === 0) {
                console.warn("No customer records found with location data");
                this.notification.add("No customer locations found. Please add some customers with coordinates.", { type: "info" });
                this.state.customerCount = 0;
                return;
            }

            this.state.customerCount = records.length;

            // Create marker group (with clustering if available)
            let markers;
            if (window.L.markerClusterGroup) {
                markers = window.L.markerClusterGroup({
                    chunkedLoading: true,
                    maxClusterRadius: 50,
                });
            } else {
                markers = window.L.layerGroup();
            }

            const validMarkers = [];

            // Add markers for each customer
            records.forEach((record, index) => {
                try {
                    const marker = this.addCustomerMarker(record);
                    if (marker) {
                        markers.addLayer(marker);
                        validMarkers.push([record.latitude, record.longitude]);
                    }
                } catch (error) {
                    console.error(`Error adding marker for customer ${record.name}:`, error);
                }
            });

            // Add marker group to map
            if (markers.getLayers && markers.getLayers().length > 0) {
                this.map.addLayer(markers);

                // Fit map bounds to show all markers with padding
                if (validMarkers.length > 0) {
                    const group = new window.L.featureGroup(markers.getLayers());
                    this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
                }

                // Show success notification
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

            // Fallback: Try to load without any PostGIS related filters
            try {
                console.log("Trying fallback query without PostGIS filters...");
                const fallbackRecords = await this.orm.searchRead(
                    "customer.map",
                    [('active', '=', true)],
                    ["id", "name", "description", "phone", "email", "latitude", "longitude", "location_display", "active"]
                );

                const validRecords = fallbackRecords.filter(record =>
                    record.latitude && record.longitude &&
                    parseFloat(record.latitude) !== 0 && parseFloat(record.longitude) !== 0
                );

                if (validRecords.length > 0) {
                    console.log(`Fallback found ${validRecords.length} valid records`);
                    await this.processFallbackRecords(validRecords);
                } else {
                    this.notification.add("No customers with valid coordinates found", { type: "info" });
                }
            } catch (fallbackError) {
                console.error("Fallback query also failed:", fallbackError);
                this.notification.add(`Failed to load customer data: ${error.message}`, { type: "danger" });
            }
        } finally {
            if (loadingDiv) loadingDiv.style.display = 'none';
        }
    }

    async processFallbackRecords(records) {
        this.state.customerCount = records.length;

        // Create marker group
        let markers;
        if (window.L.markerClusterGroup) {
            markers = window.L.markerClusterGroup({
                chunkedLoading: true,
                maxClusterRadius: 50,
            });
        } else {
            markers = window.L.layerGroup();
        }

        const validMarkers = [];

        // Add markers for each valid customer
        records.forEach((record) => {
            try {
                const marker = this.addCustomerMarker(record);
                if (marker) {
                    markers.addLayer(marker);
                    validMarkers.push([record.latitude, record.longitude]);
                }
            } catch (error) {
                console.error(`Error adding fallback marker for customer ${record.name}:`, error);
            }
        });

        // Add marker group to map
        if (markers.getLayers && markers.getLayers().length > 0) {
            this.map.addLayer(markers);

            // Fit map bounds to show all markers
            if (validMarkers.length > 0) {
                const group = new window.L.featureGroup(markers.getLayers());
                this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
            }

            this.notification.add(
                `Successfully loaded ${validMarkers.length} customer location${validMarkers.length !== 1 ? 's' : ''} (fallback mode)`,
                { type: "success" }
            );
        }
    }

    addCustomerMarker(record) {
        // Validate coordinates
        const lat = parseFloat(record.latitude);
        const lng = parseFloat(record.longitude);

        if (isNaN(lat) || isNaN(lng)) {
            console.warn(`Invalid coordinates for customer ${record.name}: lat=${record.latitude}, lng=${record.longitude}`);
            return null;
        }

        if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
            console.warn(`Out of range coordinates for customer ${record.name}: lat=${lat}, lng=${lng}`);
            return null;
        }

        try {
            // Create custom icon with FontAwesome or Unicode
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

            // Create marker
            const marker = window.L.marker([lat, lng], {
                icon: customIcon,
                title: record.name
            });

            // Create detailed popup content
            const popupContent = `
                <div class="customer-popup" style="min-width: 250px;">
                    <h4 style="margin: 0 0 15px 0; color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 8px;">
                        <i class="fa fa-user" style="margin-right: 8px;"></i>${record.name}
                    </h4>
                    ${record.description ? `
                        <p style="margin: 8px 0;"><strong>Description:</strong><br>
                        <span style="font-style: italic;">${record.description}</span></p>
                    ` : ''}
                    ${record.phone ? `
                        <p style="margin: 8px 0;"><strong><i class="fa fa-phone"></i> Phone:</strong>
                        <a href="tel:${record.phone}">${record.phone}</a></p>
                    ` : ''}
                    ${record.email ? `
                        <p style="margin: 8px 0;"><strong><i class="fa fa-envelope"></i> Email:</strong>
                        <a href="mailto:${record.email}">${record.email}</a></p>
                    ` : ''}
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

            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'customer-popup-container'
            });

            // Add click handler for additional functionality
            marker.on('click', () => {
                console.log(`Clicked customer: ${record.name} (ID: ${record.id})`);
            });

            return marker;

        } catch (error) {
            console.error(`Error creating marker for ${record.name}:`, error);
            return null;
        }
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
                res_model: "customer.map",
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
            // Clear existing layers except base tiles
            this.map.eachLayer((layer) => {
                if (layer instanceof window.L.MarkerClusterGroup ||
                    layer instanceof window.L.LayerGroup ||
                    layer instanceof window.L.Marker) {
                    this.map.removeLayer(layer);
                }
            });

            // Reload data
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
                res_model: "customer.map",
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

// Register the action
registry.category("actions").add("custom_module.map_dashboard", CustomerMapDashboard);