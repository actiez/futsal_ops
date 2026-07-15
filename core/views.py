from django.http import JsonResponse


def aliveagain(request):
    return JsonResponse({
        "ok": True,
        "status": "aliveagain",
    })