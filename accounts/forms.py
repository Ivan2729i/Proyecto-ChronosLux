from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
import re

User = get_user_model()

# ---------- Reglas / Regex ----------
NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' ]+$")
PWD_RE  = re.compile(
    r"""
    ^
    (?=.*[a-z])        # al menos una minúscula
    (?=.*[A-Z])        # al menos una mayúscula
    (?=.*\d)           # al menos un número
    (?=.*[^A-Za-z0-9]) # al menos un caracter especial
    .{8,}              # mínimo 8
    $
    """,
    re.VERBOSE
)

def _require_letters_min2(value: str, label: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError(f"{label} es requerido.")
    if len(v) < 2:
        raise ValidationError(f"{label} debe tener al menos 2 caracteres.")
    if not NAME_RE.match(v):
        raise ValidationError(f"{label} solo puede contener letras, acentos o espacios.")
    # Si puso varias palabras en NOMBRE, cada una debe tener >=2
    parts = [p for p in re.split(r"\s+", v) if p]
    for p in parts:
        if len(p) < 2:
            raise ValidationError(f"Cada parte de {label} debe tener al menos 2 caracteres.")
    return v

def _require_two_surnames(value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError("Apellidos son requeridos.")
    if not NAME_RE.match(v):
        raise ValidationError("Apellidos solo pueden contener letras, acentos o espacios.")
    parts = [p for p in re.split(r"\s+", v) if p]
    if len(parts) != 2:
        raise ValidationError("Debes ingresar dos apellidos (paterno y materno).")
    for p in parts:
        if len(p) < 2:
            raise ValidationError("Cada apellido debe tener al menos 2 caracteres.")
    return v

def _validate_password_strength(pwd: str):
    if not PWD_RE.match(pwd or ""):
        raise ValidationError(
            "La contraseña debe tener mínimo 8 caracteres e incluir al menos: "
            "una mayúscula, una minúscula, un número y un carácter especial."
        )

# ---------- Formularios ----------
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={
            "placeholder": "ejemplo@correo.com",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "invalid": "Ingresa un correo válido.",
            "required": "El correo es requerido.",
        }
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "••••••••",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "required": "La contraseña es requerida.",
        }
    )

class SignupForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Tu nombre",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "required": "El nombre es requerido.",
            "max_length": "El nombre es demasiado largo.",
        }
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Tus apellidos (dos palabras)",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "required": "Los apellidos son requeridos.",
            "max_length": "Los apellidos son demasiado largos.",
        }
    )
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={
            "placeholder": "ejemplo@correo.com",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "invalid": "Ingresa un correo válido.",
            "required": "El correo es requerido.",
        }
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "••••••••",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "required": "La contraseña es requerida.",
        }
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "••••••••",
            "class": "mt-1 block w-full border rounded-md shadow-sm p-2 border-gray-300"
        }),
        error_messages={
            "required": "Debes repetir la contraseña.",
        }
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["first_name", "last_name", "email", "password1", "password2"])

    # ---- Validaciones de campos ----
    def clean_first_name(self):
        return _require_letters_min2(self.cleaned_data.get("first_name"), "Nombre")

    def clean_last_name(self):
        return _require_two_surnames(self.cleaned_data.get("last_name"))

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("El correo es requerido.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean_password1(self):
        p1 = self.cleaned_data.get("password1") or ""
        _validate_password_strength(p1)
        return p1

    # Evitar MENSAJES en inglés en password2: no validamos aquí.
    def clean_password2(self):
        return (self.cleaned_data.get("password2") or "")

    # Comparamos nosotros y ponemos el mensaje SOLO en password1
    def clean(self):
        cleaned = forms.ModelForm.clean(self)  # no llamamos al clean de UserCreationForm
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if not p1 or not p2:
            self.add_error("password1", "Debes ingresar y repetir la contraseña.")
            return cleaned
        if p1 != p2:
            self.add_error("password1", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        # Saltamos save de UserCreationForm para no reactivar validaciones por defecto
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.email      = self.cleaned_data["email"].strip().lower()
        if hasattr(user, "username") and not getattr(user, "username", None):
            user.username = (user.email.split("@")[0])[:150]
        if commit:
            user.save()
        return user
