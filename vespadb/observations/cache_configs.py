
from celery.schedules import crontab
PREWARM_CONFIGS = [
    {
        'name': 'default',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01'},
        'schedule': crontab(minute='*/15')
    },
    {
        'name': 'anb-true',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'anbAreasActief': True},
        'schedule': crontab(minute='1-59/15')
    },
    {
        'name': 'anb-false',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'anbAreasActief': False},
        'schedule': crontab(minute='2-59/15')
    },
    {
        'name': 'status-open',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['open']},
        'schedule': crontab(minute='3-59/15')
    },
    {
        'name': 'status-reserved',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['reserved']},
        'schedule': crontab(minute='4-59/15')
    },
    {
        'name': 'status-eradicated',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['eradicated']},
        'schedule': crontab(minute='5-59/15')
    },
    {
        'name': 'status-visited',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['visited']},
        'schedule': crontab(minute='6-59/15')
    },
    {
        'name': 'type-secondary',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestType': ['actief_secundair_nest']},
        'schedule': crontab(minute='7-59/15')
    },
]
