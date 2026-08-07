from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.validators import (
    validate_email_required,
    validate_password_strength,
    validate_phone,
    validate_username,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_display",
            "phone",
            "department",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
            "role_display",
            "full_name",
        )

    def get_full_name(self, obj: User) -> str:
        name = obj.get_full_name().strip()
        return name or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone",
            "department",
            "is_active",
            "is_staff",
        )

    def validate_username(self, value):
        username = validate_username(value)
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Cet identifiant est déjà utilisé.")
        return username

    def validate_email(self, value):
        email = validate_email_required(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return email

    def validate_phone(self, value):
        return validate_phone(value)

    def validate_password(self, value):
        password = validate_password_strength(value)
        validate_password(password)
        return password

    def create(self, validated_data):
        from apps.accounts.services.users import user_create

        return user_create(actor=getattr(self.context.get("request"), "user", None), **validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=8,
        style={"input_type": "password"},
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone",
            "department",
            "is_active",
            "is_staff",
        )

    def validate_email(self, value):
        email = validate_email_required(value)
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return email

    def validate_phone(self, value):
        return validate_phone(value)

    def validate_password(self, value):
        if not value:
            return value
        password = validate_password_strength(value)
        validate_password(password, user=self.instance)
        return password

    def update(self, instance, validated_data):
        from apps.accounts.services.users import user_update

        password = validated_data.pop("password", None)
        if password == "":
            password = None
        data = dict(validated_data)
        if password:
            data["password"] = password
        return user_update(
            user=instance,
            data=data,
            actor=getattr(self.context.get("request"), "user", None),
        )


class MeSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = UserSerializer.Meta.read_only_fields + (
            "username",
            "role",
            "is_staff",
            "is_active",
        )
