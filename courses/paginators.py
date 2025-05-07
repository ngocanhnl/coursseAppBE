from rest_framework.pagination import PageNumberPagination


class ItemPagination(PageNumberPagination):
    page_size = 10

class CommentPagination(PageNumberPagination):
    page_size = 5
