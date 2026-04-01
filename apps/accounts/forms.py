from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User, VerificationStatus


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Password",
            }
        )
    )

    error_messages = {
        "invalid_login": "Invalid username or password.",
        "inactive": "This account is inactive.",
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )

            if self.user_cache is None:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    raise self.get_invalid_login_error()

                if user.check_password(password):
                    if user.verification_status == VerificationStatus.PENDING:
                        raise forms.ValidationError(
                            "Your account is awaiting administrator verification.",
                            code="inactive",
                        )
                    elif user.verification_status == VerificationStatus.REJECTED:
                        raise forms.ValidationError(
                            "Your account request was rejected. Please contact the administrator.",
                            code="inactive",
                        )
                    elif not user.is_active:
                        raise forms.ValidationError(
                            "This account is inactive.",
                            code="inactive",
                        )

                raise self.get_invalid_login_error()

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            if user.verification_status == VerificationStatus.PENDING:
                raise forms.ValidationError(
                    "Your account is awaiting administrator verification.",
                    code="inactive",
                )
            elif user.verification_status == VerificationStatus.REJECTED:
                raise forms.ValidationError(
                    "Your account request was rejected. Please contact the administrator.",
                    code="inactive",
                )
            raise forms.ValidationError(
                "This account is inactive.",
                code="inactive",
            )


class StaffSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "employee_id",
            "role",
            "password1",
            "password2",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "username": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "phone_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "employee_id": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "role": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input input-bordered w-full"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input input-bordered w-full"})
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.is_verified_staff = False
        user.verification_status = VerificationStatus.PENDING

        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "profile_picture",
            "shift_start",
            "shift_end",
            "shift_days",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "phone_number": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "shift_start": forms.TimeInput(
                attrs={"class": "input input-bordered w-full", "type": "time"}
            ),
            "shift_end": forms.TimeInput(
                attrs={"class": "input input-bordered w-full", "type": "time"}
            ),
            "shift_days": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": 'Example: ["Monday", "Tuesday"]',
                }
            ),
        }