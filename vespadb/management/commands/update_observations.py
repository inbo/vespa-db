from django.core.management.base import BaseCommand
from django.db import transaction, connection
from vespadb.observations.models import Observation
from vespadb.observations.utils import get_municipality_from_coordinates, check_if_point_in_anb_area
from django.contrib.gis.geos import Point
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Update municipality and province assignments for all observations based on current municipality data."

    def handle(self, *args, **options):
        batch_size = 1000
        total_updated = 0
        total_failed = 0

        # Log initial state
        observation_count = Observation.objects.count()
        logger.info(f"Starting update_observations command. Total observations in database: {observation_count}")
        self.stdout.write(self.style.SUCCESS(f"Found {observation_count} observations to process"))

        if observation_count == 0:
            logger.warning("No observations found in the database. Exiting.")
            self.stdout.write(self.style.WARNING("No observations to update. Check if observations have been loaded."))
            return

        # Verify database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM observations_observation")
                db_count = cursor.fetchone()[0]
                logger.info(f"Raw SQL count of observations: {db_count}")
                self.stdout.write(self.style.SUCCESS(f"Raw SQL count confirms {db_count} observations"))
        except Exception as e:
            logger.error(f"Failed to verify observation count via raw SQL: {str(e)}")
            self.stdout.write(self.style.ERROR("Error verifying observation count in database"))

        with transaction.atomic():
            # Process observations in batches
            for i in range(0, observation_count, batch_size):
                logger.info(f"Processing batch {i // batch_size + 1} (indices {i} to {i + batch_size})")
                batch = Observation.objects.all()[i:i + batch_size]
                batch_count = len(batch)
                logger.info(f"Batch size: {batch_count} observations")
                self.stdout.write(self.style.SUCCESS(f"Batch {i // batch_size + 1}: Processing {batch_count} observations"))

                if batch_count == 0:
                    logger.warning(f"Empty batch at index {i}. Skipping.")
                    continue

                for obs in batch:
                    try:
                        logger.debug(f"Processing observation ID {obs.id}")
                        if obs.location and isinstance(obs.location, Point):
                            long, lat = obs.location.x, obs.location.y
                            logger.debug(f"Observation {obs.id} location: ({long}, {lat})")
                            municipality = get_municipality_from_coordinates(long, lat)
                            logger.debug(f"Observation {obs.id} assigned municipality: {municipality.name if municipality else 'None'}")

                            # Store old values for comparison
                            old_municipality = obs.municipality
                            old_province = obs.province
                            old_anb = obs.anb

                            # Assign new values
                            obs.municipality = municipality
                            obs.province = municipality.province if municipality else None
                            obs.anb = check_if_point_in_anb_area(long, lat)

                            # Check which fields have changed
                            changed_fields = []
                            if old_municipality != obs.municipality:
                                old_muni_name = old_municipality.name if old_municipality else "None"
                                new_muni_name = municipality.name if municipality else "None"
                                changed_fields.append(
                                    f"municipality: {old_muni_name} -> {new_muni_name}"
                                )
                            if old_province != obs.province:
                                old_prov_name = old_province.name if old_province else "None"
                                new_prov_name = municipality.province.name if municipality and municipality.province else "None"
                                changed_fields.append(
                                    f"province: {old_prov_name} -> {new_prov_name}"
                                )
                            if old_anb != obs.anb:
                                changed_fields.append(f"anb: {old_anb} -> {obs.anb}")

                            # Save only if changes are detected
                            if changed_fields:
                                obs.save(update_fields=['municipality', 'province', 'anb'])
                                total_updated += 1
                                logger.info(
                                    f"Successfully updated observation {obs.id}. Changed fields: {', '.join(changed_fields)}"
                                )
                            else:
                                logger.debug(f"No changes for observation {obs.id}. Skipping save.")
                        else:
                            logger.warning(f"Invalid location for observation {obs.id}: {obs.location}")
                            total_failed += 1
                    except Exception as e:
                        logger.error(f"Failed to update observation {obs.id}: {str(e)}")
                        total_failed += 1

                self.stdout.write(
                    self.style.SUCCESS(f"Processed batch {i // batch_size + 1}: {total_updated} updated, {total_failed} failed")
                )

        logger.info(f"Update complete: {total_updated} observations updated, {total_failed} failed")
        self.stdout.write(
            self.style.SUCCESS(f"Update complete: {total_updated} observations updated, {total_failed} failed")
        )
