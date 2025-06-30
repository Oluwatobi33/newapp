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
from .models import User, StaffProfile, TechnicalProfile
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect


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

# ... rest of your view classes ...



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




# @login_required
# def create_post(request):
#     # Only staff users can create posts
#     if request.user.role != 'STAFF':
#         return redirect('home')
    
#     if request.method == 'POST':
#         # Process form data and create post
#         # ... your implementation here ...
        
#         # For now, redirect to dashboard
#         return redirect('staff_dashboard')
    
#     return render(request, 'create_post.html')

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

from rest_framework.permissions import IsAuthenticated

# class StaffDashboardView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role != 'STAFF':
#             return Response(
#                 {"error": "Access denied"}, 
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         # Return staff-specific data
#         return Response({
#             "pending_posts": Post.objects.filter(author=request.user, status='DRAFT').count(),
#             "published_posts": Post.objects.filter(author=request.user, status='PUBLISHED').count(),
#             # ... other staff data ...
#         })

# class TechnicalDashboardView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role != 'TECHNICAL':
#             return Response(
#                 {"error": "Access denied"}, 
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         # Return technical-specific data
#         return Response({
#             "pending_reviews": Post.objects.filter(status='PENDING_REVIEW').count(),
#             "recent_activity": Post.objects.filter(reviewed_by=request.user).order_by('-published_at')[:5],
#             # ... other technical data ...
#         })

# class LoginView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def post(self, request, format=None):
#         email = request.data.get('email')
#         password = request.data.get('password')
        
#         user = authenticate(request, username=email, password=password)
#         if user is not None:
#             if user.is_verified:
#                 login(request, user)
#                 return Response({"detail": "Login successful"}, status=status.HTTP_200_OK)
#             else:
#                 # Generate and send OTP
#                 otp = user.generate_otp()
#                 self.send_otp_email(user.email, otp)
#                 return Response(
#                     {
#                         "detail": "OTP sent to your email",
#                         "user_id": user.id
#                     },
#                     status=status.HTTP_200_OK
#                 )
#         else:
#             return Response(
#                 {"error": "Invalid credentials"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
    
#     def send_otp_email(self, email, otp_code):
#         subject = "Your OTP Code for Verification"
#         message = f"""
#         Hello,

#         Your One-Time Password (OTP) for verifying your account is:

#         🔐 {otp_code}

#         This OTP will expire in 30 minutes.

#         If you did not request this, please ignore this email. 

#         Best regards,  
#         News Blog Team
#         """
#         from_email = settings.EMAIL_HOST_USER
#         recipient_list = [email]

#         try:
#             send_mail(subject, message, from_email, recipient_list, fail_silently=False)
#             return True
#         except Exception as e:
#             print(f"Failed to send OTP email: {e}")
#             return False


# class VerifyOTPView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def post(self, request, format=None):
#         user_id = request.data.get('user_id')
#         otp = request.data.get('otp')
        
#         try:
#             user = User.objects.get(id=user_id)
#             if user.verify_otp(otp):
#                 login(request, user)
#                 return Response(
#                     {
#                         "detail": "OTP verified successfully",
#                         "user": UserSerializer(user).data
#                     },
#                     status=status.HTTP_200_OK
#                 )
#             else:
#                 return Response(
#                     {"error": "Invalid or expired OTP"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         except User.DoesNotExist:
#             return Response(
#                 {"error": "User not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Post
from django import forms

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

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'category', 'summary', 'content', 'featured_image', 'status']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
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

from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')



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

@login_required
def create_post(request):
    # Only staff users can create posts
    if request.user.role != 'STAFF':
        return redirect('index')
    
    categories = Category.objects.all()
    error = None
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create but don't save yet
                post = form.save(commit=False)
                
                # Set additional fields
                post.author = request.user
                post.slug = slugify(form.cleaned_data['title'])
                
                # Save to database
                post.save()
                
                return redirect('staff_dashboard')
                
            except Exception as e:
                error = f"Error creating post: {str(e)}"
        else:
            error = "Please correct the errors below"
    else:
        form = PostForm()
    
    return render(request, 'create_post.html', {
        'form': form,
        'categories': categories,
        'error': error
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
