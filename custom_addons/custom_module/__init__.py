from . import models
from . import wizard
from . import controller

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-installation hook to set up PostGIS integration
    """
    _logger.info("Setting up Customer Map Tracking with PostGIS...")

    try:
        cr = env.cr

        # Check PostGIS availability
        cr.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        postgis_available = cr.fetchone()[0]

        if not postgis_available:
            _logger.warning("PostGIS extension not found. Installing PostGIS...")
            try:
                cr.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                _logger.info("PostGIS extension installed successfully")
            except Exception as e:
                _logger.error("Failed to install PostGIS extension: %s", e)
                _logger.info("Please install PostGIS manually: CREATE EXTENSION postgis;")
                return
        else:
            _logger.info("PostGIS extension is available")

        # Verify PostGIS functions
        cr.execute("SELECT postgis_full_version();")
        version_info = cr.fetchone()
        _logger.info("PostGIS version: %s", version_info[0] if version_info else "Unknown")

        # Check if shape column exists, if not create it
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stock_picking' AND column_name = 'shape'
        """)
        shape_exists = cr.fetchone()

        if not shape_exists:
            _logger.info("Creating shape column...")
            cr.execute("ALTER TABLE stock_picking ADD COLUMN shape geometry(POINT, 4326);")

        # Update demo data with PostGIS geometries
        _logger.info("Converting demo data coordinates to PostGIS geometries...")
        cr.execute("""
            UPDATE stock_picking 
            SET shape = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND (shape IS NULL OR ST_IsEmpty(shape))
        """)

        updated_count = cr.rowcount
        _logger.info("Updated %d customer records with PostGIS geometries", updated_count)

        # Create spatial index for better performance
        try:
            cr.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_picking_shape_gist 
                ON stock_picking USING GIST (shape);
            """)
            _logger.info("Created spatial index on stock_picking.shape")
        except Exception as e:
            _logger.warning("Could not create spatial index: %s", e)

        # Verify the setup
        cr.execute("""
            SELECT COUNT(*) FROM stock_picking 
            WHERE shape IS NOT NULL
        """)
        geom_count = cr.fetchone()[0]
        _logger.info("Successfully set up %d customer locations with PostGIS geometries", geom_count)

    except Exception as e:
        _logger.error("PostGIS setup failed: %s", e)
        _logger.info("""
        Manual PostGIS setup required:
        1. Install PostGIS: sudo apt-get install postgresql-postgis
        2. Enable in database: CREATE EXTENSION postgis;
        3. Restart Odoo and upgrade the module
        """)


def uninstall_hook(env):
    """
    Pre-uninstallation hook to clean up PostGIS data
    """
    _logger.info("Cleaning up Customer Map Tracking PostGIS data...")

    try:
        cr = env.cr

        # Drop spatial indexes
        cr.execute("DROP INDEX IF EXISTS idx_stock_picking_shape_gist;")
        _logger.info("Dropped spatial indexes")

        # Note: We don't drop the PostGIS extension as it might be used by other modules
        _logger.info("PostGIS extension preserved (may be used by other modules)")

        # Clear geometry data (optional - data will be removed with table anyway)
        cr.execute("UPDATE stock_picking SET shape = NULL WHERE shape IS NOT NULL;")
        _logger.info("Cleared PostGIS geometry data")

    except Exception as e:
        _logger.warning("PostGIS cleanup warning: %s", e)

    _logger.info("Customer Map Tracking module uninstalled successfully")