import datetime
import pytz

def get_cet_timezone():
    """Return the consistent CET timezone object."""
    return pytz.timezone("Europe/Brussels")

def now_in_cet():
    """Return current time in CET."""
    return datetime.now(get_cet_timezone())

def convert_to_cet(dt):
    """Convert a datetime to CET."""
    if dt is None:
        return None
    cet = get_cet_timezone()
    if dt.tzinfo is None:
        return cet.localize(dt)
    return dt.astimezone(cet)
