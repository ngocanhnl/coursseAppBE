from rest_framework.decorators import action
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from django.db.models import Q
from courses import serializers
from rest_framework import viewsets, generics, status, parsers, permissions
from courses.models import ClassCategory, Course, Lesson, Comment, Tag, User, Like, News, Apointment
from courses.paginators import ItemPagination, CommentPagination
from courses.perm import CommentOwner, IsHLV




#
# class ChatViewSet(viewsets.ViewSet, generics.CreateAPIView):
#     queryset = Chat.objects.filter(is_active=True)
#     serializer_class = serializers.ChatSerializer



class ApointmentViewSet(viewsets.ViewSet, generics.CreateAPIView, ):
    queryset = Apointment.objects.filter(is_active=True)
    serializer_class = serializers.ApointmentSerializer
    permission_classes = [IsHLV]



class ClassCategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = ClassCategory.objects.filter(is_active=True)
    serializer_class = serializers.CategorySerializer

class CourseViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Course.objects.filter(is_active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class =  ItemPagination

    def get_queryset(self):
        query = self.queryset

        q = self.request.query_params.get('q')
        if q:
            query = query.filter(name__icontains=q)

        cate_id = self.request.query_params.get('category_id')

        if cate_id:
            query = query.filter(category_id=cate_id)

        # typeNews = self.request.query_params.get('typeNews')
        # if typeNews:
        #     query = query.filter(type_news.__eq__(typeNews))

        return query



    @action(detail=True, methods=['get','post'])
    def news(self, request, pk):
        if request.method.__eq__('POST'):
            print("Post news",request.data)
            data = request.data.copy()
            data['course'] = pk
            n = serializers.NewsSerializer(data=data)
            n.is_valid(raise_exception=True)
            d = n.save(user=request.user)  # GÁN user thủ công ở đây
            return Response(serializers.NewsSerializer(d).data, status=status.HTTP_201_CREATED)
        type_news = request.query_params.get('typeNews')
        news = self.get_object().news_set.filter(is_active=True)
        if type_news:
            news = news.filter(type_news=type_news)

            # Sắp xếp theo ngày tạo mới nhất
        news = news.order_by('-created_at')

        # news = News.objects.filter(course=course)
        paginator = ItemPagination()
        page = paginator.paginate_queryset(news, request)
        if page is not None:
            serializer = serializers.NewsSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        return Response(serializers.NewsSerializer(news, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='addStudent')
    def addStudent(self, request, pk=None):
        course = self.get_object()
        if request.user in course.students.all():
            return Response({'message': 'You are already enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)

        print('Khoa hoc',course)
        print('Thong tin request.user ',request.user)
        course.students.add(request.user)
        course.save()

        return Response(serializers.CourseSerializer(course).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['get'])
    def get_lessons(self, request, pk):
        lessons = self.get_object().lesson_set.filter(is_active=True)

        return Response(serializers.LessonSerializer(lessons, many=True).data, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action in ['get_comment','like'] and self.request.method.__eq__('POST'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    @action(detail=True, methods=['get','post'], url_path='comments')
    def get_comment(self, request, pk):

        if request.method.__eq__('POST'):
            c = serializers.CommentSerializer(data={
                'content': request.data.get('content'),
                'user': request.user.pk,
                'course': pk
            })
            c.is_valid(raise_exception=True)
            d = c.save()
            return Response(serializers.CommentSerializer(d).data, status=status.HTTP_201_CREATED)

        comment = self.get_object().comment_set.select_related('user').filter(is_active=True)
        paginator = CommentPagination()
        page = paginator.paginate_queryset(comment, request)
        if page is not None:
            serializer = serializers.CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)


        return Response(serializers.CommentSerializer(comment, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk):
        li, created = Like.objects.get_or_create(user=self.request.user, course=self.get_object())
        if not created:
            li.is_active = not li.is_active

        li.save()
        return Response(serializers.CourseSerializer(self.get_object(), context={'request': request}).data,status=status.HTTP_200_OK)

class LessonViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Lesson.objects.prefetch_related('tags').filter(is_active=True)
    serializer_class = serializers.LessonDetailSerializer

    @action(methods=['post'], detail=True, url_path='lesson-done')
    def lesson_done(self, request, pk):
        lesson = self.get_object()
        lesson.is_done = not lesson.is_done
        lesson.save()
        return Response(serializers.LessonSerializer(lesson).data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]



    def get_queryset(self):
        query = self.queryset

        q = self.request.query_params.get('q')
        if q:
            query = query.filter(name__icontains=q)

        cate_id = self.request.query_params.get('category_id')

        if cate_id:
            query = query.filter(category_id=cate_id)

        return query


    @action(methods=['get'], url_path='my-appointment', detail=True, permission_classes=[permissions.IsAuthenticated])
    def get_my_appointment(self, request, pk):
        appointment = Apointment.objects.filter(student=request.user, is_active=True)

        return Response(serializers.ApointmentSerializer(appointment, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='my-courses', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_my_courses(self, request):
        # courses = Course.objects.filter(students=request.user || teacher = request.user)

        courses = Course.objects.filter(Q(students=request.user) | Q(teacher=request.user))
        serializer = serializers.CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'patch'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        if request.method.__eq__('PATCH') :
            u = request.user
            for k, v in request.data.items():
                if k.__eq__('password'):
                    u.set_password(v)
                else:
                    setattr(u, k, v)
            u.save()
            return Response(serializers.UserSerializer(u).data, status=status.HTTP_200_OK)


        return Response(serializers.UserSerializer(request.user).data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='staff', detail=False, permission_classes=[permissions.IsAuthenticated])
    def create_staff(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        request.data['is_superuser'] = True
        request.data['is_staff'] = True
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializers.UserSerializer(user).data, status=status.HTTP_201_CREATED)



class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.filter(is_active=True)
    serializer_class = serializers.CommentSerializer
    permission_classes = [CommentOwner]


from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from datetime import datetime
import urllib.parse
import hmac
import hashlib
import random
# class VNPayCreateUrl(APIView):
#     def post(self, request):
#         order_id = str(random.randint(100000, 999999))
#         amount = random.randint(100000, 999999)
#         client_ip = "127.0.0.1"
#
#         config = settings.VNPAY_CONFIG
#         vnp_TxnRef = str(random.randint(100000, 999999))
#         vnp_Amount = int(amount) * 100
#         vnp_OrderInfo = f"Thanh toan don hang {order_id}"
#         vnp_ReturnUrl = "http://localhost:8000/order/vnpay-return/"
#         vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
#
#         inputData = {
#             "vnp_Version": "2.1.0",
#             "vnp_Command": "pay",
#             "vnp_TmnCode": config['vnp_TmnCode'],
#             "vnp_Amount": vnp_Amount,
#             "vnp_CurrCode": "VND",
#             "vnp_TxnRef": vnp_TxnRef,
#             "vnp_OrderInfo": vnp_OrderInfo,
#             "vnp_OrderType": "other",
#             "vnp_Locale": "vn",
#             "vnp_BankCode": "NCB",
#             "vnp_ReturnUrl": vnp_ReturnUrl,
#             "vnp_IpAddr": client_ip,
#             "vnp_CreateDate": vnp_CreateDate,
#             "vnp_SecureHashType": "SHA512"
#         }
#
#         sorted_data = sorted(inputData.items())
#         hash_data = '&'.join(f"{k}={v}" for k, v in sorted_data)
#         query_string = urllib.parse.urlencode(sorted_data)
#         print(config['vnp_HashSecret'])
#         print(inputData)
#         secure_hash = hmac.new(
#             config['vnp_HashSecret'].encode(),
#             hash_data.encode(),
#             hashlib.sha512
#         ).hexdigest()
#
#         payment_url = f"{config['vnp_Url']}?{query_string}&vnp_SecureHash={secure_hash}"
#
#         return Response({"payment_url": payment_url})
#

class VNPayCreateUrl(APIView):
    def post(self, request):
        # Generate order details
        order_id = str(random.randint(100000, 999999))
        amount = request.data.get('amount', random.randint(100000, 999999))
        client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

        config = settings.VNPAY_CONFIG
        vnp_TxnRef = order_id  # Using order_id as transaction reference for consistency
        vnp_Amount = int(amount) * 100  # Convert to smallest currency unit (cents)
        vnp_OrderInfo = f"Thanh toan don hang {order_id}"
        vnp_ReturnUrl = "https://a999-2001-ee0-4f01-2ec0-206e-70d2-cbc9-2008.ngrok-free.app/payment/vnpay-return/"
        vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')

        # Prepare payment data
        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": config['vnp_TmnCode'],
            "vnp_Amount": vnp_Amount,
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": vnp_TxnRef,
            "vnp_OrderInfo": vnp_OrderInfo,
            "vnp_OrderType": "other",
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": vnp_ReturnUrl,
            "vnp_IpAddr": client_ip,
            "vnp_CreateDate": vnp_CreateDate,
        }

        # Optional bank code if provided
        bank_code = request.data.get('bank_code')
        if bank_code:
            inputData["vnp_BankCode"] = bank_code

        # Sort the dictionary by key for consistent hashing
        sorted_data = sorted(inputData.items())

        # Create the URL-encoded query string
        query_string = urllib.parse.urlencode(sorted_data)

        # Calculate the secure hash
        secret = config['vnp_HashSecret'].encode()
        message = query_string.encode()
        secure_hash = hmac.new(
            secret,
            message,
            hashlib.sha512
        ).hexdigest()

        # Construct the final payment URL
        payment_url = f"{config['vnp_Url']}?{query_string}&vnp_SecureHash={secure_hash}&vnp_SecureHashType=SHA512"

        # Log the transaction details for debugging (remove in production)
        # logger.debug(f"VNPay URL created: {payment_url}")

        return Response({
            "status": "success",
            "payment_url": payment_url,
            "order_id": order_id
        })

import logging
logger = logging.getLogger(__name__)

class VNPayReturnView(APIView):
    def get(self, request):
        input_data = request.query_params.dict()
        logger.info(f"Input data: {input_data}")
        vnp_secure_hash = input_data.pop('vnp_SecureHash', None)
        vnp_secure_hash_type = input_data.pop('vnp_SecureHashType', None)

        sorted_data = sorted(input_data.items())
        query_string = urllib.parse.urlencode(sorted_data)

        # Verify hash
        config = settings.VNPAY_CONFIG
        secret = config['vnp_HashSecret'].encode()
        message = query_string.encode()
        generated_hash = hmac.new(secret, message, hashlib.sha512).hexdigest()

        if vnp_secure_hash == generated_hash:
            # TODO: cập nhật trạng thái đơn hàng theo `vnp_TxnRef` trong DB nếu cần
            return Response({
                "status": "success",
                "message": "Payment verified",
                "data": input_data
            })
        else:
            return Response({
                "status": "error",
                "message": "Invalid hash"
            }, status=400)



