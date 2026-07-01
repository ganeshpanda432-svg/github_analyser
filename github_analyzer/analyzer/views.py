from django.shortcuts import render
from .utils import parse_github_url, fetch_repo_data
from .models import RepoAnalysis
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import RegisterForm

# Create your views here.
@login_required
def analyze_repo(request):
    context = {}
    if request.method == "POST":
        url = request.POST.get("repo_url")
        try:
            owner, repo = parse_github_url(url)
            data = fetch_repo_data(owner, repo)

            RepoAnalysis.objects.create(
                repo_url=url,
                owner=owner,
                repo_name=repo,
                stars=data["stars"],
                forks=data["forks"],
                language_data=data["languages"],
            )
            context["result"] = data
            context["owner"] = owner
            context["repo"] = repo
        except Exception as e:
            context["error"] = str(e)

    return render(request, "index.html", context)

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("analyze_repo")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/login/")
