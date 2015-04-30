from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.http import HttpResponse
from forms import ArticlesFilterForm
from models import Article, Service, Ticker


def services_index(request):
	"""
	a listing of the services, ordered by pretty name
	"""

	all_services = Service.objects.all().order_by('pretty_name')

	dictionary_of_values = {
		'services_in_alpha_order':all_services,
	}

	return render(request, 'satellite/all_the_services.html', dictionary_of_values)



def my_sample_view(request):
	"""
	in this view we practice pulling values from the query string
	and rendering a template that looks up
	values from a dictionary compiled within this view
	"""

	fav_color = 'probably green'
	if 'fav_color' in request.GET:
		fav_color = request.GET['fav_color']

	
	fav_service = 'i like them all!'
	if 'fav_service' in request.GET:
		fav_service = request.GET['fav_service']


	dictionary_of_values = {
		'fav_color' : fav_color,
		'fav_service': fav_service
	}
	return render(request, 'satellite/my_gorgeous_page.html', dictionary_of_values)



def articles_by_service(request):
	
	service_name = None
	# let's see if the user passed along a 'service' in the query string
	if 'service' in request.GET:
		service_name = request.GET['service']

	max_count = 20

	# if we happen to have the local variable called 'service_name', 
	# let's user it to filter the articles
	if service_name:
		# we happen to have the local variable! let's get all Service objects that have a 
		# name that matches the value of service_name
		# capture those Service object matches into a variable named 'service_match'
		service_match = Service.objects.filter(name=service_name)

		# we've identified the service(s) that satisfy our constraint. 
		# let's now query for all Article objects whose service field references a Service object in our service_match.
		articles = Article.objects.filter(service__in=service_match)[:max_count]
	else:
		articles = Article.objects.all()[:max_count]

	

	dictionary_of_values = {
		'articles' : articles,
		'service_name': service_name,
		'articles_max_count': max_count
	}

	return render(request, 'satellite/my_awesome_articles.html', dictionary_of_values)


def extra_views_homepage(request):
	"""
	show a page with links to the views defined in this file
	"""
	return render(request, 'satellite/extra_pages.html')


def grand_vision_articles(request):
	"""
	shows all articles and some meta data
	(time range of the articles, unique authors)

	contains a form that lets you specify tickers and services

	if a service name is detected in the request's POST dictionary, then filters to articles for that service
	if a ticker is detected in the request's POST dictionary, then filters to articles on that ticker
	"""

	tickers_to_filter_by = None 	# will hold the Ticker objects that satisfy our filter
	services_to_filter_by = None 	# will hold the Service objects that satisfy our filter
 	ticker_filter_description = None 	# this will be a string description of the ticker filter. we'll display this value on the page.
	service_filter_description = None   # this will be a string description of the service filter. we'll display this value on the page.


	#---- start of handling a ticker/service filter submitted via POST request ---------

	if request.POST:
		article_filter_form = ArticlesFilterForm(request.POST)
		
		if article_filter_form.is_valid():
			if 'tickers' in article_filter_form.cleaned_data:

				tickers_user_input = article_filter_form.cleaned_data['tickers'].strip()
				if tickers_user_input != '':
					user_tickers_as_list = tickers_user_input.split(",")

					# take the user input and try to find corresponding Ticker objects 
					# the list of matches across all of the tickers in user_tickers_as_list
					tickers_to_filter_by = [] 
					for ticker_symbol in user_tickers_as_list:
						cleaned_up_ticker_symbol = ticker_symbol.strip()
						ticker_matches_for_this_single_ticker_symbol = Ticker.objects.filter(ticker_symbol__iexact=cleaned_up_ticker_symbol)

						# add the list of matches on this particular ticker symbol to tickers_to_filter_by
						# http://www.tutorialspoint.com/python/list_extend.htm
						tickers_to_filter_by.extend(ticker_matches_for_this_single_ticker_symbol)

					# make the pretty description of the tickers
					ticker_filter_description = tickers_user_input.upper()

			# retrieve the services that were selected in the form. 
			if 'services' in article_filter_form.cleaned_data:
				# the form makes available "cleaned data" that's pretty convenient - 
				# in this case, it returns a list of Service objects that correspond
				# to what the user selected.
				services_to_filter_by = article_filter_form.cleaned_data['services']

				# make the pretty description of the services we found. 
				pretty_names_of_services_we_matched = [s.pretty_name for s in services_to_filter_by]
				pretty_names_of_services_we_matched.sort()
				service_filter_description = ', '.join(pretty_names_of_services_we_matched)
		
	#---- end of handling a ticker/service filter submitted via POST request ---------
	else:
		article_filter_form = ArticlesFilterForm()


	# get the set of articles, filtered by ticker/service, if those filters are defined
	if tickers_to_filter_by is not None and services_to_filter_by is not None:
		articles = Article.objects.filter(ticker__in=tickers_to_filter_by, service__in=services_to_filter_by).order_by('-date_pub')
	elif tickers_to_filter_by is not None:
		articles = Article.objects.filter(ticker__in=tickers_to_filter_by).order_by('-date_pub')
	elif services_to_filter_by is not None:
		articles = Article.objects.filter(service__in=services_to_filter_by).order_by('-date_pub')		
	else:
		# get all articles, and sort by descending date
		articles = Article.objects.all().order_by('-date_pub')

	# introduce django's built-in pagination!! let each page show 50 articles
	# https://docs.djangoproject.com/en/1.7/topics/pagination/
	paginator = Paginator(articles, 50) 

	# let's see if the query string already has a value for which 
	# page we should show (eg: '/sol/articles_vomit/?page=4')
	# this could be introduced by the user or by a link on our page
	page_num = request.GET.get('page')

	try:
		articles_subset = paginator.page(page_num)
	except PageNotAnInteger:
		# page is not an integer; let's show the first page of results
		articles_subset = paginator.page(1)
	except EmptyPage:
		# the user asked for a page way beyond what we have available;
		# let's show the last page of articles, which we can calculate
		# with paginator.num_pages
		articles_subset = paginator.page(paginator.num_pages)


	# compile meta data -------------------
	## we already sorted the articles by pub date. to get the newest and oldest, 
	## we just look at the first element in the list, and the last element
	if len(articles):
		article_most_recent_date = articles[0].date_pub  
		article_oldest_date = articles[len(articles)-1].date_pub
	else:
		article_most_recent_date = "n/a"
		article_oldest_date = "n/a"

	## how many authors?
	authors = [art.author for art in articles]
	'''  the above line is equivalent to the bottom 3! an example of "list comprehension"
	authors = []
	for art in articles:
		authors.append(art.author)
	'''
	## convert into a set, so that we toss out duplicates
	authors_set = set(authors)
	num_authors = len(authors_set)

	### how many articles?
	num_articles = len(articles)

	dictionary_of_values = {
		'form': article_filter_form,
		'articles': articles_subset,
		'pub_date_newest': article_most_recent_date,
		'pub_date_oldest': article_oldest_date,
		'num_authors' : num_authors,
		'num_articles' : num_articles,
		'service_filter_description': service_filter_description,
		'ticker_filter_description': ticker_filter_description
	}
	return render(request, 'satellite/index_of_articles.html', dictionary_of_values)
