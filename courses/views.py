from rest_framework.decorators import action
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from django.db.models import Q
from courses import serializers
from rest_framework import viewsets, generics, status, parsers, permissions
from courses.models import ClassCategory, Course, Lesson, Comment, Tag, User, Like, Chat, Apointment
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

        return query



    @action(detail=True, methods=['get','post'], url_path='chats')
    def get_chats(self, request, pk=None):

        if request.method.__eq__('POST'):
            c = serializers.ChatSerializer(data={
                'message': request.data.get('message'),
                'user': request.user.pk,
                'course': pk
            })
            c.is_valid(raise_exception=True)
            d = c.save()
            return Response(serializers.ChatSerializer(d).data, status=status.HTTP_201_CREATED)
        chats = self.get_object().chat_set.filter(is_active=True).order_by('-created_at')
        return Response(serializers.ChatListSerializer(chats, many=True).data, status=status.HTTP_200_OK)

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


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
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


