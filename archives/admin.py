from django.contrib import admin

from archives.models import Archive


class ArchiveAdmin(admin.ModelAdmin):
    list_display = (
        "name", "default", "host", "basedir", "policy", "transport")
    list_filter = ("policy", "transport")
    list_display_links = ("name",)
    search_fields = ("name", "host")

    def save_model(self, request, obj, form, change):
        if obj.default:
            Archive.objects.update(default=False)
        else:
            if Archive.objects.count() < 2:
                obj.default = True
        obj.save()


admin.site.register(Archive, ArchiveAdmin)
