def theme(request):
    """
    Context processor pour le thème.
    Si l'utilisateur est connecté, on utilise user.theme.
    Sinon, on utilise la session ou 'light' par défaut.
    """
    if request.user.is_authenticated:
        theme = request.user.theme
    else:
        theme = request.session.get('theme', 'light')
    return {'current_theme': theme}

def language(request):
    """
    Context processor pour la langue.
    Si l'utilisateur est connecté, on utilise user.preferred_language.
    Sinon, on utilise la session ou 'fr' par défaut.
    """
    if request.user.is_authenticated:
        lang = request.user.preferred_language
    else:
        lang = request.session.get('django_language', 'fr')
    return {'LANGUAGE_CODE': lang}