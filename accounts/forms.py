from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from watches.models import Domicilio

User = get_user_model()

# --- INICIO: LÓGICA COMPLETA DEL LOGIN ---

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

    def clean_password2(self):
        return (self.cleaned_data.get("password2") or "")

    def clean(self):
        cleaned_data = super().clean()
        password_1 = cleaned_data.get("password1")

        if password_1:
            try:
                validate_password(password_1, self.instance)
            except forms.ValidationError as error:
                self.add_error('password1', error.messages)

        return cleaned_data

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.email      = self.cleaned_data["email"].strip().lower()
        if hasattr(user, "username") and not getattr(user, "username", None):
            user.username = (user.email.split("@")[0])[:150]
        if commit:
            user.save()
        return user

# --- FIN: LÓGICA COMPLETA DEL LOGIN ---

# --- INICIO: LÓGICA COMPLETA DE REGISTRO DOMICILIOS ---

class DomicilioForm(forms.ModelForm):
    class Meta:
        model = Domicilio
        exclude = ['usuario']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'calle': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'num_ext': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'num_int': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'colonia': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'estado': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'cp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
            'pais': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            if not telefono.isdigit():
                raise forms.ValidationError("El teléfono solo puede contener números.")
            if len(telefono) != 10:
                raise forms.ValidationError("El teléfono debe tener exactamente 10 dígitos.")
        return telefono

    def clean_num_ext(self):
        num_ext = self.cleaned_data.get('num_ext')
        if num_ext and not num_ext.isdigit():
            raise forms.ValidationError("El número exterior solo puede contener números.")
        return num_ext

    def clean_num_int(self):
        num_int = self.cleaned_data.get('num_int')
        if num_int and not num_int.isdigit():
            raise forms.ValidationError("El número interior solo puede contener números.")
        return num_int

    def clean_estado(self):
        estado = self.cleaned_data.get('estado')
        if estado and not re.match(r'^[a-zA-Z\sáéíóúÁÉÍÓÚñÑ]+$', estado):
            raise forms.ValidationError("El estado solo puede contener letras, acentos y espacios.")
        return estado

    def clean_cp(self):
        cp = self.cleaned_data.get('cp')
        if cp:
            if not cp.isdigit():
                raise forms.ValidationError("El Código Postal solo puede contener números.")
            if len(cp) != 5:
                raise forms.ValidationError("El Código Postal debe tener exactamente 5 dígitos.")
        return cp

    def clean_pais(self):
        pais = self.cleaned_data.get('pais')
        if pais and not re.match(r'^[a-zA-Z\sáéíóúÁÉÍÓÚñÑ]+$', pais):
            raise forms.ValidationError("El país solo puede contener letras, acentos y espacios.")
        return pais