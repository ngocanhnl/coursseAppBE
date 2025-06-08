from django.contrib.auth.models import AbstractUser
from django.db import models
from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField
# Create your models here.


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('tiep_tan', 'Tiếp Tân'),
        ('hlv', 'Hlv'),
        ('hoc-vien', 'Hoc Vien'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='hoc-vien', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    avatar = CloudinaryField('image', null=True, blank=True)



class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    degree = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField(default=0)
    certificate = models.TextField(blank=True)

    def __str__(self):
        return f"TeacherProfile for {self.user.username}"


class ExpoDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)




class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)
    is_active = models.BooleanField(default=True, null=True)
    class Meta:
        abstract = True
        ordering = ['-id']








class ClassCategory(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = CloudinaryField('image', null=True)

    def __str__(self):
        return self.name


class Bookmark(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classBookmark = models.ForeignKey('Course', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.classBookmark.name}"

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)
    class Meta:
        unique_together = ('user', 'course')



class Course(BaseModel):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ClassCategory, on_delete=models.CASCADE)
    description = models.TextField()
    image = CloudinaryField('image', null=True, blank=True)
    capacity = models.PositiveIntegerField()
    price = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    bookmark_user = models.ManyToManyField(User, through=Bookmark, related_name='bookmark_user')
    students = models.ManyToManyField(User, through='Enrollment', related_name="enrolled_courses")

    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='teaching_courses')
    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['-id']

class Discount(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    discount_percentage = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    def __str__(self):
        return f"{self.course.name} - {self.discount_percentage}%"


class Session(BaseModel):
    class_instance = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.TextField(blank=True)


    def __str__(self):
        return f"{self.class_instance.name} - {self.start_time} - {self.end_time}"



class Tag(BaseModel):
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.name}"



class Lesson(BaseModel):
    title = models.CharField(max_length=100)
    content = RichTextField()
    image = CloudinaryField('image', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, null = True, blank=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('title', 'course')


class Interaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Comment(Interaction):
    content = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.content}"

class Like(Interaction):


    class Meta:
        unique_together = ('user', 'course')


class Apointment(BaseModel):
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name='student')
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='teacher')
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.teacher.username} - {self.date} {self.time}"


class News(BaseModel):
    TYPE_NEWS_CHOICES = [
        ('work out', 'Work Out'),
        ('nutrition', 'Nutrition'),
        ('event', 'Event'),
        ('news', 'News'),
    ]

    title = models.CharField(max_length=100)
    content = RichTextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    type_news = models.CharField(
        max_length=20,
        choices=TYPE_NEWS_CHOICES,
        default='news'
    )
    image = CloudinaryField('image', null=True, blank=True)
    def __str__(self):
        return f"{self.content}"




class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.user.username} - {self.course.name}"


import uuid

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Chờ thanh toán'),
        ('completed', 'Đã thanh toán'),
        ('failed', 'Thanh toán thất bại'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_url = models.URLField(blank=True, null=True)
    vnp_txn_ref = models.CharField(max_length=100, blank=True, null=True)
    vnp_transaction_no = models.CharField(max_length=100, blank=True, null=True)
    vnp_response_code = models.CharField(max_length=10, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.order_id} - {self.amount} VND"






