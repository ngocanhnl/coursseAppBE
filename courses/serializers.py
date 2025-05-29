from cloudinary.provisioning import users
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from courses.models import Course, ClassCategory, Lesson, Comment, Discount, Tag, User, Apointment, News, Payment,Order, ExpoDevice, TeacherProfile
from datetime import date

class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','username', 'email', 'first_name', 'last_name','phone_number', 'password', 'avatar','is_superuser','is_staff','role']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['avatar'] = instance.avatar.url if instance.avatar else ''
        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'avatar','id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = instance.avatar.url if instance.avatar else ''
        return data

class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'degree', 'experience_years', 'certificate']



class CategorySerializer(ModelSerializer):
    class Meta:
        model = ClassCategory
        fields = ['id', 'name']


class ItemSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['image'] = instance.image.url if instance.image else ''
        return data



class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'code', 'discount_percentage', 'is_active', 'created_at', 'updated_at']
        extra_kwargs = {
            'code': {
                'validators': [UniqueValidator(queryset=Discount.objects.all())]
            }
        }





class CourseSerializer(ItemSerializer):
    like = serializers.SerializerMethodField()
    students = UserMiniSerializer(many=True, read_only=True)
    teacher = UserMiniSerializer(read_only=True)
    best_active_discount = serializers.SerializerMethodField()
    def get_like(self, course):
        request =  self.context.get('request')
        if request and request.user.is_authenticated:
            return course.like_set.filter(user=request.user, is_active=True).exists()
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'image','capacity', 'price','best_active_discount', 'start_date', 'end_date','like', 'teacher', 'category', 'students']

    def get_best_active_discount(self, course):
        today = date.today()
        discount = (
            Discount.objects.filter(
                course=course,
                is_active = True,
                end_date__gte=today
            )
            .order_by('-discount_percentage')
            .first()
        )
        if discount:
            return DiscountSerializer(discount).data
        return None

class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class LessonSerializer(ItemSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'created_at', 'updated_at', 'image','content','is_done']


class LessonDetailSerializer(LessonSerializer):
    tags = TagSerializer(many=True)
    class Meta:
        model = LessonSerializer.Meta.model
        fields = LessonSerializer.Meta.fields + ['content', 'tags']



class CommentSerializer(ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        data['parent'] = CommentSerializer(instance.parent).data if instance.parent else None
        return data

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'user', 'course', 'parent']
        extra_kwargs = {
            'course': {'write_only': True},
        }

class ApointmentSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['teacher'] = UserSerializer(instance.teacher).data
        data['student'] = UserSerializer(instance.student).data
        return data


    class Meta:
        model = Apointment
        fields = ['id', 'date', 'time', 'notes','student','teacher']




class NewsSerializer(ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'image', 'user', 'course','type_news']



class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'amount', 'payment_url', 'status', 'created_at']
        read_only_fields = ['id', 'payment_url', 'status', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'course', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



class ExpoDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpoDevice
        fields = ['token']

    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data['token']

        device, _ = ExpoDevice.objects.update_or_create(
            user=user,
            token=token,  # không nên unique token toàn cục
            defaults={'token': token}
        )
        return device

