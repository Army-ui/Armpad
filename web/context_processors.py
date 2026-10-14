def theme(request):
    """Context processor pour le thème."""
    if request.user.is_authenticated:
        theme = request.user.theme
    else:
        theme = request.session.get('theme', 'light')
    return {'current_theme': theme}


def language(request):
    """Context processor pour la langue."""
    if request.user.is_authenticated:
        lang = request.user.preferred_language
    else:
        lang = request.session.get('django_language', 'fr')
    return {'LANGUAGE_CODE': lang}
