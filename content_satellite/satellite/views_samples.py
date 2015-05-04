from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
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


def _get_ticker_objects_for_ticker_symbols(ticker_symbols_csv='AAPL,SWIR,Z'):
	"""
	given a set of ticker symbols as a single string, symbols separated by commas, find corresponding Ticker objects
	"""
	csv_elements = ticker_symbols_csv.split(',')

	# clean up - for each element, strip whitespace and convert to uppercase
	csv_elements = [el.strip().upper() for el in csv_elements]

	return Ticker.objects.filter(ticker_symbol__in=csv_elements)

def _get_service_objects_for_service_ids(service_ids_csv='1,4,7'):
	"""
	given a set of db ids of services, find corresponding Service objects
	# note: these ids were assigned by our db. they are *not* the service's product ids (eg Rule Breakers might have
		a product id of 1069, but in our db, its db id might be 3)
	"""	
	csv_elements = service_ids_csv.split(',')

	# clean up - for each element, strip whitespace and convert to an integer
	csv_elements = [int(el.strip()) for el in csv_elements]

	return Service.objects.filter(id__in=csv_elements)


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

	page_num = 1

	# filter by ticker/service if we detect that preference in the query string (in the request.GET)
	# or via a form post (in the request.POST)
	# additionally, if this is a GET, let's attempt to set the page_num. otherwise, we'll default to page_num of 1.

	if request.POST:
		if 'page_number' in request.POST:
			page_num = int(request.POST['page_number'])

		article_filter_form = ArticlesFilterForm(request.POST)
		
		if article_filter_form.is_valid():
			if 'tickers' in article_filter_form.cleaned_data:
				tickers_user_input = article_filter_form.cleaned_data['tickers'].strip()
				if tickers_user_input != '':
					# take the user input and try to find corresponding Ticker objects 
					tickers_to_filter_by = _get_ticker_objects_for_ticker_symbols(tickers_user_input)

			# retrieve the services that were selected in the form. 
			if 'services' in article_filter_form.cleaned_data:
				# the form makes available "cleaned data" that's pretty convenient - 
				# in this case, it returns a list of Service objects that correspond
				# to what the user selected.
				services_to_filter_by = article_filter_form.cleaned_data['services']

	elif request.GET:
		initial_form_values = {}

		if 'tickers' in request.GET:
			tickers_user_input = request.GET.get('tickers')
			tickers_to_filter_by = _get_ticker_objects_for_ticker_symbols(tickers_user_input)

			initial_form_values['tickers'] = tickers_user_input
		if 'service_ids' in request.GET:
			services_to_filter_by = _get_service_objects_for_service_ids(request.GET.get('service_ids'))
			initial_form_values['services'] = services_to_filter_by

		article_filter_form = ArticlesFilterForm(initial=initial_form_values)

	else:
		article_filter_form = ArticlesFilterForm()

	# end of inspecting request.GET and request.POST for ticker/service filter

	if tickers_to_filter_by:
		# make the pretty description of the tickers
		ticker_filter_description = tickers_user_input.upper()
	if services_to_filter_by:
		# make the pretty description of the services we found. 
		pretty_names_of_services_we_matched = [s.pretty_name for s in services_to_filter_by]
		pretty_names_of_services_we_matched.sort()
		service_filter_description = ', '.join(pretty_names_of_services_we_matched)


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

	# introduce django's built-in pagination!! 
	# https://docs.djangoproject.com/en/1.7/topics/pagination/
	paginator = Paginator(articles, 25) 


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

	# article_defns will be a list of article "profiles" - 
	# each element in article_defns will be a dictionary
	# each dictionary will have the full Article object, as well as meta data
	# our template will iterate over article_defns
	article_defns = []
	for article in articles_subset:

		# find some meta data: what other articles are by this author? across what services? 
		# how many articles has he written in the last 10 days?
		articles_by_this_author = Article.objects.filter(author=article.author)	
		
		services_of_those_articles = [art.service.pretty_name for art in articles_by_this_author]
		services_of_those_articles = set(services_of_those_articles) # convert to a set so that we toss out duplicates
		services_of_those_articles = list(services_of_those_articles) # convert to a list so that we can put in alpha order
		services_of_those_articles.sort()
		services_in_which_this_author_writes = ', '.join(services_of_those_articles) 

		ten_days_ago = datetime.today() - timedelta(days=10)
		# filter this author's articles by the "date_pub" field. we're interested only in the ones with
		# a date greater than ('gt') ten days ago
		articles_by_this_author_from_within_last_ten_days = articles_by_this_author.filter(date_pub__gt=ten_days_ago)

		article_defns.append({
			'article':article,
			'num_articles_by_this_author': len(articles_by_this_author),
			'author_service_associations': services_in_which_this_author_writes, 
			'num_author_articles_last_ten_dates': len(articles_by_this_author_from_within_last_ten_days)
			})

	dictionary_of_values = {
		'form': article_filter_form,
		'articles': articles_subset,
		'article_defns': article_defns,
		'pub_date_newest': article_most_recent_date,
		'pub_date_oldest': article_oldest_date,
		'num_authors' : num_authors,
		'num_articles' : num_articles,
		'service_filter_description': service_filter_description,
		'ticker_filter_description': ticker_filter_description
	}

	return render(request, 'satellite/index_of_articles.html', dictionary_of_values)