from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout

from rango.models import Category, Page, encode, decode, UserProfile

from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from django.contrib.auth.decorators import login_required

from datetime import datetime

from rango.bing_search import run_query

def index(request):
    context = RequestContext(request)

    category_list = Category.objects.order_by('-likes')[:5]
    context_dict = {'categories': category_list}

    pages_popular_list = Page.objects.order_by('-views')[:5]
    context_dict['popular_pages'] = pages_popular_list

    for category in category_list:
        category.url = category.name.replace(' ', '_')

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    context_dict['cat_list'] = get_category_list()  
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)

    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    
    return render_to_response('rango/about.html', {'cat_list': get_category_list(), 'visits': count}, context)

def view_category(request, category_name_url):
    if request.method == 'POST':
        print "AAAAAAAAAAAAAAAFFFFFFFFFFFFFFFFFF"
        return search(request, category_name_url)
    else:
        context = RequestContext(request)
        context_dict = {'category_name': decode(category_name_url)}
    
        try:
            category = Category.objects.get(name=decode(category_name_url))
            page_list = Page.objects.filter(category=category)
            context_dict['pages'] = page_list
            context_dict['category'] = category
        except Category.DoesNotExist:
            pass
        
        context_dict['category_name_url'] = category_name_url
        context_dict['cat_list'] = get_category_list()    
        return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
    context = RequestContext(request)

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    
    return render_to_response('rango/add_category.html', {'cat_list': get_category_list(), 'form': form}, context)
        
@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)
            
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html', {'cat_list': get_category_list()}, context)

            page.views = 0

            page.save()
   
            return view_category(request, category_name_url)
        else:
            print form.errors
    else:
        try:
           category = Category.objects.get(name=category_name)
           form = PageForm()
        except Category.DoesNotExist:
           form = None 
           pass
            

    return render_to_response('rango/add_page.html',
            {'cat_list': get_category_list(), 'category_name_url': category_name_url,
             'form': form, 'category_name': category_name},
             context)

def register(request):
    context = RequestContext(request)
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            
            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
 
            profile.save()

            registered = True
        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()   
    
    return render_to_response('rango/registration.html', {'cat_list': get_category_list(),'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)

def user_login(request):
    context = RequestContext(request)
    
    if request.method == 'POST':
        if 'username' in request.POST:
            username = request.POST['username']
        else:
            return HttpResponse("view error dict haven't 'username' key")
        
        if 'password' in request.POST:
            password = request.POST['password']
        else:
            return HttpResponse("view error dict haven't 'password' key")
 
        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return render_to_response('rango/login.html', {'cat_list': get_category_list(), 'bad_details': True, 'disabled_account': True}, context)

        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return render_to_response('rango/login.html', {'cat_list': get_category_list(), 'bad_details': True, 'disabled_account': False}, context)

    else:
        return render_to_response('rango/login.html', {'cat_list': get_category_list(), 'bad_details': False, 'disabled_account': False}, context)
      
@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')

def search(request, category_name_url):
    context = RequestContext(request)
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

    category = Category.objects.get(name=decode(category_name_url))
    category_id = category.id
    print category_id
    return render_to_response('rango/search.html', {'category_id': category_id, 'category_name_url':category_name_url ,'cat_name': decode(category_name_url), 'cat_list': get_category_list(), 'result_list': result_list, 'search_item': query}, context)

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
        cat_list = Category.objects.order_by('-likes')

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
        
    for cat in cat_list:
        cat.url = encode(cat.name)
    
    return cat_list

@login_required
def profile(request):
    context = RequestContext(request)
    
    current_user = request.user
    
    context_dictionary = {'cat_list': get_category_list()}
    
    try:
        current_user_profile = UserProfile.objects.get(user=current_user.id)
        context_dictionary['user_website'] = current_user_profile.website
        context_dictionary['user_picture'] = current_user_profile.picture
    except:
        context_dictionary['user_website'] = None
        context_dictionary['user_picture'] = None
        print "AAAAAAAAAAAAAA"
    
    return render_to_response('rango/profile.html', context_dictionary, context)

def track_url(request):
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                link = Page.objects.get(id=page_id)
                link.views += 1
                link.save()
            except:
                return HttpResponseRedirect('Error in track url')
            return HttpResponseRedirect(link.url)   
    else:
       return HttpResponse('Error in track url')

@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            category.save()    
    
    return HttpResponse(likes)

def suggest_category(request):
    context = RequestContext(request)
    cat_list = []
    start_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']
 
    cat_list = get_category_list(8, starts_with)

    return render_to_response('rango/category_list.html', {'cat_list': cat_list}, context)
