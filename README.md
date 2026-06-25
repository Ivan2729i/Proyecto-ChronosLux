# ChronosLux ⌚✨

Bienvenido a ChronosLux, un proyecto de eCommerce completamente funcional desarrollado con Django, enfocado en la venta de relojes de lujo. Este sitio web ofrece una experiencia de usuario completa, desde la navegación por el catálogo hasta la finalización de la compra y la gestión de la cuenta.

---

## 🚀 Características (Features)

Este proyecto implementa un flujo de eCommerce completo, incluyendo:

* **Catálogo de Productos:** Navegación por un catálogo completo y una sección de relojes exclusivos, con filtros dinámicos por tipo, género, marca y precio.
* **Buscador Funcional:** Una barra de búsqueda en el `navbar` para encontrar productos por nombre, marca o descripción.
* **Sistema de Autenticación Completo:**
    * Registro de nuevos usuarios con validaciones de datos.
    * Inicio y cierre de sesión.
    * Recuperación de contraseña por correo electrónico.
* **Carrito de Compras Persistente:**
    * Los usuarios logueados guardan su carrito en la base de datos, persistiendo entre sesiones.
    * Los usuarios anónimos usan un carrito temporal basado en la sesión de Django.
* **Página de Detalles del Producto:** Vista detallada de cada reloj con sus especificaciones y una sección de reseñas.
* **Sistema de Reseñas y Favoritos:**
    * Los usuarios pueden dejar una calificación por estrellas y un comentario por producto (una reseña por usuario).
    * Funcionalidad para marcar relojes como favoritos y verlos en una página personal.
* **Flujo de Compra Completo (Checkout):**
    * Resumen del pedido.
    * Gestión de domicilios (CRUD: Crear, Ver, Editar, Eliminar direcciones).
    * Selección de método de pago y creación de un `Pedido` en la base de datos.
    * Validación de stock para evitar ventas de productos agotados.
* **Panel de Administración Personalizado:**
    * Un panel de control para administradores (`is_staff`) con acceso a un CRUD completo para gestionar los productos del inventario.
* **Gestión de Devoluciones:**
    * Los usuarios pueden solicitar devoluciones de sus compras desde su historial.
    * Los administradores pueden ver y gestionar estas solicitudes (Aceptar/Rechazar).

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Django
* **Base de Datos:** MongoDB
* **Frontend:** HTML, CSS, Tailwind CSS, JavaScript
* **Librerías Clave de Python:**
    * `Pillow` (para el manejo de imágenes)

---

## ⚙️ Instalación y Puesta en Marcha

Sigue estos pasos para correr el proyecto en un entorno local.

### Prerrequisitos
* Python 3.x
* pip (gestor de paquetes de Python)
* Un servidor de MongoDB

### Pasos

1.  **Clona el repositorio:**
    ```bash
    git clone [URL_DE_TU_REPOSITORIO]
    cd ChronosLux
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    python -m venv .venv
    # En Windows
    .\.venv\Scripts\activate
    # En macOS/Linux
    source .venv/bin/activate
    ```

3.  **Instala las dependencias:**
    
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura la base de datos:**
    * Crea una base de datos en MongoDB llamada `chronoslux`.
    * En el archivo `.env`, actualiza los datos de `DATABASES` con tu usuario y contraseña de MongoDB.

5.  **Aplica las migraciones:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Crea un superusuario (administrador):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Inicia el servidor de desarrollo:**
    ```bash
    python manage.py runserver
    ```
    ¡Ahora puedes visitar `http://127.0.0.1:8000/` en tu navegador!

---

## 👤 Contacto
Iván Paz Valladares

[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ivan-paz-valladares-b8886a343)

