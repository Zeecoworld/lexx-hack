import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import nlp_engine


def index(request):
    return render(request, "core/index.html")


@require_POST
def ask(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Malformed request."}, status=400)

    turns = payload.get("turns", [])
    if not turns or not isinstance(turns, list):
        return JsonResponse({"error": "No message provided."}, status=400)

    last_user_msg = next(
        (t.get("content", "") for t in reversed(turns) if t.get("role") == "user"), ""
    )
    answer = nlp_engine.answer_question(last_user_msg)
    return JsonResponse({"answer": answer})


@require_POST
def analyze(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Malformed request."}, status=400)

    doc_text = (payload.get("text") or "").strip()
    if not doc_text:
        return JsonResponse({"error": "Paste some contract text first."}, status=400)

    items = nlp_engine.analyze_document(doc_text[:20000])
    return JsonResponse({"items": items})
