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
from rest_framework import generics, permissions, filters, pagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Category, Comment
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView, DetailView
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



class CategoryPostView(ListView):
    model = Post
    template_name = 'category_posts.html'
    context_object_name = 'posts'
    paginate_by = 5
    
    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        self.category = get_object_or_404(Category, slug=category_slug)
        return Post.objects.filter(
            category=self.category,
            status='PUBLISHED'
        ).select_related('author').order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        return context


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


from .serializers import (
    CategorySerializer, 
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentSerializer
)


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        # Only show published posts to non-staff users
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='PUBLISHED')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        
        # Track view count
        if self.object.status == 'PUBLISHED':
            ip_address = self.request.META.get('REMOTE_ADDR')
            PostView.objects.create(
                post=self.object,
                ip_address=ip_address,
                user=self.request.user if self.request.user.is_authenticated else None
            )
        
        return context


def search(request):
    query = request.GET.get('q', '')
    if query:
        results = Post.objects.filter(
            Q(status='PUBLISHED') &
            (Q(title__icontains=query) | 
             Q(content__icontains=query) |
             Q(summary__icontains=query))
        ).select_related('author', 'category').order_by('-published_at')
    else:
        results = Post.objects.none()
    
    # Pagination
    paginator = Paginator(results, 5)  # 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'categories': Category.objects.all()
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

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone


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
            'summary': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 200,
                'class': 'form-control',
                'placeholder': 'Enter a brief summary (max 200 characters)'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control',
                'placeholder': 'Write your post content here...'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'title': 'Post Title',
            'category': 'Category',
            'summary': 'Short Summary',
            'content': 'Post Content',
            'featured_image': 'Featured Image',
            'status': 'Post Status'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit category choices to only active categories if needed
        self.fields['category'].queryset = Category.objects.all()
        # Set initial status to DRAFT for staff users
        self.fields['status'].initial = 'DRAFT'

@login_required
def create_post(request):
    # Only staff users can create posts
    if request.user.role != 'STAFF':
        messages.error(request, "You don't have permission to create posts.")
        return redirect('index')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.author = request.user
                
                # If status is being submitted for review
                if form.cleaned_data['status'] == 'PENDING_REVIEW':
                    messages.info(request, "Your post has been submitted for review.")
                
                post.save()
                messages.success(request, "Post created successfully!")
                return redirect('staff_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error creating post: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm()
    
    return render(request, 'create_post.html', {
        'form': form,
        'categories': Category.objects.all()
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
    ).exclude(status='PENDING_REVIEW').order_by('-published_at')[:12]
    
    context = {
        'pending_posts': pending_posts,
        'reviewed_posts': reviewed_posts,
        'pending_count': pending_posts.count(),
    }
    return render(request, 'technical_dashboard.html', context)




from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from .models import Post, Category, PostView


class HomeView(ListView):
    model = Post
    template_name = 'index.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(
            status='PUBLISHED',
            published_at__isnull=False,
            published_at__lte=timezone.now()
        ).select_related('author', 'category').order_by('-published_at')
        
        # Handle search if query exists
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(summary__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured post (most recent)
        context['featured_post'] = self.get_queryset().first()
        
        # Popular posts (most viewed)
        context['popular_posts'] = Post.objects.filter(
            status='PUBLISHED',
            published_at__lte=timezone.now()
        ).annotate(view_count=Count('post_views')).order_by('-view_count')[:5]
        
        # Categories with counts
        context['categories'] = Category.objects.annotate(
            post_count=Count('post_category', 
                           filter=Q(post_category__status='PUBLISHED',
                                  post_category__published_at__lte=timezone.now())))
        
        # Search query
        context['query'] = self.request.GET.get('q', '')
        
        return context

# class HomeView(ListView):
#     model = Post
#     template_name = 'index.html'
#     context_object_name = 'posts'
#     paginate_by = 10  # 10 posts per page

#     def get_queryset(self):
#         # Get only published posts ordered by most recent
#         queryset = Post.objects.filter(
#             status='PUBLISHED',
#             published_at__lte=timezone.now()
#         ).select_related('author', 'category').order_by('-published_at')
        
#         # Get featured post (most recent published post)
#         self.featured_post = queryset.first()
        
#         # Exclude featured post from regular posts
#         if self.featured_post:
#             queryset = queryset.exclude(id=self.featured_post.id)
        
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['featured_post'] = self.featured_post


#         # Get all categories with published post counts
#         categories = Category.objects.annotate(post_count=Count('post_category', filter=Q(post_category__status='PUBLISHED')))
        
                                               
#         context['categories'] = categories

#         # Get popular posts (most viewed published posts)
#         context['popular_posts'] = Post.objects.filter(
#             status='PUBLISHED'
#         ).annotate(view_count=Count('post_views')).order_by('-view_count')[:5]

#         # Add today's date for filtering
#         context['today'] = timezone.now().date()

#         # return context
# views.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def search(request):
    query = request.GET.get('q', '')
    results = Post.objects.none()
    
    if query:
        results = Post.objects.filter(
            status='PUBLISHED',
            published_at__lte=timezone.now()
        ).filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(summary__icontains=query)
        ).select_related('author', 'category').order_by('-published_at')

    paginator = Paginator(results, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    categories = Category.objects.annotate(
        post_count=Count('post_category', 
                       filter=Q(post_category__status='PUBLISHED',
                              post_category__published_at__lte=timezone.now())))
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'categories': categories,
        'results_count': results.count()
    }
    return render(request, 'search.html', context)        


from django.shortcuts import get_object_or_404

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, status='PUBLISHED')
    
    if not request.user.is_authenticated or request.user != post.author:
        PostView.objects.create(
            post=post,
            ip_address=request.META.get('REMOTE_ADDR'),
            user=request.user if request.user.is_authenticated else None
        )
    
    return render(request, 'post_detail.html', {'post': post})