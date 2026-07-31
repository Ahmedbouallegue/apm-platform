from django.contrib.auth import get_user_model
from rest_framework import serializers

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

    def create(self, validated_data):
        from apps.accounts.services.users import user_create

        return user_create(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=8,
        style={"input_type": "password"},
    )

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

    def update(self, instance, validated_data):
        from apps.accounts.services.users import user_update

        password = validated_data.pop("password", None)
        if password == "":
            password = None
        data = dict(validated_data)
        if password:
            data["password"] = password
        return user_update(user=instance, data=data)


class MeSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = UserSerializer.Meta.read_only_fields + (
            "username",
            "role",
            "is_staff",
            "is_active",
        )
