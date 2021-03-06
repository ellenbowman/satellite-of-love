'''
posts to slack a recap of the articles published the previous day

how many articles were published? how many tickers were covered? which tickers had the most coverage?
how many articles did each service publish?
'''
from collections import Counter
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta
from satellite.models import Article, Service

from satellite.slack_utils import post_message_to_slack


class Command(BaseCommand):
	help = 'posts to slack a recap of the articles published the previous day'

	def handle(self, *args, **options):
		print 'starting script'

		yesterday = (datetime.today() - timedelta(days=1)).date()
		articles_published_yesterday = Article.objects.filter(date_pub__year=yesterday.year,date_pub__month=yesterday.month, date_pub__day=yesterday.day)

		unique_urls = set([a.url for a in articles_published_yesterday])
		article_count = len(unique_urls)

		message_snippets = []
		message_snippets.append("*Articles recap for %s *" % yesterday.strftime('%a, %b %d, %Y'))  # eg: Tue, May 12, 2015
		message_snippets.append("articles published: %d" % article_count)

		if article_count > 0:

			ticker_symbols_list = [a.ticker.ticker_symbol for a in articles_published_yesterday]
			tickers_count = len(set(ticker_symbols_list))

			# which tickers received the most coverage, across yesterday's articles?
			# use python's Counter to do the counting for us. https://docs.python.org/dev/library/collections.html#counter-objects
			most_common_tickers = []
			tickers_frequency_counter = Counter(ticker_symbols_list)
			most_common = tickers_frequency_counter.most_common(15) # we'll pick at most the top 15
			for ticker_popularity in most_common:

				ticker_symbol = ticker_popularity[0]
				count = ticker_popularity[1]

				# if count == 1, then this isn't so interesting. let's not bother including it
				if count==1:
					break

				most_common_tickers.append("%s (%d)" % (ticker_symbol, count))
			most_common_tickers = ', '.join(most_common_tickers)  # eg: AVAV (3), FB (2), AAPL (2)

			article_count_by_service = ''
			for s in Service.objects.all().order_by('pretty_name'):
				articles_for_service = [a for a in articles_published_yesterday if a.service==s]
				num_articles_for_service = len(set([a.url for a in articles_for_service]))

				if num_articles_for_service > 0:
					tickers_in_service_articles = set([a.ticker.ticker_symbol for a in articles_for_service])
					tickers_in_service_articles = list(tickers_in_service_articles)
					tickers_in_service_articles.sort()

					article_count_by_service += "\n   - %s : %d (%s)" % (s.pretty_name, num_articles_for_service, ', '.join(tickers_in_service_articles))

			message_snippets.append("```tickers covered: %d" % tickers_count)

			if most_common_tickers:
				message_snippets.append("tickers with the most coverage: %s" % most_common_tickers)

			message_snippets.append('--------------')
			message_snippets.append("articles by service: %s" % article_count_by_service)
			message_snippets.append('```')

		message_to_post = "\n".join(message_snippets)

		post_message_to_slack(message_to_post)

    	print 'finished script'
