from django.http import HttpResponse

def home(request):
    return HttpResponse("Futsal Ops is LIVE")