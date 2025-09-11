// Main JavaScript for luxury watch ecommerce

// Cart functionality
let cart = []
let isCartOpen = false

// Watch data
const watches = [
  {
    id: 1,
    name: "Submariner Date",
    brand: "ROLEX",
    price: 12550,
    image: "../src/img/rolex-submariner.jpg",
    category: "rolex",
    rating: 4.9,
    features: ["Resistente al agua hasta 300m", "Movimiento automático perpetuo"],
  },
  {
    id: 2,
    name: "Speedmaster Professional",
    brand: "OMEGA",
    price: 6350,
    image: "../src/img/omega-speedmaster.jpg",
    category: "omega",
    rating: 4.8,
    features: ["El reloj lunar oficial", "Cronógrafo manual legendario"],
  },
  {
    id: 3,
    name: "Calatrava",
    brand: "PATEK PHILIPPE",
    price: 32100,
    image: "../src/img/patek-philippe-calatrava.jpg",
    category: "patek",
    rating: 5.0,
    features: ["Elegancia pura en oro rosa", "Movimiento mecánico de manufactura"],
  },
  {
    id: 4,
    name: "Daytona",
    brand: "ROLEX",
    price: 18750,
    image: "../src/img/rolex-daytona.jpg",
    category: "rolex",
    rating: 4.9,
    features: ["Cronógrafo de carreras", "Bisel de cerámica"],
  },
  {
    id: 5,
    name: "Seamaster Planet Ocean",
    brand: "OMEGA",
    price: 8200,
    image: "../src/img/omega-seamaster.jpg",
    category: "omega",
    rating: 4.7,
    features: ["Resistente hasta 600m", "Movimiento Co-Axial"],
  },
  {
    id: 6,
    name: "Nautilus",
    brand: "PATEK PHILIPPE",
    price: 45900,
    image: "../src/img/patek-philippe-nautilus.jpg",
    category: "patek",
    rating: 5.0,
    features: ["Icónico diseño deportivo", "Acero inoxidable premium"],
  },
]

// DOM elements
const cartBtn = document.getElementById("cart-btn")
const cartModal = document.getElementById("cart-modal")
const closeCartBtn = document.getElementById("close-cart")
const cartCount = document.getElementById("cart-count")
const cartItems = document.getElementById("cart-items")
const cartTotal = document.getElementById("cart-total")
const mobileMenuBtn = document.getElementById("mobile-menu-btn")
const mobileMenu = document.getElementById("mobile-menu")
const menuIcon = document.getElementById("menu-icon")
const closeIcon = document.getElementById("close-icon")
const watchGrid = document.getElementById("watch-grid")
const filterBtns = document.querySelectorAll(".filter-btn")

// Initialize the app
document.addEventListener("DOMContentLoaded", () => {
  initializeEventListeners()
  populateWatchGrid()
  updateCartUI()
})

// Event listeners
function initializeEventListeners() {
  // Cart modal
  cartBtn.addEventListener("click", openCart)
  closeCartBtn.addEventListener("click", closeCart)
  cartModal.addEventListener("click", (e) => {
    if (e.target === cartModal) {
      closeCart()
    }
  })

  // Mobile menu
  mobileMenuBtn.addEventListener("click", toggleMobileMenu)

  // Filter buttons
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const filter = this.dataset.filter
      filterWatches(filter)

      // Update active button
      filterBtns.forEach((b) => b.classList.remove("active"))
      this.classList.add("active")
    })
  })

  // Add to cart buttons (delegated event listener)
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("add-to-cart")) {
      const watchData = JSON.parse(e.target.dataset.watch)
      addToCart(watchData)
    }
  })

  // Smooth scrolling for navigation links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })
}

// Mobile menu toggle
function toggleMobileMenu() {
  const isOpen = !mobileMenu.classList.contains("hidden")

  if (isOpen) {
    mobileMenu.classList.add("hidden")
    menuIcon.classList.remove("hidden")
    closeIcon.classList.add("hidden")
  } else {
    mobileMenu.classList.remove("hidden")
    menuIcon.classList.add("hidden")
    closeIcon.classList.remove("hidden")
  }
}

// Cart functions
function openCart() {
  cartModal.classList.remove("hidden")
  cartModal.classList.add("show")
  isCartOpen = true
  document.body.style.overflow = "hidden"
}

function closeCart() {
  cartModal.classList.remove("show")
  setTimeout(() => {
    cartModal.classList.add("hidden")
  }, 300)
  isCartOpen = false
  document.body.style.overflow = "auto"
}

