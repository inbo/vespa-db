"""
Dry run to see what would change:
bashpython manage.py update_user_municipalities --dry-run

Auto-match municipalities by name:
bashpython manage.py update_user_municipalities --strategy=name_match <-- do this

Remove invalid municipalities only:
bashpython manage.py update_user_municipalities --strategy=clear_invalid

Interactive mode for manual review:
bashpython manage.py update_user_municipalities --strategy=interactive
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from vespadb.users.models import VespaUser
from vespadb.observations.models import Municipality
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Update user municipality assignments after municipality data changes."

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['name_match', 'clear_invalid', 'interactive'],
            default='name_match',
            help='Strategy for updating municipalities: name_match (auto-match by name), clear_invalid (remove invalid assignments), interactive (manual review)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes'
        )

    def handle(self, *args, **options):
        strategy = options['strategy']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get all users with municipality assignments
        users_with_municipalities = VespaUser.objects.prefetch_related('municipalities').filter(
            municipalities__isnull=False
        ).distinct()
        
        total_users = users_with_municipalities.count()
        logger.info(f"Found {total_users} users with municipality assignments")
        self.stdout.write(self.style.SUCCESS(f"Found {total_users} users with municipality assignments"))
        
        if total_users == 0:
            self.stdout.write(self.style.WARNING("No users with municipality assignments found"))
            return
        
        # Get current valid municipalities
        current_municipalities = Municipality.objects.all()
        current_municipality_names = set(current_municipalities.values_list('name', flat=True))
        
        self.stdout.write(self.style.SUCCESS(f"Current valid municipalities: {len(current_municipality_names)}"))
        
        updated_users = 0
        users_with_issues = 0
        
        with transaction.atomic():
            for user in users_with_municipalities:
                try:
                    user_municipalities = list(user.municipalities.all())
                    invalid_municipalities = []
                    valid_municipalities = []
                    municipalities_to_add = []
                    
                    # Check which municipalities are still valid
                    for municipality in user_municipalities:
                        if municipality.name in current_municipality_names:
                            valid_municipalities.append(municipality)
                        else:
                            invalid_municipalities.append(municipality)
                    
                    if invalid_municipalities:
                        self.stdout.write(
                            self.style.WARNING(
                                f"User {user.username} (ID: {user.id}) has invalid municipalities: "
                                f"{[m.name for m in invalid_municipalities]}"
                            )
                        )
                        
                        if strategy == 'name_match':
                            # Try to match by name with current municipalities
                            for invalid_muni in invalid_municipalities:
                                # Find municipality with same name in current data
                                try:
                                    new_municipality = current_municipalities.get(name=invalid_muni.name)
                                    if new_municipality not in valid_municipalities:
                                        municipalities_to_add.append(new_municipality)
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f"  -> Matched '{invalid_muni.name}' to new municipality (ID: {new_municipality.id})"
                                            )
                                        )
                                except Municipality.DoesNotExist:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f"  -> Could not find replacement for '{invalid_muni.name}'"
                                        )
                                    )
                        
                        elif strategy == 'interactive':
                            # Interactive mode - ask user what to do
                            self.stdout.write(f"\nUser: {user.username} (ID: {user.id})")
                            self.stdout.write(f"Valid municipalities: {[m.name for m in valid_municipalities]}")
                            self.stdout.write(f"Invalid municipalities: {[m.name for m in invalid_municipalities]}")
                            
                            for invalid_muni in invalid_municipalities:
                                choice = input(f"Replace '{invalid_muni.name}' with (municipality name or 'skip'): ").strip()
                                if choice and choice.lower() != 'skip':
                                    try:
                                        new_municipality = current_municipalities.get(name=choice)
                                        if new_municipality not in valid_municipalities:
                                            municipalities_to_add.append(new_municipality)
                                    except Municipality.DoesNotExist:
                                        self.stdout.write(self.style.ERROR(f"Municipality '{choice}' not found"))
                        
                        # Update user's municipalities
                        if not dry_run:
                            # Remove invalid municipalities
                            user.municipalities.remove(*invalid_municipalities)
                            
                            # Add new municipalities
                            if municipalities_to_add:
                                user.municipalities.add(*municipalities_to_add)
                        
                        changes_made = len(invalid_municipalities) > 0 or len(municipalities_to_add) > 0
                        if changes_made:
                            updated_users += 1
                            action = "Would update" if dry_run else "Updated"
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"{action} user {user.username}: "
                                    f"removed {len(invalid_municipalities)}, added {len(municipalities_to_add)}"
                                )
                            )
                        
                        users_with_issues += 1
                    
                    else:
                        logger.debug(f"User {user.username} has all valid municipalities")
                
                except Exception as e:
                    logger.error(f"Failed to update user {user.username} (ID: {user.id}): {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(f"Error updating user {user.username}: {str(e)}")
                    )
        
        # Summary
        action = "Would be updated" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary:\n"
                f"Total users checked: {total_users}\n"
                f"Users with issues: {users_with_issues}\n"
                f"Users {action.lower()}: {updated_users}"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run. Use --dry-run=False to make actual changes."))
        
        logger.info(f"Update complete: {updated_users} users updated, {users_with_issues} users had issues")
