from cloudinary.provisioning import users
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from courses.models import Course, ClassCategory, Lesson, Comment, Bookmark, Tag, User, Apointment, News, Payment


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ['id','username', 'email', 'first_name', 'last_name', 'password', 'avatar','is_superuser','is_staff','role']
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




class CategorySerializer(ModelSerializer):
    class Meta:
        model = ClassCategory
        fields = ['id', 'name']


class ItemSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['image'] = instance.image.url if instance.image else ''
        return data


class CourseSerializer(ItemSerializer):
    like = serializers.SerializerMethodField()
    students = UserMiniSerializer(many=True, read_only=True)
    teacher = UserMiniSerializer(read_only=True)
    def get_like(self, course):
        request =  self.context.get('request')
        if request and request.user.is_authenticated:
            return course.like_set.filter(user=request.user, is_active=True).exists()
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'image','capacity', 'price', 'start_date', 'end_date','like', 'teacher', 'category', 'students']



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
        return data

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'user', 'course']
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


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'order_id']


class PaymentCallbackSerializer(serializers.Serializer):
    vnp_Amount = serializers.CharField(required=True)
    vnp_BankCode = serializers.CharField(required=False, allow_blank=True)
    vnp_BankTranNo = serializers.CharField(required=False, allow_blank=True)
    vnp_CardType = serializers.CharField(required=False, allow_blank=True)
    vnp_OrderInfo = serializers.CharField(required=True)
    vnp_PayDate = serializers.CharField(required=True)
    vnp_ResponseCode = serializers.CharField(required=True)
    vnp_TmnCode = serializers.CharField(required=True)
    vnp_TransactionNo = serializers.CharField(required=True)
    vnp_TransactionStatus = serializers.CharField(required=True)
    vnp_TxnRef = serializers.CharField(required=True)
    vnp_SecureHash = serializers.CharField(required=True)
