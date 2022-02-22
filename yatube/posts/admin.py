from django.contrib import admin

from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    DEFAULT_EMPTY: str = '-пусто-'
    list_display: tuple = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    search_fields: tuple = ('text', )
    list_filter: tuple = ('pub_date', )
    list_editable: tuple = ('group', )
    empty_value_display: str = DEFAULT_EMPTY


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
