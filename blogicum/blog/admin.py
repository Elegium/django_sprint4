from django.contrib import admin
from .models import Post, Category, Location, Comment

admin.site.empty_value_display = 'Не задано'


class PostInLine(admin.StackedInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInLine,
    )
    list_display = (
        'title',
        'description',
        'is_published',
        'slug'
    )
    list_editable = (
        'is_published',
    )


class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInLine,
    )
    list_display = (
        'name',
    )


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = "pub_date"
    list_display = ('title',
                    'is_published',
                    'pub_date',
                    'author',
                    'location',
                    'category',
                    'created_at',
                    )
    list_editable = (
        'is_published',
        'pub_date',
        'author',
        'location',
        'category'

    )
    search_fields = [
        'title',
    ]

    list_filter = (
        'title',
        'author',
        'location',
        'category'
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Comment)
