from django.contrib.gis import admin
from vespadb.observations.models import Observation, Cluster


admin.site.register(Observation, admin.GISModelAdmin)
admin.site.register(Cluster, admin.GISModelAdmin)
