from rest_framework import serializers
from .models import Category, Post, Comment
from django.contrib.auth import get_user_model
from .models import User, StaffProfile, TechnicalProfile, Category, Post
User = get_user_model()
from .models import Post, User



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_verified']



class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = StaffProfile
        fields = '__all__'
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(role='STAFF', **user_data)
        return StaffProfile.objects.create(user=user, **validated_data)
    
class TechnicalProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = TechnicalProfile
        fields = '__all__'
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(role='TECHNICAL', **user_data)
        return TechnicalProfile.objects.create(user=user, **validated_data)



class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'published_at', 'reviewed_by']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']

class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'summary', 'featured_image', 
            'author', 'category', 'publish_date', 'comment_count'
        ]
    
    def get_comment_count(self, obj):
        return obj.comments.count()

class PostDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = '__all__'
    
    def get_comments(self, obj):
        comments = obj.comments.filter(active=True)
        return CommentSerializer(comments, many=True).data

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']



class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'category', 'summary', 'content', 'featured_image', 'status', 'publish_date']
        
    def create(self, validated_data):
        # Automatically set the author to the current user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)