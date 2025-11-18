"""Helper functions for consistent product data handling"""

def safe_extract_price(product: dict) -> float:
    """
    Extract price from product dict, trying multiple possible keys

    Handles variations:
    - 'price', 'cost', 'amount', 'sale_price', 'product_price'
    - Currency symbols: $100, $100.00, etc.
    """
    price_keys = [
        'price', 'cost', 'amount', 'sale_price',
        'product_price', 'sale', 'final_price'
    ]

    for key in price_keys:
        value = product.get(key)
        if value is not None:
            try:
                # Remove currency symbols
                cleaned = str(value).replace('$', '').replace(',', '').strip()
                return float(cleaned)
            except (ValueError, AttributeError, TypeError):
                continue

    return None  # No price found


def safe_extract_title(product: dict) -> str:
    """
    Extract title from product dict, trying multiple possible keys

    Handles variations:
    - 'title', 'name', 'product_name', 'product_title'
    """
    title_keys = [
        'title', 'name', 'product_name', 'product_title',
        'product', 'item_title', 'item_name'
    ]

    for key in title_keys:
        value = product.get(key)
        if value and isinstance(value, str):
            return value.strip()

    return "Unknown Product"


def safe_extract_image(product: dict) -> str:
    """Extract image URL from product dict"""
    image_keys = ['image', 'image_url', 'thumbnail', 'picture', 'photo']

    for key in image_keys:
        value = product.get(key)
        if value and isinstance(value, str) and value.startswith('http'):
            return value

    return ""


def safe_extract_link(product: dict) -> str:
    """Extract product link from product dict"""
    link_keys = ['link', 'url', 'product_url', 'product_link', 'href']

    for key in link_keys:
        value = product.get(key)
        if value and isinstance(value, str) and value.startswith('http'):
            return value

    return ""


def normalize_product(product: dict) -> dict:
    """
    Normalize product to standard format

    Returns:
    {
        'title': str,
        'price': float or None,
        'image': str,
        'link': str,
        'source': str,
        **rest of fields
    }
    """
    normalized = {
        'title': safe_extract_title(product),
        'price': safe_extract_price(product),
        'image': safe_extract_image(product),
        'link': safe_extract_link(product),
        'source': product.get('source', product.get('retailer', 'unknown')),
        **{k: v for k, v in product.items()
           if k not in ['title', 'name', 'price', 'cost', 'image', 'image_url', 'link', 'url']}
    }
    return normalized