function addToCart(watch) {
  const existingItem = cart.find((item) => item.id === watch.id)

  if (existingItem) {
    existingItem.quantity += 1
  } else {
    cart.push({
      ...watch,
      quantity: 1,
    })
  }

  updateCartUI()

  // Show success feedback
  showNotification(`${watch.name} agregado al carrito`)
}

function removeFromCart(id) {
  cart = cart.filter((item) => item.id !== id)
  updateCartUI()
}

function updateQuantity(id, quantity) {
  if (quantity === 0) {
    removeFromCart(id)
    return
  }

  const item = cart.find((item) => item.id === id)
  if (item) {
    item.quantity = quantity
    updateCartUI()
  }
}

function updateCartUI() {
  // Update cart count
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0)
  cartCount.textContent = totalItems

  if (totalItems > 0) {
    cartCount.classList.remove("hidden")
  } else {
    cartCount.classList.add("hidden")
  }

  // Update cart items
  if (cart.length === 0) {
    cartItems.innerHTML = '<p class="text-gray-500 text-center">Tu carrito está vacío</p>'
  } else {
    cartItems.innerHTML = cart
      .map(
        (item) => `
            <div class="flex items-center space-x-4 mb-4 p-4 border rounded-lg">
                <img src="${item.image}" alt="${item.name}" class="w-16 h-16 object-cover rounded">
                <div class="flex-1">
                    <h4 class="font-semibold">${item.name}</h4>
                    <p class="text-sm text-gray-600">${item.brand}</p>
                    <p class="font-bold">$${item.price.toLocaleString()}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="updateQuantity(${item.id}, ${item.quantity - 1})" class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">-</button>
                    <span class="w-8 text-center">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, ${item.quantity + 1})" class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">+</button>
                </div>
                <button onclick="removeFromCart(${item.id})" class="text-red-500 hover:text-red-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        `,
      )
      .join("")
  }

  // Update total
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
  cartTotal.textContent = `$${total.toLocaleString()}`
}

// Watch grid and filtering
function populateWatchGrid() {
  watchGrid.innerHTML = watches.map((watch) => createWatchCard(watch)).join("")
}

function createWatchCard(watch) {
  const stars = "★".repeat(Math.floor(watch.rating)) + (watch.rating % 1 ? "☆" : "")

  return `
        <div class="watch-card group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden" data-category="${watch.category}">
            <div class="aspect-square overflow-hidden">
                <img src="${watch.image}" alt="${watch.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
            </div>
            <div class="p-6">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-semibold" style="color: oklch(0.85 0.15 85);">${watch.brand}</span>
                    <div class="flex items-center">
                        <span class="text-yellow-400">${stars}</span>
                        <span class="text-sm text-gray-500 ml-1">(${watch.rating})</span>
                    </div>
                </div>
                <h3 class="text-xl font-bold mb-2" style="color: oklch(0.12 0.08 240);">${watch.name}</h3>
                <p class="text-gray-600 text-sm mb-4">${watch.features.join(", ")}</p>
                <div class="flex items-center justify-between">
                    <span class="text-2xl font-bold" style="color: oklch(0.12 0.08 240);">$${watch.price.toLocaleString()}</span>
                    <button class="add-to-cart px-4 py-2 rounded-lg font-semibold transition-colors" style="background-color: oklch(0.85 0.15 85); color: oklch(0.12 0.08 240);" data-watch='${JSON.stringify(watch)}'>
                        Agregar
                    </button>
                </div>
            </div>
        </div>
    `
}

function filterWatches(category) {
  const watchCards = document.querySelectorAll(".watch-card")

  watchCards.forEach((card) => {
    if (category === "all" || card.dataset.category === category) {
      card.style.display = "block"
      card.style.animation = "fade-in 0.5s ease-out"
    } else {
      card.style.display = "none"
    }
  })
}

// Notification system
function showNotification(message) {
  const notification = document.createElement("div")
  notification.className =
    "fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300"
  notification.textContent = message

  document.body.appendChild(notification)

  // Animate in
  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)

  // Animate out and remove
  setTimeout(() => {
    notification.style.transform = "translateX(full)"
    setTimeout(() => {
      document.body.removeChild(notification)
    }, 300)
  }, 3000)
}

// Scroll animations
function handleScrollAnimations() {
  const elements = document.querySelectorAll(".animate-on-scroll")

  elements.forEach((element) => {
    const elementTop = element.getBoundingClientRect().top
    const elementVisible = 150

    if (elementTop < window.innerHeight - elementVisible) {
      element.classList.add("animate-fade-in")
    }
  })
}

// Add scroll event listener
window.addEventListener("scroll", handleScrollAnimations)

// Make functions globally available
window.updateQuantity = updateQuantity
window.removeFromCart = removeFromCart
