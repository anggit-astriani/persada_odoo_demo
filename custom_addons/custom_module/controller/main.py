# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class CustomerMapController(http.Controller):

    @http.route('/customer_map_tracking/customers_json', type='json', auth='user')
    def customers_json(self):
        """Return customer data in JSON format for JavaScript dashboard"""
        try:
            # Search for active customers with location data
            domain = [
                ('active', '=', True),
                '|', '|',
                ('shape', '!=', False),
                '&', ('delivered_latitude', '!=', False), ('delivered_longitude', '!=', False),
                '&', ('delivered_latitude', '!=', 0), ('delivered_longitude', '!=', 0)
            ]

            records = request.env['stock.picking'].sudo().search(domain)
            _logger.info(f"Found {len(records)} customer records with location data")

            data = []
            for record in records:
                try:
                    # Get coordinates from different sources
                    lat = lng = None

                    # First, try to get from PostGIS shape if available
                    if record.shape:
                        try:
                            # PostGIS coordinates
                            if hasattr(record.shape, 'coords') and len(record.shape.coords) >= 2:
                                lng, lat = float(record.shape.coords[0]), float(record.shape.coords[1])
                            elif hasattr(record.shape, 'x') and hasattr(record.shape, 'y'):
                                lng, lat = float(record.shape.x), float(record.shape.y)
                        except Exception as e:
                            _logger.warning(f"Error extracting PostGIS coordinates for {record.name}: {e}")

                    # Fallback to delivered_latitude/delivered_longitude fields
                    if lat is None or lng is None:
                        if record.delivered_latitude and record.delivered_longitude:
                            lat, lng = float(record.delivered_latitude), float(record.delivered_longitude)

                    # Validate coordinates
                    if lat is not None and lng is not None:
                        if -90 <= lat <= 90 and -180 <= lng <= 180:
                            records_data = {
                                'id': record.id,
                                'name': record.name,
                                'street': record.street,
                                'street2': record.street2,
                                'city': record.city,
                                'state_id': record.state_id.id if record.state_id else False,
                                'state_name': record.state_id.name if record.state_id else '',
                                'zip': record.zip,
                                'country_id': record.country_id.id if record.country_id else False,
                                'country_name': record.country_id.name if record.country_id else '',
                                'delivered_latitude': lat,
                                'delivered_longitude': lng,
                                'location_display': record.location_display or f"Lat: {lat:.6f}, Lng: {lng:.6f}",
                                'active': record.active,
                            }
                            data.append(records_data)
                            _logger.debug(f"Added customer: {record.name} at {lat}, {lng}")
                        else:
                            _logger.warning(f"Invalid coordinates for {record.name}: lat={lat}, lng={lng}")
                    else:
                        _logger.warning(f"No valid coordinates found for customer: {record.name}")

                except Exception as e:
                    _logger.error(f"Error processing customer {record.name}: {e}")
                    continue

            _logger.info(f"Returning {len(data)} customer locations")
            return {
                'success': True,
                'data': data,
                'count': len(data),
                'message': f'Found {len(data)} customer locations'
            }

        except Exception as e:
            _logger.error(f"Error in customers_json endpoint: {e}")
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': str(e),
                'message': 'Failed to load customer data'
            }

    @http.route('/customer_map_tracking/customer/<int:customer_id>', type='json', auth='user')
    def get_customer_single(self, customer_id):
        """Get single customer data"""
        try:
            record = request.env['stock.picking'].sudo().browse(customer_id)

            if not record.exists():
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'message': f'Customer with ID {customer_id} not found'
                }

            # Extract coordinates
            lat = lng = None
            if record.shape:
                try:
                    if hasattr(record.shape, 'coords') and len(record.shape.coords) >= 2:
                        lng, lat = float(record.shape.coords[0]), float(record.shape.coords[1])
                except:
                    pass

            if lat is None or lng is None:
                if record.delivered_latitude and record.delivered_longitude:
                    lat, lng = float(record.delivered_latitude), float(record.delivered_longitude)

            records_data = {
                'id': record.id,
                'name': record.name,
                'street': record.street,
                'street2': record.street2,
                'city': record.city,
                'state_id': record.state_id.id if record.state_id else False,
                'state_name': record.state_id.name if record.state_id else '',
                'zip': record.zip,
                'country_id': record.country_id.id if record.country_id else False,
                'country_name': record.country_id.name if record.country_id else '',
                'delivered_latitude': lat,
                'delivered_longitude': lng,
                'location_display': record.location_display,
                'active': record.active,
            }

            return {
                'success': True,
                'data': records_data,
                'message': f'Customer {record.name} retrieved successfully'
            }

        except Exception as e:
            _logger.error(f"Error getting customer {customer_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to get customer {customer_id}'
            }

    @http.route('/customer_map_tracking/customers_geojson', type='json', auth='user')
    def customers_geojson(self):
        """Return customer data in GeoJSON format"""
        try:
            # Get customers with coordinates - avoid PostGIS queries that cause errors
            domain = [
                ('active', '=', True),
                '&', ('delivered_latitude', '!=', False), ('delivered_longitude', '!=', False),
                '&', ('delivered_latitude', '!=', 0), ('delivered_longitude', '!=', 0)
            ]

            records = request.env['stock.picking'].sudo().search(domain)

            # If no records found, try all active customers and filter in Python
            if not records:
                all_records = request.env['stock.picking'].sudo().search([('active', '=', True)])
                records = [r for r in all_records if
                           r.delivered_latitude and r.delivered_longitude and float(r.delivered_latitude) != 0 and float(r.delivered_longitude) != 0]

            features = []

            for record in records:
                try:
                    # Get coordinates - prioritize lat/lng fields
                    lat = lng = None
                    if record.delivered_latitude and record.delivered_longitude:
                        lat, lng = float(record.delivered_latitude), float(record.delivered_longitude)

                    # Fallback to PostGIS if needed
                    if lat is None or lng is None:
                        if record.shape:
                            try:
                                if hasattr(record.shape, 'coords') and len(record.shape.coords) >= 2:
                                    lng, lat = float(record.shape.coords[0]), float(record.shape.coords[1])
                            except:
                                pass

                    if lat is not None and lng is not None and -90 <= lat <= 90 and -180 <= lng <= 180:
                        feature = {
                            'type': 'Feature',
                            'properties': {
                                'id': record.id,
                                'name': record.name,
                                'street': record.street,
                                'street2': record.street2,
                                'city': record.city,
                                'state_id': record.state_id.id if record.state_id else False,
                                'state_name': record.state_id.name if record.state_id else '',
                                'zip': record.zip,
                                'country_id': record.country_id.id if record.country_id else False,
                                'country_name': record.country_id.name if record.country_id else '',
                                'active': record.active,
                            },
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [lng, lat]  # GeoJSON uses [delivered_longitude, delivered_latitude]
                            }
                        }
                        features.append(feature)
                except Exception as e:
                    _logger.error(f"Error processing GeoJSON for {record.name}: {e}")
                    continue

            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }

            return {
                'success': True,
                'data': geojson,
                'count': len(features),
                'message': f'Generated GeoJSON for {len(features)} customers'
            }

        except Exception as e:
            _logger.error(f"Error generating GeoJSON: {e}")
            return {
                'success': False,
                'data': {'type': 'FeatureCollection', 'features': []},
                'count': 0,
                'error': str(e),
                'message': 'Failed to generate GeoJSON'
            }

    @http.route('/customer_map_tracking/debug_customers', type='http', auth='user')
    def debug_customers(self):
        """Debug endpoint to check customer data"""
        try:
            records = request.env['stock.picking'].sudo().search([])

            debug_info = {
                'total_customers': len(records),
                'customers_with_coordinates': 0,
                'customers_with_postgis': 0,
                'customers_active': 0,
                'sample_data': []
            }

            for record in records[:10]:  # Show first 10 for debugging
                has_coords = bool(record.delivered_latitude and record.delivered_longitude)
                has_postgis = bool(record.shape)

                if has_coords:
                    debug_info['customers_with_coordinates'] += 1
                if has_postgis:
                    debug_info['customers_with_postgis'] += 1
                if record.active:
                    debug_info['customers_active'] += 1

                sample = {
                    'id': record.id,
                    'name': record.name,
                    'street': record.street,
                    'street2': record.street2,
                    'city': record.city,
                    'state_id': record.state_id.id if record.state_id else False,
                    'state_name': record.state_id.name if record.state_id else '',
                    'zip': record.zip,
                    'country_id': record.country_id.id if record.country_id else False,
                    'country_name': record.country_id.name if record.country_id else '',
                    'delivered_latitude': record.delivered_latitude,
                    'delivered_longitude': record.delivered_longitude,
                    'has_postgis_shape': has_postgis,
                    'active': record.active,
                    'location_display': record.location_display
                }
                debug_info['sample_data'].append(sample)

            # Check PostGIS status
            try:
                request.env.cr.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
                postgis_available = request.env.cr.fetchone()[0]
                debug_info['postgis_available'] = postgis_available
            except Exception as e:
                debug_info['postgis_error'] = str(e)

            return request.make_response(
                json.dumps(debug_info, indent=2, default=str),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}, indent=2),
                headers=[('Content-Type', 'application/json')]
            )