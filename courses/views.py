from rest_framework.decorators import action
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from courses import serializers
from rest_framework import viewsets, generics, status, parsers, permissions
from courses.models import ClassCategory, Course, Lesson, Comment, Tag, User, Like, News, Apointment, Payment, Order, ExpoDevice
from courses.paginators import ItemPagination, CommentPagination
from courses.perm import CommentOwner, IsHLV
from courses.utils import notify_user


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
        print("request", request.user)

        lesson = Lesson.objects.select_related('course').get(id=pk)
        lesson.is_done = True
        lesson.save()

        students = lesson.course.students.all()

        notify_user(students, "Bài học đã hoàn thành",
                     f"Bài học '{lesson.title}' đã được giáo viên đánh dấu hoàn thành.")

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
        appointments = Apointment.objects.filter(
            Q(student_id=pk) | Q(teacher_id=pk),
            is_active=True
        )

        return Response(serializers.ApointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)

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



class OrderViewSet(viewsets.ViewSet, generics.CreateAPIView):
    serializer_class = serializers.OrderSerializer
    # permission_classes = [permissions.IsAuthenticated]



from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from datetime import datetime
import urllib.parse
import hmac
import hashlib
import random


class VNPayCreateUrl(APIView):
    def post(self, request):

        # Generate order details
        amount = request.data.get('amount')
        client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        print("Data", request.data)

        order_id = request.data.get('orderId', f"ORDER{random.randint(100000, 999999)}")
        print("orderId", order_id)
        current_order = Order.objects.filter(id=order_id).first()
        print("User pay", current_order.user_id)
        # amount = int(request.data.get('amount', random.randint(100000, 999999)))
        bank_code = request.data.get('bank_code', None)

        order_object = Order.objects.get(id=order_id)
        user_object = User.objects.get(id=current_order.user_id)
        # Construct the final payment URL

        payment = Payment.objects.create(
            order=order_object,
            amount=amount,
            # payment_url=payment_url,
            # vnp_txn_ref=vnp_TxnRef,
            user=user_object,  # đảm bảo endpoint có @authentication_classes
            status='pending'
        )

        config = settings.VNPAY_CONFIG
        vnp_TxnRef = order_id  # Using order_id as transaction reference for consistency
        vnp_Amount = (amount) * 100  # Convert to smallest currency unit (cents)
        vnp_OrderInfo = f"Thanh toan don hang {order_id}"
        vnp_ReturnUrl = "https://f342-2001-ee0-4f42-2f20-34fb-694d-6a47-61da.ngrok-free.app/payment/vnpay-return/?paymentId="+str(payment.id)
        # vnp_ReturnUrl = "https://5ed7-2001-ee0-4f01-2ec0-3c2b-72b7-3457-5400.ngrok-free.app/payment/vnpay-return/"
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

        # order_object = Order.objects.get(id=order_id)
        # user_object = User.objects.get(id=7)
        # # Construct the final payment URL
        #
        # payment = Payment.objects.create(
        #     order=order_object,
        #     amount=amount,
        #     # payment_url=payment_url,
        #     # vnp_txn_ref=vnp_TxnRef,
        #     user=user_object,  # đảm bảo endpoint có @authentication_classes
        #     status='pending'
        # )
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
        raw_query = request.META['QUERY_STRING']
        full_data = dict(urllib.parse.parse_qsl(raw_query))
        vnp_secure_hash = full_data.pop('vnp_SecureHash', None)
        vnp_secure_hash_type = full_data.pop('vnp_SecureHashType', None)

        # Không đưa paymentId vào khi tính hash
        input_data = {k: v for k, v in full_data.items() if k != 'paymentId'}

        logger.info(f"Input data: {input_data}")
        print("32113123", input_data)
        # vnp_secure_hash = input_data.pop('vnp_SecureHash', None)
        # vnp_secure_hash_type = input_data.pop('vnp_SecureHashType', None)

        sorted_data = sorted(input_data.items())
        query_string = urllib.parse.urlencode(sorted_data)


        # Verify hash
        config = settings.VNPAY_CONFIG
        secret = config['vnp_HashSecret'].encode()
        message = query_string.encode()
        generated_hash = hmac.new(secret, query_string.encode(), hashlib.sha512).hexdigest()
        paymentId = full_data.get('paymentId')


        payment = Payment.objects.get(id=paymentId)
        print("payment", payment)
        print("Hash từ VNPay:", vnp_secure_hash)
        print("Hash tự tạo:", generated_hash)
        print("So sánh:", vnp_secure_hash == generated_hash)
        print("PAYMENT ID:", paymentId)
        print("TRƯỚC khi cập nhật trạng thái:", payment.status)

        if vnp_secure_hash == generated_hash:
            if payment.status != "completed":
                payment.status = "completed"
                payment.save()
                return Response({
                    "status": "success",
                    "message": "Payment completed"
                })

        # Nếu sai hash nhưng status đã completed rồi => đừng fail
        if payment.status == "completed":
            return Response({
                "status": "success",
                "message": "Already completed",
                "data": input_data
            })

        # Trường hợp hash sai + chưa completed => mark failed
        payment.status = "failed"
        payment.save()
        return Response({
            "status": "error",
            "message": "Invalid hash or payment not completed"
        }, status=400)



class ExpoDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.ExpoDeviceSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            ExpoDevice.objects.update_or_create(user=request.user, defaults={'token': token})
            return Response({'status': 'Token saved'})
        print("❌ Serializer Error:", serializer.errors)
        return Response(serializer.errors, status=400)

class DiscountViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    serializer_class = serializers.DiscountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        discount = serializer.save(user=request.user)
        return Response(serializers.DiscountSerializer(discount).data, status=status.HTTP_201_CREATED)

