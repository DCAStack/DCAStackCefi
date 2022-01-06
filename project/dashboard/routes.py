from flask import render_template, redirect, url_for, flash, session, request, jsonify
from project import db
from flask_login import login_required
from project.models import dcaSchedule
from project.services.ccxtHelper import create_exchangeConnection
from flask import current_app
from project.dashboard import bp
from pycoingecko import CoinGeckoAPI
import json
from flask import current_app
from sqlalchemy import text
from project import executor
import concurrent.futures
import collections, functools, operator

cg = CoinGeckoAPI()
allCoinList = cg.get_coins_list()

def get_exchange_balances(x):

    freeFunds = {}

    try: #catch malformed exchange formats
        exchange_class_set,bal = create_exchangeConnection(x.exchange_id,
                                                    x.api_key,x.api_secret,x.api_passphrase,x.api_uid,needBal=True)
        for k,v in bal['total'].items():
            k = k.split('.')[0] #kraken fix
            if k not in freeFunds:
                freeFunds[k] = 0
            freeFunds[k] += v if v else 0

    except:
        current_app.logger.warning("fetch_account_balance failed for exchange: {}".format(x.exchange_id))

    return freeFunds



@bp.route('/userinfo/account_balance')
@login_required
def fetch_account_balance():
    
    returnQuery = []
    totalValue = 0
    coins = {}
    freeFunds = {}
    allFreeFunds = []

    try:  
        user_id=session['_user_id']
        
        #unique exchanges by user_id only
        entry = dcaSchedule.query.filter_by(user_id=user_id).all()
        seenExchange = set()
        filteredEntry = []
        for x in entry:
            if x.exchange_id not in seenExchange:
                filteredEntry.append(x)
                seenExchange.add(x.exchange_id)

        #connect to all exchanges and fetch balances simultaneously
        future_to_url = {executor.submit(get_exchange_balances, row): row for row in filteredEntry if row.user_id == int(user_id)}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
            except:
                current_app.logger.warning("fetch_account_balance failed for exchange details threading")
            else:
                allFreeFunds.append(data)

        if allFreeFunds:
            freeFunds = dict(functools.reduce(operator.add,map(collections.Counter, allFreeFunds)))

            freeFunds =  {k.upper(): v for k, v in freeFunds.items()}
            freeFundKeys = set(freeFunds.keys())

            checkFundIds = []
            matchedIds = {}

            for coin in allCoinList:
                coin['symbol'] = coin['symbol'].upper()

                if coin['symbol'] != "USD": #skip fiat

                    if coin['symbol'] in freeFundKeys:
                        if freeFunds[coin['symbol']] > 0:
                            matchedIds[coin['id']] = coin['symbol']
                            checkFundIds.append(coin['id'])

            inverse_dict = {}
            for k, v in matchedIds.items():
                inverse_dict.setdefault(v, []).append(k)

            currPrice = cg.get_price(ids=checkFundIds, vs_currencies='usd',include_market_cap=True)

            #sometimes we get duplicate coins for each symbol, here we filter by highest mkt cap for accuracy
            for k,v in inverse_dict.items():
                if len(v) > 1:
                    maxcap = 0
                    trueidx = 0
                    for i,value in enumerate(v):
                        if currPrice[value]['usd_market_cap'] > maxcap:
                            maxcap = currPrice[value]['usd_market_cap']
                            trueidx = i
                    inverse_dict[k] = v[trueidx]
                else:
                    inverse_dict[k] = v[0]

            verifiedCoins = set(inverse_dict.values())
        
            for coinId,coinVal in currPrice.items():
                if coinId in verifiedCoins: #verified mktcap only
                
                    coinParsedVal = float(coinVal['usd'])

                    if matchedIds[coinId] not in coins:
                        coins[matchedIds[coinId]] = [0,0,0] #fiat, native, price

                    coinValue = freeFunds[matchedIds[coinId]] * coinParsedVal
                    coins[matchedIds[coinId]][0] += round(coinValue,2)
                    coins[matchedIds[coinId]][1] += freeFunds[matchedIds[coinId]]
                    coins[matchedIds[coinId]][2] += round(coinParsedVal,4)

                    totalValue += coinValue

            #add fiat to query
            coins["USD"] = [0,0,1]
            coins["USD"][0] = round(freeFunds["USD"],2)
            coins["USD"][1] = round(freeFunds["USD"],2)
            totalValue += freeFunds["USD"]

    except:
        current_app.logger.exception("fetch_account_balance GeneralError")

    coins = dict(sorted(coins.items(), key=lambda item: item[1], reverse=True))
    return jsonify({'payload':json.dumps({
                    'coins':list(coins.keys()),
                    'values':[v[0] for v in list(coins.values())],
                    'native':[v[1] for v in list(coins.values())],
                    'price':[v[2] for v in list(coins.values())],
                    'raw':[[k, "$"+str(v[2]), v[1], "$"+str(v[0])] for k,v in coins.items()],
                    'total_balance':round(totalValue,2)})})
        

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard_main():
    return render_template('user/dashboard.html')

