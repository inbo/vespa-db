from celery.schedules import crontab
PREWARM_CONFIGS = [
    {
        'name': 'default-visible',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01'},
        'schedule': crontab(minute='*/15') # Loopt op minuut 0, 15, 30, 45
    },
    ## ANB Filters
    {
        'name': 'anb-true',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'anbAreasActief': True},
        'schedule': crontab(minute='2-59/15')
    },
    {
        'name': 'anb-false',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'anbAreasActief': False},
        'schedule': crontab(minute='3-59/15')
    },
    ## Nest Status Filters
    {
        'name': 'status-open',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['open']},
        'schedule': crontab(minute='4-59/15')
    },
    {
        'name': 'status-reserved',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['reserved']},
        'schedule': crontab(minute='5-59/15')
    },
    {
        'name': 'status-eradicated',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['eradicated']},
        'schedule': crontab(minute='6-59/15')
    },
    {
        'name': 'status-visited',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestStatus': ['visited']},
        'schedule': crontab(minute='7-59/15')
    },
    ## Nest Type Filters
    {
        'name': 'type-embryonic',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestType': ['actief_embryonaal_nest']},
        'schedule': crontab(minute='8-59/15')
    },
    {
        'name': 'type-primary',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestType': ['actief_primair_nest']},
        'schedule': crontab(minute='9-59/15')
    },
    {
        'name': 'type-secondary',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestType': ['actief_secundair_nest']},
        'schedule': crontab(minute='10-59/15')
    },
    {
        'name': 'type-inactive',
        'params': {'visible': 'true', 'min_observation_datetime': '2024-04-01', 'nestType': ['inactief_leeg_nest']},
        'schedule': crontab(minute='11-59/15')
    },
]
