
export interface TranslationKeys {
  'nav.home': string;
  'nav.products': string;
  'nav.about': string;
  'nav.contact': string;
  'hero.title': string;
  'hero.subtitle': string;
  'hero.description': string;
  'hero.cta.primary': string;
  'hero.cta.secondary': string;
  'features.title': string;
  'features.ai.title': string;
  'features.ai.description': string;
  'features.tracking.title': string;
  'features.tracking.description': string;
  'features.reviews.title': string;
  'features.reviews.description': string;
  'features.fast.title': string;
  'features.fast.description': string;
  'products.title': string;
  'products.subtitle': string;
  'products.explore': string;
  'cta.title': string;
  'cta.description': string;
  'cta.getStarted': string;
  'cta.scheduleDemo': string;
  'common.loading': string;
  'common.error': string;
  'common.retry': string;
  'accessibility.menuOpen': string;
  'accessibility.menuClose': string;
  'accessibility.themeToggle': string;
  'accessibility.addToFavorites': string;
  'accessibility.removeFromFavorites': string;
  'accessibility.addedToCart': string;
  'accessibility.addedToFavorites': string;
  'accessibility.removedFromFavorites': string;
}

export const translations: Record<string, TranslationKeys> = {
  en: {
    'nav.home': 'Home',
    'nav.products': 'Products',
    'nav.about': 'About',
    'nav.contact': 'Contact',
    'hero.title': 'Smart Shopping',
    'hero.subtitle': 'Reimagined',
    'hero.description': 'Experience the future of e-commerce with AI-powered product discovery, real-time price comparison, and intelligent recommendations across thousands of premium stores',
    'hero.cta.primary': 'Start Shopping Now',
    'hero.cta.secondary': 'Watch Demo',
    'features.title': 'Why Industry Leaders Choose Compair',
    'features.ai.title': 'AI-Powered Search',
    'features.ai.description': 'Find products using natural language or images with advanced ML algorithms',
    'features.tracking.title': 'Real-time Price Tracking',
    'features.tracking.description': 'Monitor price changes across 1000+ stores with instant notifications',
    'features.reviews.title': 'Verified Reviews',
    'features.reviews.description': 'Authentic reviews from verified buyers with AI-powered sentiment analysis',
    'features.fast.title': 'Lightning Fast Results',
    'features.fast.description': 'Sub-second product comparisons powered by advanced indexing',
    'products.title': 'Trending Products',
    'products.subtitle': 'Discover the most sought-after items with exclusive deals and authentic reviews',
    'products.explore': 'Explore More Products',
    'cta.title': 'Ready to Transform Your Shopping?',
    'cta.description': 'Join over 2 million smart shoppers who save an average of $500 annually with Compair\'s revolutionary AI-powered platform',
    'cta.getStarted': 'Get Started Free',
    'cta.scheduleDemo': 'Schedule Demo',
    'common.loading': 'Loading...',
    'common.error': 'Something went wrong',
    'common.retry': 'Try Again',
    'accessibility.menuOpen': 'Open menu',
    'accessibility.menuClose': 'Close menu',
    'accessibility.themeToggle': 'Toggle theme',
    'accessibility.addToFavorites': 'Add to favorites',
    'accessibility.removeFromFavorites': 'Remove from favorites',
    'accessibility.addedToCart': 'Product added to cart',
    'accessibility.addedToFavorites': 'Product added to favorites',
    'accessibility.removedFromFavorites': 'Product removed from favorites',
  },
  es: {
    'nav.home': 'Inicio',
    'nav.products': 'Productos',
    'nav.about': 'Acerca de',
    'nav.contact': 'Contacto',
    'hero.title': 'Compras Inteligentes',
    'hero.subtitle': 'Reimaginadas',
    'hero.description': 'Experimenta el futuro del comercio electrónico con descubrimiento de productos impulsado por IA, comparación de precios en tiempo real y recomendaciones inteligentes en miles de tiendas premium',
    'hero.cta.primary': 'Comenzar a Comprar',
    'hero.cta.secondary': 'Ver Demo',
    'features.title': 'Por qué los Líderes de la Industria Eligen Compair',
    'features.ai.title': 'Búsqueda con IA',
    'features.ai.description': 'Encuentra productos usando lenguaje natural o imágenes con algoritmos de ML avanzados',
    'features.tracking.title': 'Seguimiento de Precios en Tiempo Real',
    'features.tracking.description': 'Monitorea cambios de precios en más de 1000 tiendas con notificaciones instantáneas',
    'features.reviews.title': 'Reseñas Verificadas',
    'features.reviews.description': 'Reseñas auténticas de compradores verificados con análisis de sentimientos impulsado por IA',
    'features.fast.title': 'Resultados Súper Rápidos',
    'features.fast.description': 'Comparaciones de productos en fracciones de segundo impulsadas por indexación avanzada',
    'products.title': 'Productos Tendencia',
    'products.subtitle': 'Descubre los artículos más buscados con ofertas exclusivas y reseñas auténticas',
    'products.explore': 'Explorar Más Productos',
    'cta.title': '¿Listo para Transformar tus Compras?',
    'cta.description': 'Únete a más de 2 millones de compradores inteligentes que ahorran un promedio de $500 anuales con la plataforma revolucionaria impulsada por IA de Compair',
    'cta.getStarted': 'Comenzar Gratis',
    'cta.scheduleDemo': 'Programar Demo',
    'common.loading': 'Cargando...',
    'common.error': 'Algo salió mal',
    'common.retry': 'Intentar de nuevo',
    'accessibility.menuOpen': 'Abrir menú',
    'accessibility.menuClose': 'Cerrar menú',
    'accessibility.themeToggle': 'Cambiar tema',
    'accessibility.addToFavorites': 'Agregar a favoritos',
    'accessibility.removeFromFavorites': 'Quitar de favoritos',
    'accessibility.addedToCart': 'Producto agregado al carrito',
    'accessibility.addedToFavorites': 'Producto agregado a favoritos',
    'accessibility.removedFromFavorites': 'Producto removido de favoritos',
  }
};

let currentLanguage: keyof typeof translations = 'en';

export const setLanguage = (lang: keyof typeof translations) => {
  currentLanguage = lang;
  localStorage.setItem('preferred-language', lang);
};

export const getLanguage = (): keyof typeof translations => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('preferred-language') as keyof typeof translations;
    if (saved && translations[saved]) {
      currentLanguage = saved;
    }
  }
  return currentLanguage;
};

export const t = (key: keyof TranslationKeys): string => {
  const lang = getLanguage();
  return translations[lang]?.[key] || translations.en[key] || key;
};

export const useTranslation = () => {
  return { t, setLanguage, currentLanguage: getLanguage() };
};
