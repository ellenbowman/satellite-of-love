import urllib
import json
from models import Scorecard
from models import Ticker
from models import ServiceTake
import datetime

base_url = 'http://apiary.fool.com/PremiumScorecards/v1/scorecards/'

for scorecard in Scorecard.objects.all():

    scorecard_name = scorecard.name
    url = base_url + scorecard_name
    response = urllib.urlopen(url).read()
    json_resp = json.loads(response)
    op = json_resp['OpenPositions']

    for o in op:
        ticker_symbol = o['UnderlyingTickerSymbol']
        if ticker_symbol=='':
            ticker_symbol=o['TickerSymbol']

        matches = Ticker.objects.filter(ticker_symbol=ticker_symbol)

        
        if len(matches)==0:
            t = Ticker()
            t.ticker_symbol = ticker_symbol
            t.instrument_id = o['InstrumentId']
            t.exchange_symbol = o['ExchangeSymbol']
            t.percent_change_historical = 0.0
            t.company_name = o['CompanyName']
            t.save()
        else:
            t = matches[0]
        
        st = ServiceTake()
        st.is_core = o['IsCore']
        st.is_first = o['IsFirst']
        st.is_newest = o['IsNewest']
        st.action = o['Action']
        st.is_present = True
        st.ticker = t
        st.scorecard = scorecard
        temp = o['OpenDate']
        temp = temp.split('T')[0]
        st.open_date = datetime.datetime.strptime(temp, '%Y-%m-%d')

        st.save()


        service_takes_on_this_ticker = ServiceTake.objects.filter(ticker=t)
        scorecards_for_ticker = list()
        for st in service_takes_on_this_ticker:
            scorecards_for_ticker.append(st.scorecard.pretty_name)

        scorecards_for_ticker = set(scorecards_for_ticker)
        t.scorecards_for_ticker = ", ".join(scorecards_for_ticker)

        services_for_ticker = list()
        for st in service_takes_on_this_ticker:
            services_for_ticker.append(st.scorecard.service.pretty_name)

        services_for_ticker = set(services_for_ticker)
        t.services_for_ticker = ", ".join(services_for_ticker)

        t.save()
        
