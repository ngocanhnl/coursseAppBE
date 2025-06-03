from collections import defaultdict

from django.contrib import admin

from django.utils.safestring import mark_safe
from django.urls import path
from .models import Course, Session, ClassCategory, Lesson, Comment, Bookmark, Tag, User, Discount, TeacherProfile, Payment, Enrollment, News
import json
from django.shortcuts import render
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms
from ckeditor_uploader.widgets \
import CKEditorUploadingWidget

from .utils import notify_user


class LessonForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)
    class Meta:
        model = Lesson
        fields = '__all__'


class UserAdmin(admin.ModelAdmin):
    # def has_module_permission(self, request):
    #     return request.user.role == 'admin'
    #
    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'
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


class NewFeedsAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_at']
    search_fields = ['title', 'course__name']
    list_filter = ['course', 'created_at']
    exclude = ['user']

    def image_view(self, news):
        if news.image:
            return mark_safe(f"<img src='{news.image.url}' width='200' />")
        return "No Image"
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Nếu là admin, xem tất cả bài học
        if request.user.role == 'admin':
            return qs
        # Nếu là HLV, chỉ hiển thị bài học thuộc các course do họ làm teacher
        return qs.filter(course__teacher=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Giới hạn course nếu là HLV
        if request.user.role == 'hlv':
            form.base_fields['course'].queryset = Course.objects.filter(teacher=request.user)
        else:
            form.base_fields['course'].queryset = Course.objects.all()

        return form

    def save_model(self, request, obj, form, change):
        # Gán user là người đang đăng nhập nếu tạo mới
        if not change or not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


class MyAdminSite(admin.AdminSite):
    site_header = "Course Management"
    site_title = "Course Management Admin"
    index_title = "Welcome to Course Management Admin"

    def has_permission(self, request):
        # Cho phép tất cả user đã đăng nhập vào Admin Site
        return  request.user.is_active

    def get_urls(self):
        return [path('course-stats/', self.stats_view), ] + super().get_urls()

    def stats_view(self, request):
        # Lấy tham số từ request
        period = request.GET.get('period', 'month')
        selected_month = request.GET.get('month', str(timezone.now().month))
        selected_year = request.GET.get('year', str(timezone.now().year))
        selected_course = request.GET.get('course', '')

        # Thống kê số lượng hội viên
        total_members = User.objects.filter(role='hoc-vien').count()

        # Xác định khoảng thời gian
        now = timezone.now()

        if period == 'custom':
            # Lọc theo tháng/năm cụ thể
            try:
                year = int(selected_year)
                month = int(selected_month)
                start_date = datetime(year, month, 1).replace(tzinfo=timezone.get_current_timezone())
                if month == 12:
                    end_date = datetime(year + 1, 1, 1).replace(tzinfo=timezone.get_current_timezone())
                else:
                    end_date = datetime(year, month + 1, 1).replace(tzinfo=timezone.get_current_timezone())
                date_format = lambda d: f"{d.year}-{d.month:02d}-{d.day:02d}"
            except:
                start_date = now - timedelta(days=365)
                end_date = now
                date_format = lambda d: f"{d.year}-{d.month:02d}"
        elif period == 'week':
            start_date = now - timedelta(weeks=12)
            end_date = now
            date_format = lambda d: f"{d.year}-W{d.isocalendar()[1]:02d}"
        elif period == 'year':
            start_date = now - timedelta(days=365 * 5)
            end_date = now
            date_format = lambda d: str(d.year)
        else:  # month
            start_date = now - timedelta(days=365)
            end_date = now
            date_format = lambda d: f"{d.year}-{d.month:02d}"

        # Lấy dữ liệu thô và group theo period
        members_filter = Q(role='hoc-vien', date_joined__gte=start_date)
        if end_date:
            members_filter &= Q(date_joined__lt=end_date)
        #
        # members = User.objects.filter(members_filter).values_list('date_joined', flat=True)
        members = []
        members2 = []
        enrollment_filter = Q(created_at__gte=start_date)
        if end_date:
            enrollment_filter &= Q(created_at__lt=end_date)

        if selected_course:
            enrollment_filter &= Q(course=selected_course)
        members2 = Enrollment.objects.filter(enrollment_filter).values_list('created_at', flat=True)
        print("Members2 quẻy:", members2)
        if members2:
            members = [m for m in members2 if m]
        print("Members :", members)
        payments_filter = Q(status='completed', created_at__gte=start_date)
        if end_date:
            payments_filter &= Q(created_at__lt=end_date)

        if selected_course:
            payments_filter &= Q(order__course_id=selected_course)

        payments = Payment.objects.filter(payments_filter).values_list('created_at', 'amount')

        # Group dữ liệu theo period
        member_stats = defaultdict(int)
        for date_joined in members:
            if date_joined:
                period_key = date_format(date_joined)
                member_stats[period_key] += 1

        revenue_stats = defaultdict(float)
        for created_at, amount in payments:
            if created_at and amount:
                period_key = date_format(created_at)
                revenue_stats[period_key] += float(amount)

        # Thống kê doanh thu theo từng khóa học
        course_revenue_filter = Q(status='completed', created_at__gte=start_date)
        if end_date:
            course_revenue_filter &= Q(created_at__lt=end_date)

        course_revenue = (Payment.objects
                          .filter(course_revenue_filter)
                          .select_related('order__course')
                          .values('order__course__name', 'order__course_id')
                          .annotate(total=Sum('amount'), count=Count('id'))
                          .order_by('-total'))

        # Chi tiết course được chọn
        course_detail = None
        if selected_course:
            try:
                course = Course.objects.get(id=selected_course)
                course_payments = Payment.objects.filter(
                    status='completed',
                    order__course=course,
                    created_at__gte=start_date
                )
                if end_date:
                    course_payments = course_payments.filter(created_at__lt=end_date)

                course_detail = {
                    'name': course.name,
                    'total_revenue': course_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
                    'total_students': course.students.count(),
                    'total_orders': course_payments.count(),
                    'price': course.price,
                    'capacity': course.capacity,
                    'start_date': course.start_date,
                    'end_date': course.end_date,
                }
            except Course.DoesNotExist:
                pass

        # Thống kê số học viên theo từng khóa học
        course_students = (Course.objects
                           .annotate(student_count=Count('students'))
                           .values('name', 'student_count')
                           .order_by('-student_count'))

        # Chuẩn bị dữ liệu cho biểu đồ
        member_labels = sorted(member_stats.keys())
        member_data = [member_stats[label] for label in member_labels]

        revenue_labels = sorted(revenue_stats.keys())
        revenue_data = [revenue_stats[label] for label in revenue_labels]

        # Đảm bảo có dữ liệu hiển thị ngay cả khi không có
        if not member_labels:
            member_labels = [date_format(now)]
            member_data = [0]

        if not revenue_labels:
            revenue_labels = [date_format(now)]
            revenue_data = [0]

        course_names = [item['order__course__name'] for item in course_revenue[:10] if item['order__course__name']]
        course_revenues = [float(item['total']) if item['total'] else 0 for item in course_revenue[:10]]
        course_ids = [item['order__course_id'] for item in course_revenue[:10]]

        # Danh sách tất cả courses để chọn
        all_courses = Course.objects.all().values('id', 'name').order_by('name')

        # Tính tổng doanh thu
        total_revenue_filter = Q(status='completed')
        if selected_course:
            total_revenue_filter &= Q(order__course_id=selected_course)

        total_revenue = Payment.objects.filter(total_revenue_filter).aggregate(
            total=Sum('amount')
        )['total'] or 0

        student_course_names = [item['name'] for item in course_students[:10] if item['name']]
        student_counts = [item['student_count'] for item in course_students[:10]]

        context = {
            'title': 'Thống kê',
            'total_members': total_members,
            'total_courses': Course.objects.count(),
            'total_revenue': total_revenue,
            'current_period': period,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_course': selected_course,
            'all_courses': all_courses,
            'course_detail': course_detail,
            'months': [(i, f'Tháng {i}') for i in range(1, 13)],
            'years': [i for i in range(2020, timezone.now().year + 2)],
            'member_chart_data': {
                'labels': json.dumps(member_labels),
                'data': json.dumps(member_data)
            },
            'revenue_chart_data': {
                'labels': json.dumps(revenue_labels),
                'data': json.dumps(revenue_data)
            },
            'course_revenue_data': {
                'labels': json.dumps(course_names),
                'data': json.dumps(course_revenues),
                'ids': json.dumps(course_ids)
            },
            'course_students_data': {
                'labels': json.dumps(student_course_names),
                'data': json.dumps(student_counts)
            }
        }
        print("Context for stats view:", context['member_chart_data'])

        return render(request, 'admin/stats.html', context)
    # def stats_view(self, request):
    #     day = request.GET.get('day')
    #     month = request.GET.get('month')
    #     year = request.GET.get('year')
    #     print("day", day)
    #     print("month", month)
    #     print("year", year)
    #
    #
    #     payment_filter = Payment.objects.all()
    #     if year:
    #         payment_filter = payment_filter.filter(created_at__year=year)
    #     if month:
    #         payment_filter = payment_filter.filter(created_at__month=month)
    #     if day:
    #         payment_filter = payment_filter.filter(created_at__day=day)
    #     print(payment_filter.query)
    #
    #     # Thống kê danh mục và học viên
    #     category_stats = ClassCategory.objects.annotate(
    #         course_count=Count('course')
    #     ).filter(course_count__gt=0)
    #
    #     course_student_stats = Course.objects.annotate(
    #         student_count=Count('students')
    #     ).order_by('-student_count')[:10]
    #
    #     # Doanh thu theo khóa học
    #     course_revenue_stats = (
    #         payment_filter
    #         .values(name=F('order__course__name'))
    #         .annotate(
    #             revenue=Sum('amount'),
    #             created_at=F('created_at')
    #         )
    #         .order_by('-revenue')[:10]
    #     )
    #
    #     # Thống kê trạng thái thanh toán
    #     payment_stats = payment_filter.values('status').annotate(
    #         count=Count('id')
    #     )
    #
    #     context = {
    #         'category_stats': category_stats,
    #         'course_student_stats': course_student_stats,
    #         'course_revenue_stats': course_revenue_stats,
    #         'payment_stats': payment_stats,
    #         'total_courses': Course.objects.count(),
    #         'total_students': User.objects.filter(role='hoc-vien').count(),
    #         'total_revenue': payment_filter.aggregate(total=Sum('amount'))['total'] or 0,
    #         'total_categories': ClassCategory.objects.count(),
    #
    #     }
    #
    #     return render(request, 'admin/stats.html', context)

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

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'start_date', 'end_date']
    search_fields = ['code']
    list_filter = ['start_date', 'end_date']
    readonly_fields = ['created_at', 'updated_at']

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def save_model(self, request, obj, form, change):
        print("printModel")
        obj.user = request.user  # Gán user tạo mã giảm giá
        super().save_model(request, obj, form, change)
        students = User.objects.filter(role='hoc-vien')
        notify_user(
                students,
                "New Discount Created",
                f"'{obj.course}' has new discount."
            )



class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'created_at']
    search_fields = ['user__username', 'lesson__title']
    list_filter = ['created_at']

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

class TeacherInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'degree', 'experience_years')  # tuỳ chỉnh hiển thị

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(role='hlv')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'status', 'created_at']
    search_fields = ['order__course__name', 'order__user__username']
    list_filter = ['status', 'created_at']

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_add_permission(self, request):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_change_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == 'admin'


admin_site = MyAdminSite(name='eCourseAdmin')
admin_site.register(User, UserAdmin)

admin_site.register(Course, CourseAdmin)
admin_site.register(Session)
admin_site.register(ClassCategory)
admin_site.register(Lesson, MyLessonAdmin)
admin_site.register(Comment)
admin_site.register(Bookmark)
admin_site.register(Tag)
admin_site.register(Discount, DiscountAdmin)
admin_site.register(TeacherProfile, TeacherInfoAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(News, NewFeedsAdmin)
