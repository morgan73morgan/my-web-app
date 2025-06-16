def theme(request):
    """Context processor that adds theme information to the template context."""
    # Default to 'light' theme if not set
    theme = request.COOKIES.get('theme', 'light')
    return {'current_theme': theme}
