from django.contrib import admin

from djangochain import models


class BlockAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Block, BlockAdmin)
