from django.shortcuts import render
from .crud.read import get_all_events

def event_list(request):
    event_list = get_all_events()

    return render(
        request,
        "events/event_list.html",
        {"events": event_list}
    )