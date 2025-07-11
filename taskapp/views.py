from django.utils import timezone
from rest_framework import generics, permissions, filters, pagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Post
from django import forms
from django.contrib.auth import logout
from django.contrib import messages
from rest_framework.permissions import *
User = get_user_model()

from .serializers import (
    CategorySerializer,
    UserSerializer,
    StaffProfileSerializer,
    TechnicalProfileSerializer, 
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer
)


def index(request):
    return render(request,"index.html")


# Custom pagination class
class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100



class PostListView(generics.ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['publish_date', 'created_at', 'views']
    ordering = ['-publish_date']

    def get_queryset(self):
        queryset = Post.objects.filter(
            status='published',
            publish_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('comments')
        return queryset

# ... rest of your view classes ...from django.utils import timezone
from rest_framework import generics, permissions, filters, pagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Category, Comment

from .serializers import (
    CategorySerializer, 
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer
)

# Custom pagination class
class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostListView(generics.ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['publish_date', 'created_at', 'views']
    ordering = ['-publish_date']

    def get_queryset(self):
        queryset = Post.objects.filter(
            status='published',
            publish_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('comments')
        return queryset


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Track view
        ip_address = request.META.get('REMOTE_ADDR')
        PostView.objects.create(
            post=instance,
            ip_address=ip_address,
            user=request.user if request.user.is_authenticated else None
        )
        
        return Response(serializer.data)

# views.py
def search(request):
    query = request.GET.get('q', '')
    if query:
        results = Post.objects.filter(
            status='PUBLISHED',
            title__icontains=query
        ) | Post.objects.filter(
            status='PUBLISHED',
            content__icontains=query
        )
    else:
        results = Post.objects.none()
    
    context = {
        'query': query,
        'results': results
    }
    return render(request, 'search.html', context)

class PostCreateView(generics.CreateAPIView):
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Only staff users can create posts
        if not self.request.user.role == 'STAFF':
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)




class PostUpdateView(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class PostDeleteView(generics.DestroyAPIView):
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post = generics.get_object_or_404(Post, slug=self.kwargs['slug'])
        serializer.save(user=self.request.user, post=post)



class StaffSignupView(generics.CreateAPIView):
    serializer_class = StaffProfileSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Check if user already exists
        email = request.data.get('user', {}).get('email')
        if email and User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)

class TechnicalSignupView(generics.CreateAPIView):
    serializer_class = TechnicalProfileSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Check if user already exists
        email = request.data.get('user', {}).get('email')
        if email and User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


@login_required
def staff_dashboard(request):
    # Only staff users can access this
    if request.user.role != 'STAFF':
        return redirect('index')
    
    # Get posts created by this staff member
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    # If no posts, show a message instead of empty list
    no_posts = not user_posts.exists()
    
    context = {
        'posts': user_posts,
        'draft_count': user_posts.filter(status='DRAFT').count(),
        'pending_count': user_posts.filter(status='PENDING_REVIEW').count(),
        'published_count': user_posts.filter(status='PUBLISHED').count(),
        'no_posts': no_posts
    }
    return render(request, 'staff_dashboard.html', context)




@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')




@login_required
def review_post(request, post_id):
    # Only technical users can review posts
    if request.user.role != 'TECHNICAL':
        return redirect('index')
    
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('review_comment', '')
        
        if action == 'approve':
            post.status = 'PUBLISHED'
            post.reviewed_by = request.user
            post.published_at = timezone.now()
            post.save()
            messages.success(request, "Post approved and published successfully!")
            
        elif action == 'reject':
            post.status = 'REJECTED'
            post.reviewed_by = request.user
            post.save()
            messages.success(request, "Post has been rejected.")
            
        elif action == 'request_revision':
            post.status = 'DRAFT'
            post.reviewed_by = request.user
            post.save()
            messages.success(request, "Author has been requested to revise the post.")
            
        return redirect('technical_dashboard')
    
    return render(request, 'review_post.html', {'post': post})


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'category', 'summary', 'content', 'featured_image', 'status']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3, 'maxlength': 200}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }




        labels = {
            'title': 'Post Title',
            'category': 'Category',
            'summary': 'Short Summary',
            'content': 'Post Content',
            'featured_image': 'Featured Image',
            'status': 'Post Status'
        }


@login_required
def create_post(request):
    # Only staff users can create posts
    if request.user.role != 'STAFF':
        return redirect('index')
    
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create but don't save yet
                post = form.save(commit=False)
                
                # Set author
                post.author = request.user
                
                # Save to database
                post.save()
                
                messages.success(request, "Post created successfully!")
                return redirect('staff_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error creating post: {str(e)}")
        else:
            # Collect form errors
            errors = form.errors.as_text()
            messages.error(request, f"Please correct the errors: {errors}")
    else:
        form = PostForm()
    
    return render(request, 'create_post.html', {
        'form': form,
        'categories': categories
    })




@login_required
def technical_dashboard(request):
    # Only technical users can access this
    if request.user.role != 'TECHNICAL':
        return redirect('index')
    
    # Get posts pending review
    pending_posts = Post.objects.filter(status='PENDING_REVIEW').order_by('-created_at')
    
    # Get recently reviewed posts
    reviewed_posts = Post.objects.filter(
        reviewed_by=request.user
    ).exclude(status='PENDING_REVIEW').order_by('-published_at')[:5]
    
    context = {
        'pending_posts': pending_posts,
        'reviewed_posts': reviewed_posts,
        'pending_count': pending_posts.count(),
    }
    return render(request, 'technical_dashboard.html', context)
