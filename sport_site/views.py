import datetime
import json

from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from .models import Sports, Match, EndedMatches
from django.views.generic import DetailView, View
from .forms import LoginForm, SquadForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone


class LoginView(View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {'form': form}
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                return HttpResponseRedirect('/')

        return render(request, 'login.html', {'form': form})


class SquadRegister(View):

    def get(self, request, *args, **kwargs):
        form = SquadForm(request.POST or None)
        context = {"form": form}
        return render(request, "team_registration.html", context)

    def post(self, request, *args, **kwargs):
        form = SquadForm(request.POST or None)
        red_team = form["red_squad"]
        blue_team = form["blue_squad"]
        sport = 1
        create_match(sport, red_team, blue_team)
        return HttpResponseRedirect("/Пляжный волейбол/Матч")


def enter_match(request, sport_name):
    matches = Match.objects.filter(sport__name=sport_name)

    if request.user.groups.filter(name='Referees').exists():
        user_is_referee = True
    else:
        user_is_referee = False

    if matches.exists():

        for match in matches:
            expire_time = datetime.timedelta(seconds=4)

            if match.ace_out_time is not None:
                if timezone.now() - match.ace_out_time > expire_time:
                    match.red_ace_out = " "
                    match.blue_ace_out = " "
                    match.ace_out_time = None

        match.save()

        context = {"matches": matches, "user_is_referee": user_is_referee}
        return render(request, "beach_volleyball.html", context)
    elif user_is_referee:
        return HttpResponseRedirect("/Регистрация команд/%s" % sport_name)
    else:
        return HttpResponseRedirect("/")


def check_ace_out(red_ace_out, blue_ace_out, ace_out_time):

    reset_ace_out_time = datetime.timedelta(seconds=5)

    if ace_out_time is None:
        red_ace_out_value = red_ace_out
        blue_ace_out_value = blue_ace_out
        ace_out_time_value = None

    elif red_ace_out != (" " or "undefined"):
        if timezone.now() - reset_ace_out_time > ace_out_time:
            ace_out_time_value = timezone.now()
            red_ace_out_value = " "
            blue_ace_out_value = " "
        else:
            red_ace_out_value = red_ace_out
            blue_ace_out_value = " "
            ace_out_time_value = None

    elif blue_ace_out != (" " or "undefined"):
        if timezone.now() - reset_ace_out_time > ace_out_time:
            ace_out_time_value = timezone.now()
            blue_ace_out_value = " "
            red_ace_out_value = " "
        else:
            red_ace_out_value = " "
            blue_ace_out_value = blue_ace_out
            ace_out_time_value = None



    return red_ace_out_value, blue_ace_out_value, ace_out_time_value


def change_points(request, match_id, team, action):

    match = Match.objects.get(id=match_id)

    set = str(match.active_set)

    print(set)

    if action == "plus":
        points = getattr(match, team+"_points_set_"+set)
        setattr(match, team+"_points_set_"+set, points + 1)
        match.current_inning = team

    else:
        points = getattr(match, team + "_points_set_" + set)
        if points == 0:
            points = 0
        else:
            points -= 1
        setattr(match, team + "_points_set_" + set, points)

    match.total_current_set = getattr(match, "red_points_set_"+set) + getattr(match, "blue_points_set_"+set)
    match.red_team_total = match.red_points_set_1 + match.red_points_set_2 + match.red_points_set_3
    match.blue_team_total = match.blue_points_set_1 + match.blue_points_set_2 + match.blue_points_set_3
    match.match_total = match.red_team_total + match.blue_team_total

    match.save()

    return HttpResponseRedirect("/Пляжный волейбол/Матч")


def set_inning(request, match_id, team):

    match = Match.objects.get(id=match_id)

    match.current_inning = team

    match.save()

    return HttpResponseRedirect("/Пляжный волейбол/Матч")


def swap_controls(request, match_id):

    match = Match.objects.get(id=match_id)

    if match.swap_position == 1:
        match.swap_position = 2
    else:
        match.swap_position = 1

    match.save()

    return HttpResponseRedirect("/Пляжный волейбол/Матч")


def ace_out(request, match_id, team, action):

    match = Match.objects.get(id=match_id)

    setattr(match, team + "_ace_out", action)

    match.ace_out_time = timezone.now()

    match.save()

    if action == "Ace":
        change_points(request, match_id=match_id, team=team, action="plus")
        # return HttpResponseRedirect("/Изменить счет/"+str(match_id)+"/"+team+"/plus")
    if action == "Out":
        if team == "red":
            change_points(request, match_id=match_id, team="blue", action="plus")
        if team == "blue":
            change_points(request, match_id=match_id, team="red", action="plus")

    return HttpResponseRedirect("/Пляжный волейбол/Матч")


def end_set(request, match_id):

    match = Match.objects.get(id=match_id)
    set = str(match.active_set)

    if match.red_set_score > 2 or match.blue_set_score > 2:
        match.save()

    if getattr(match, "red_points_set_" + set) > getattr(match, "blue_points_set_" + set):
        match.red_set_score += 1
    elif getattr(match, "blue_points_set_" + set) > getattr(match, "red_points_set_" + set):
        match.blue_set_score += 1

    match.active_set += 1

    match.current_inning = "blank"

    match.save()



    return HttpResponseRedirect("/Пляжный волейбол/Матч")


def create_match(sport, red_team, blue_team):
    sport_type = Sports.objects.get(id=sport)
    match = Match.objects.create(sport=sport_type, red_squad=red_team.value(), blue_squad=blue_team.value())
    match.created_date = timezone.now()
    match.save()

    """statistic_file = open("Протокол по пляжному волейболу "+str(match.id)+".html", 'w', encoding="utf-8")
    statistic_file.close()"""

    return match


def end_match(request):
    match = Match.objects.all().first()

    ended_match = EndedMatches.objects.create(sport=match.sport, date=match.date, red_squad=match.red_squad,
                                              blue_squad=match.blue_squad)

    ended_match.red_set_score = match.red_set_score
    ended_match.blue_set_score = match.blue_set_score
    ended_match.red_points_set_1 = match.red_points_set_1
    ended_match.red_points_set_2 = match.red_points_set_2
    ended_match.red_points_set_3 = match.red_points_set_3
    ended_match.blue_points_set_1 = match.blue_points_set_1
    ended_match.blue_points_set_2 = match.blue_points_set_2
    ended_match.blue_points_set_3 = match.blue_points_set_3

    ended_match.save()

    match.delete()

    return HttpResponseRedirect("/")


@login_required
def main(request):
    sports = Sports.objects.all()

    context = {"sports": sports}

    return render(request, "sports.html", context)


def statistic_view(request, match_id):

    match = Match.objects.get(id=match_id)

    context = {"match": match}

    return render(request, "Протокол шаблон.html", context)





