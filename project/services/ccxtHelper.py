import ccxt
from flask import current_app
from .mailService import send_order_notification
from project import SANDBOX_MODE
from project.models import dcaSchedule

def create_exchangeConnection(exchange_id,api_key, api_secret,api_pass,api_uid,sandboxMode=True,needBal=False,isEncrypted=True):

    #retrieve exchange class
    exchange_class = getattr(ccxt, exchange_id)
    
    #see what credentials we need
    exchange_neededCreds = exchange_class().requiredCredentials


    try:

        # decrypt to use
        if isEncrypted:
            api_key = dcaSchedule.decrypt_API(api_key)
            api_secret = dcaSchedule.decrypt_API(api_secret)
            api_pass = dcaSchedule.decrypt_API(api_pass)
            api_uid = dcaSchedule.decrypt_API(api_uid)

        #cast these to string to work with
        api_key = str(api_key)
        api_secret = str(api_secret)
        api_pass = str(api_pass)
        api_uid = str(api_uid)

        #setup exchange class
        exchange_class_set = exchange_class(
            {'apiKey': api_key, 'secret': api_secret, 'password': api_pass if exchange_neededCreds['password'] else None, 'uid': api_uid if exchange_neededCreds['uid'] else None,
            'enableRateLimit': True,
                'options': {
                #  'createMarketBuyOrderRequiresPrice': False,
            },
                })

    
        checkConnection = exchange_class_set.checkRequiredCredentials()

        if not checkConnection:
            current_app.logger.warning("create_exchangeConnection could not connect to {}!".format(exchange_id))
            raise ccxt.AuthenticationError

        current_app.logger.warning("Sandbox mode is {}".format(SANDBOX_MODE))
        if sandboxMode:
            current_app.logger.warning
            exchange_class_set.set_sandbox_mode(SANDBOX_MODE)

        #true test is really fetching account balance
        bal = exchange_class_set.fetch_balance()

        if needBal:
            return exchange_class_set,bal

        return exchange_class_set

    except ccxt.AuthenticationError as e:
        current_app.logger.warning("create_exchangeConnection AuthenticationError could not connect to {}!".format(exchange_id))
        raise ccxt.AuthenticationError("create_exchangeConnection AuthenticationError: {}".format(exchange_id))

    except Exception as e:
        current_app.logger.warning("create_exchangeConnection General Exception to {}!".format(exchange_id))
        raise Exception("create_exchangeConnection General Exception: {}".format(exchange_id))



#has to run in real time once user configures
def place_market_order(exchange,trading_pair, dcaAmount,user,repeat=False):
    current_app.logger.info("place_order: {} {} {} {}".format(exchange,trading_pair, dcaAmount,user))
    order = None
    try:
        exchange.load_markets()

        if exchange.has['createMarketOrder']:
            current_app.logger.info("Start Making market order pair: {} on exchange: {}".format(trading_pair, exchange))

            if exchange.options.get('createMarketBuyOrderRequiresPrice', False):
                current_app.logger.info("Start Making market createMarketBuyOrderRequiresPrice")
                # cost = price * amount = how much USD you want to spend for buying 
                amount = 1 #base amount
                price = dcaAmount #price
                current_app.logger.info("place createMarketBuyOrderRequiresPrice pair:{} amount:{} price:{}".format(trading_pair, amount, price))
                order = exchange.createOrder(trading_pair, 'market', 'buy', amount, price)

            else:
                current_app.logger.info("Start Making market just amount")
                got = exchange.fetch_order_book(trading_pair)
                maxAskPrice = got['asks'][0][0]
                lastAskAmount = got['asks'][0][1]

                formatted_amount = exchange.amount_to_precision(trading_pair, dcaAmount/maxAskPrice)
                formatted_price = exchange.price_to_precision(trading_pair, maxAskPrice)

                current_app.logger.info("place market order just amount for pair:{} on exchange: {} fmt_amount: {} fmt_price: {} dca_amt: {} lastAskSize: {}".format(trading_pair, exchange, formatted_amount, formatted_price, dcaAmount, lastAskAmount))
                amount = formatted_amount  # how much CRYPTO you want to market-buy, change for your value here
                order = exchange.createOrder(trading_pair, 'market', 'buy', amount)

        else:
            current_app.logger.info("Emulated market order")
            got = exchange.fetch_order_book(trading_pair)
            maxAskPrice = got['asks'][0][0]
            lastAskAmount = got['asks'][0][1]

            formatted_amount = exchange.amount_to_precision(trading_pair, dcaAmount/maxAskPrice)
            formatted_price = exchange.price_to_precision(trading_pair, maxAskPrice)

            current_app.logger.info("place emulated market order for pair:{} on exchange: {} fmt_amount: {} fmt_price: {} dca_amt: {} lastAskSize: {}".format(trading_pair, exchange, formatted_amount, formatted_price, dcaAmount, lastAskAmount))
            order = exchange.create_limit_buy_order(trading_pair, formatted_amount, formatted_price) #amount, price

        current_app.logger.info("Making market order for pair:{} on exchange: {} order {}".format(trading_pair, exchange, order))

        if order:
            try: #catch exchanges with extra params
                if exchange.has['fetchOrderTrades']: 

                    orderDetails = exchange.fetch_order_trades(order['id'])

                    current_app.logger.info("fetchOrderTrades order details {}".format(orderDetails))
                    
                    if not orderDetails:
                        raise Exception("Order never filled for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
                    orderPrice = 0
                    orderAmount = 0
                    orderLen = len(orderDetails)
                    for execOrder in orderDetails:
                        orderPrice += execOrder['price']
                        orderAmount += execOrder['amount']

                    orderPrice = orderPrice/orderLen
                    current_app.logger.info("Sending explicit order notif to user: {}".format(user.email))
                    send_order_notification(user, exchange, dcaAmount, trading_pair, price=orderPrice, cryptoAmount=orderAmount)

                else:
                    current_app.logger.info("Sending simple order notif to user: {}".format(user.email))
                    send_order_notification(user, exchange, dcaAmount, trading_pair)

            except ccxt.errors.ArgumentsRequired:
                current_app.logger.info("ccxt.errors.ArgumentsRequired Sending simple order notif to user: {}".format(user.email))
                send_order_notification(user, exchange, dcaAmount, trading_pair)             

            return True

        current_app.logger.warning("Failed order placement for user: {} pair:{} on exchange: {}".format(user.email,trading_pair, exchange))
        return False


    except ccxt.InsufficientFunds as e:
        current_app.logger.warning("place_market_order InsufficientFunds for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
        raise ccxt.InsufficientFunds("not enough funds!")

    except ccxt.AuthenticationError as e:
        current_app.logger.warning("place_market_order AuthenticationError for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
        raise ccxt.AuthenticationError("could not authenticate API details!")

    except ccxt.InvalidOrder as e:
        current_app.logger.warning("place_market_order InvalidOrder for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
        raise ccxt.InvalidOrder("could not place order due to small order size!")

    except ccxt.NetworkError as e:
        current_app.logger.warning("place_market_order NetworkError for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
        raise ccxt.NetworkError("could not connect to exchange!")

    except Exception as e:
        current_app.logger.exception("place_market_order GeneralException for pair:{} on exchange: {} for order: {}!".format(trading_pair, exchange, order))
        raise Exception("something went wrong with the API! Please contact us :(")