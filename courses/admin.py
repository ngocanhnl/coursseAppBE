from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django.urls import path
# Register your models here.

from .models import Course, Session, ClassCategory, Lesson, Comment, Bookmark, Tag, User






from django import forms
from ckeditor_uploader.widgets \
import CKEditorUploadingWidget




class LessonForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)
    class Meta:
        model = Lesson
        fields = '__all__'




class UserAdmin(admin.ModelAdmin):
    # def has_module_permission(self, request):
    #     return request.user.role == 'admin'
    #
    def has_view_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.role == 'admin'

    list_display = ['username', 'email', 'first_name', 'last_name', 'role']

class MyLessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_at']
    search_fields = ['title', 'course__name']
    list_filter = ['course', 'created_at']
    list_editable = ['course']
    readonly_fields = ['image_view']
    form = LessonForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Nếu là admin, xem tất cả bài học
        if request.user.role == 'admin':
            return qs
        # Nếu là HLV, chỉ hiển thị bài học thuộc các course do họ làm teacher
        return qs.filter(course__teacher=request.user)

    def image_view(self, lesson):
        if lesson:
            return mark_safe(f"<img src='/static/{lesson.image.name}' width='200' />")

    class Media:
        css = {
            'all': ('/static/css/styles.css',)
        }

class MyAdminSite(admin.AdminSite):
    site_header = "Course Management"
    site_title = "Course Management Admin"
    index_title = "Welcome to Course Management Admin"

    def has_permission(self, request):
        # Cho phép tất cả user đã đăng nhập vào Admin Site
        return  request.user.is_active

    def get_urls(self):
        return [path('course-stats/', self.course_stats), ] + super().get_urls()

    def course_stats(self, request):
        stats = ClassCategory.objects.annotate(course_count=Count('course__id')).values('id','name', 'course_count').order_by('-course_count')
        return TemplateResponse(request, 'admin/stats.html', {
            'stats': stats,
        })



class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(role='hlv')

class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Nếu user là admin, hiển thị toàn bộ
        if request.user.role == 'admin':
            return qs
        # Nếu là HLV, chỉ hiển thị course mà họ là giáo viên
        return qs.filter(teacher=request.user)


admin_site = MyAdminSite(name='eCourseAdmin')
admin_site.register(User, UserAdmin)

admin_site.register(Course, CourseAdmin)
admin_site.register(Session)
admin_site.register(ClassCategory)
admin_site.register(Lesson, MyLessonAdmin)
admin_site.register(Comment)
admin_site.register(Bookmark)
admin_site.register(Tag)