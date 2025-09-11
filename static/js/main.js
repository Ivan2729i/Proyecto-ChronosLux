// Main JavaScript functionality
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  const lucide = window.lucide; // Declare the lucide variable
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
});

// Tailwind configuration
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#1e3a8a',
                'primary-foreground': '#ffffff',
                secondary: '#d4af37',
                'secondary-foreground': '#1e3a8a',
                background: '#ffffff',
                foreground: '#1f2937',
                muted: '#f3f4f6',
                'muted-foreground': '#6b7280',
                border: '#e5e7eb'
            },
            fontFamily: {
                'serif': ['Montserrat', 'serif'],
                'sans': ['Open Sans', 'sans-serif']
            }
        }
    }
}
