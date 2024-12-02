from email import message
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Room, Topic, User, Message
from .forms import RoomForm, UserForm


# Create your views here.
def loginPage(request):
  page = 'login'
  
  if request.user.is_authenticated:
    return redirect('home')
  
  if request.method == "POST":
    # get username and password from POST method
    username = request.POST.get('username').lower()
    password = request.POST.get('password')
    
    # check if the user is exist in the database
    try:
      user = User.objects.get(username=username)
    except:
      messages.error(request, "User does not exist")
      
    # authenticate the user
    user = authenticate(request, username=username, password=password)
    
    # login
    if user is not None:
      login(request, user)
      return redirect('home')
    else:
      messages.error(request, "Username or password does not exist ")
  
  context = {'page': page}
  return render(request, 'baseApp/login_register.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

def logoutUser(request):
  logout(request)
  return redirect('home')

 
# <- -----------------------------------------!!----------------------------------------- -> #  
  
def registerUser(request):
  form = UserCreationForm()
  
  if request.method == "POST":
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)
      user.username = user.username.lower()
      user.save()
      login(request, user)
      return redirect('home')
    else:
      messages.error(request, "An error occurred!!")
  
  context = {'form': form}
  return render(request, 'baseApp/login_register.html', context)
  

# <- -----------------------------------------!!----------------------------------------- -> #

def home(request):
  # get rooms by searchParams by input with name='q', icontains is filter method
  q = request.GET.get('q') if request.GET.get('q') != None else ''
  rooms = Room.objects.filter(
    Q(topic__name__icontains=q) | 
    Q(name__icontains=q) | 
    Q(description__icontains=q) |
    Q(host__username__icontains=q)) 
  
  room_count = rooms.count()
  
  topics = Topic.objects.all()[0:5]
  all_rooms_message = Message.objects.filter(Q(room__topic__name__icontains=q))
  
  context = {
    'rooms' : rooms,
    'topics': topics, 
    'room_count': room_count, 
    'all_messages': all_rooms_message
  }
  return render(request, 'baseApp/home.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #
def room(request, pk):
  room = Room.objects.get(id=pk)
  room_messages = room.message_set.all()
  participants = room.participants.all()
  
  if request.method == "POST":
    new_message = Message.objects.create(
      user = request.user,
      room = room,
      body = request.POST.get('body')
    )
    room.participants.add(request.user)
    return redirect('room', pk=room.id)
  context = {'room': room, 'room_messages': room_messages, 'participants': participants}
  return render(request, 'baseApp/room.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

def userProfile(request, pk):
  user = User.objects.get(id=pk)
  rooms = user.room_set.all()
  room_messages = user.message_set.all()
  topics = Topic.objects.all()
  
  context = {
    'user': user,
    'rooms': rooms,
    'all_messages': room_messages,
    'topics': topics
  }
  return render(request, 'baseApp/profile.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

# login required for createRoom, if not login redirect to login page
@login_required(login_url='login') 
def createRoom(request):
  form = RoomForm()
  topics = Topic.objects.all()
  if request.method == 'POST':
    topic_name = request.POST.get('topic')
    topic, created = Topic.objects.get_or_create(name=topic_name) 
    
    Room.objects.create(
      host = request.user,
      topic = topic,
      name = request.POST.get('name'),
      description = request.POST.get('description')
    )
    return redirect('home')
      
  context = {'form': form, 'topics': topics}
  return render(request, 'baseApp/room_form.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

@login_required(login_url='login') 
def updateRoom(request, pk):
  room = Room.objects.get(id=pk)
  form = RoomForm(instance=room)
  topics = Topic.objects.all()
  
  if request.user != room.host:
    return HttpResponse("You have no right !!!")
  
  if request.method == 'POST':
    topic_name = request.POST.get('topic')
    topic, created = Topic.objects.get_or_create(name=topic_name) 
    room.name = request.POST.get('name')
    room.topic = topic
    room.description = request.POST.get('description')
    room.save()
    return redirect('home')
    
  context = {"form": form, 'topics': topics, 'room': room}  
  return render(request, 'baseApp/room_form.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

@login_required(login_url='login') 
def deleteRoom(request, pk):
  room = Room.objects.get(id=pk)
  
  if request.user != room.host:
    return HttpResponse("You have no right !!!")
  
  if request.method == 'POST':
    room.delete()
    return redirect('home')
  
  return render(request, 'baseApp/delete.html', {'obj': room})


# <- -----------------------------------------!!----------------------------------------- -> #

@login_required(login_url='login') 
def deleteMessage(request, pk):
  message = Message.objects.get(id=pk)
  
  if request.user != message.user:
    return HttpResponse("You have no right !!!")
  
  if request.method == 'POST':
    message.delete()
    return redirect('home')
  
  return render(request, 'baseApp/delete.html', {'obj': message})


# <- -----------------------------------------!!----------------------------------------- -> #

@login_required(login_url='login') 
def updateUser(request):
  user = request.user
  form = UserForm(instance=user)
  
  if request.method == 'POST':
    form = UserForm(request.POST, instance=user)
    if form.is_valid():
      form.save()
      return redirect('user-profile', pk=user.id)
  
  context = {'form': form}
  return render(request, 'baseApp/update_user.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

def topicsPage(request):
  q = request.GET.get('q') if request.GET.get('q') != None else ''
  topics = Topic.objects.filter(name__icontains=q)
  
  context = {'topics': topics}
  return render(request, 'baseApp/topics.html', context)


# <- -----------------------------------------!!----------------------------------------- -> #

def activitiesPage(request):
  room_messages = Message.objects.all()
  
  context = {'all_messages': room_messages}
  return render(request, 'baseApp/activity.html', context)