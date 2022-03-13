from django.contrib import admin
from .models import Sports, Match, EndedMatches


class SportsAdmin(admin.ModelAdmin):
    fields = ["name"]


class MatchAdmin(admin.ModelAdmin):
    fields = [field.name for field in Match._meta.get_fields()]
    fields.remove("id")


class EndedMatchesAdmin(admin.ModelAdmin):
    fields = [field.name for field in Match._meta.get_fields()]
    fields.remove("id")
    fields.remove("active_set")
    fields.remove("swap_position")
    fields.remove("client_os")
    fields.remove("current_inning")
    fields.remove("ace_out_time")
    fields.remove("red_ace_out")
    fields.remove("blue_ace_out")




admin.site.register(Sports, SportsAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(EndedMatches, EndedMatchesAdmin)