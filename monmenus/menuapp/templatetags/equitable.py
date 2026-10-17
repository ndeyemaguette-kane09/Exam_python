from django import template

register = template.Library()


@register.filter
def nombre(valeur):
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return valeur
    if valeur.is_integer():
        texte = f"{int(valeur):,}".replace(',', ' ')
    else:
        texte = f"{valeur:.2f}".rstrip('0').replace('.', ',')
    return texte


@register.filter
def fcfa(valeur):
    return f"{nombre(round(float(valeur or 0)))} FCFA"


@register.filter
def duree(minutes):
    minutes = int(minutes or 0)
    if minutes < 60:
        return f"{minutes} min"
    heures, reste = divmod(minutes, 60)
    return f"{heures} h {reste:02d}" if reste else f"{heures} h"
