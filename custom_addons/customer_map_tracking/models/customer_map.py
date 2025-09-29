# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerMap(models.Model):
    _name = 'customer.map'
    _description = 'Customer / Worker with Map Tracking'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)

    # PostGIS geometry field
    shape = fields.GeoPoint(
        string='Map Location',
        help='Location coordinates using PostGIS geometry (SRID 4326)',
        srid=4326
    )

    # Coordinate fields
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 6),
        tracking=True,
        help='Latitude coordinate (manual entry)'
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 6),
        tracking=True,
        help='Longitude coordinate (manual entry)'
    )

    # Display fields
    location_display = fields.Char(
        string='Location',
        compute='_compute_location_display',
        store=True
    )
    geo_wkt = fields.Char(
        string='Geometry (WKT)',
        compute='_compute_geo_wkt',
        store=True
    )

    active = fields.Boolean(default=True, tracking=True)

    # =====================================================================
    # ONCHANGE: sync dua arah di form view (belum berhasil gesssss)
    # =====================================================================
    @api.onchange('shape')
    def _onchange_shape(self):
        """Kalau user pilih lokasi di map, isi latitude/longitude"""
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.latitude = float(lat)
                    rec.longitude = float(lon)
                except Exception as e:
                    _logger.warning(f"Failed to extract coords from shape: {e}")

    @api.onchange('latitude', 'longitude')
    def _onchange_latlon(self):
        """Kalau user isi latitude/longitude manual, update shape"""
        for rec in self:
            if rec.latitude and rec.longitude:
                try:
                    rec.set_location_from_coordinates(rec.latitude, rec.longitude)
                except Exception as e:
                    _logger.warning(f"Failed to update shape from lat/lon: {e}")

    @api.depends('shape', 'latitude', 'longitude')
    def _compute_location_display(self):
        for rec in self:
            if rec.shape and hasattr(rec.shape, 'coords'):
                try:
                    lon, lat = rec.shape.coords[0], rec.shape.coords[1]
                    rec.location_display = f"Lat: {lat:.6f}, Lng: {lon:.6f}"
                except Exception:
                    rec.location_display = "PostGIS Geometry Set"
            elif rec.latitude and rec.longitude:
                rec.location_display = f"Lat: {rec.latitude:.6f}, Lng: {rec.longitude:.6f}"
            else:
                rec.location_display = "No location set"

    @api.depends('shape', 'latitude', 'longitude')
    def _compute_geo_wkt(self):
        for rec in self:
            if rec.shape:
                try:
                    if hasattr(rec.shape, 'wkt'):
                        rec.geo_wkt = rec.shape.wkt
                    else:
                        rec.geo_wkt = str(rec.shape)
                except Exception:
                    rec.geo_wkt = "PostGIS Geometry"
            elif rec.latitude and rec.longitude:
                rec.geo_wkt = f'POINT({rec.longitude} {rec.latitude})'
            else:
                rec.geo_wkt = False

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        for rec in self:
            if rec.latitude and (rec.latitude < -90 or rec.latitude > 90):
                raise ValidationError(_('Latitude must be between -90 and 90 degrees.'))
            if rec.longitude and (rec.longitude < -180 or rec.longitude > 180):
                raise ValidationError(_('Longitude must be between -180 and 180 degrees.'))

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and '@' not in rec.email:
                raise ValidationError(_('Please enter a valid email address.'))

    def set_location_from_coordinates(self, lat, lng):
        """Internal method: set shape dari lat/lon"""
        self.ensure_one()
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError(_('Invalid coordinates.'))
        try:
            self._cr.execute("""
                UPDATE customer_map 
                SET shape = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
            """, (lng, lat, self.id))
            self.write({'latitude': lat, 'longitude': lng})
        except Exception as e:
            _logger.error("Failed to create PostGIS geometry: %s", e)
            raise ValidationError(_('Failed to create PostGIS geometry.'))
        return True

    def action_set_location_from_coordinates(self):
        self.ensure_one()
        if not self.latitude or not self.longitude:
            raise ValidationError(_('Please enter both latitude and longitude.'))
        return self.set_location_from_coordinates(self.latitude, self.longitude)

    def action_clear_location(self):
        self.write({'shape': False, 'latitude': False, 'longitude': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Location Cleared'),
                'message': _('Location coordinates have been cleared.'),
                'type': 'success',
            }
        }

    def action_geocode_address(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Geocoding'),
                'message': _('Geocoding service not configured. Please set location manually.'),
                'type': 'info',
            }
        }

    def action_open_map_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Location Map'),
            'res_model': 'customer.map',
            'view_mode': 'geoengine',
            'domain': [('id', '=', self.id)],
            'context': {'create': False, 'edit': False},
        }

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if vals.get('latitude') and vals.get('longitude') and not vals.get('shape'):
            try:
                rec.set_location_from_coordinates(vals['latitude'], vals['longitude'])
            except Exception as e:
                _logger.warning("Could not set PostGIS geometry on create: %s", e)
        if rec.shape or (rec.latitude and rec.longitude):
            rec.message_post(
                body=_('Customer location created: %s') % rec.location_display,
                message_type='notification'
            )
        return rec

    def write(self, vals):
        old_locations = {rec.id: rec.location_display for rec in self}
        res = super().write(vals)

        # Sync jika lat/lon diupdate tanpa shape
        if 'latitude' in vals and 'longitude' in vals and vals['latitude'] and vals['longitude']:
            for rec in self:
                if not vals.get('shape'):
                    try:
                        rec.set_location_from_coordinates(vals['latitude'], vals['longitude'])
                    except Exception as e:
                        _logger.warning("Could not sync lat/lon to shape: %s", e)

        # Log perubahan lokasi
        for rec in self:
            if rec.id in old_locations and old_locations[rec.id] != rec.location_display:
                rec.message_post(
                    body=_('Location changed from "%s" to "%s"') %
                         (old_locations[rec.id], rec.location_display),
                    message_type='notification'
                )
        return res

    @api.model
    def get_customers_geojson(self):
        customers = self.search([('shape', '!=', False), ('active', '=', True)])
        features = []
        for cust in customers:
            try:
                if cust.shape:
                    features.append({
                        'type': 'Feature',
                        'properties': {
                            'id': cust.id,
                            'name': cust.name,
                            'description': cust.description or '',
                            'phone': cust.phone or '',
                            'email': cust.email or '',
                        },
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [cust.shape.coords[0], cust.shape.coords[1]]
                        }
                    })
            except Exception as e:
                _logger.warning("Failed to process geometry for %s: %s", cust.name, e)
        return {'type': 'FeatureCollection', 'features': features}

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.phone:
                name += f' ({rec.phone})'
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            domain = ['|', '|',
                      ('name', operator, name),
                      ('phone', operator, name),
                      ('email', operator, name)]
            ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
            return self.browse(ids).name_get()
        return super()._name_search(name, args, operator, limit, name_get_uid)
