from django import template

register = template.Library()

@register.filter
def truncate_chars(value, max_length):
    """Tronque une chaîne à max_length caractères."""
    if len(value) <= max_length:
        return value
    return value[:max_length] + '…'