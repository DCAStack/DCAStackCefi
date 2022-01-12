from project import celery, db
from project.models import User
from project.models import dcaSchedule
import datetime
from flask import current_app
from project.services.ccxtHelper import place_market_order, create_exchangeConnection
from project.services.mailService import send_order_notification
import ccxt
import requests

@celery.task(serializer='pickle',autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def async_placeMarketOrder_updateDb(subQuery,user,bypassAsync=False):

    newSession = dcaSchedule.query.filter_by(id=subQuery.id).first() #need new context to make changes
    exchange_class_name =  subQuery.exchange_id
    trading_pair = subQuery.trading_pair
    dcaAmount = subQuery.dca_budget

    try:

        exchange_class_set = create_exchangeConnection(subQuery.exchange_id,subQuery.api_key, subQuery.api_secret,subQuery.api_passphrase,subQuery.api_uid)

        current_app.logger.info("Placing order for instance: {} {} {} {}".format(subQuery.id, exchange_class_set, subQuery.trading_pair, subQuery.dca_budget))

        if (datetime.datetime.now() > subQuery.dca_nextRun and subQuery.isActive == True) or bypassAsync: #check if already ran async

            orderStatus = place_market_order(exchange_class_set,trading_pair, dcaAmount,user)
            current_app.logger.info("Order status is: {}".format(orderStatus))

            if orderStatus:
                #update last run, next run
                currentDate = datetime.datetime.now()
                nextRun = newSession.dca_nextRun #increment nextRun to prevent order drift

                dca_interval_int = [int(s)for s in subQuery.dca_frequency.split() if s.isdigit()][0]
                if "Days" in subQuery.dca_frequency:
                    nextRunTime = nextRun + datetime.timedelta(days=dca_interval_int)
                else:
                    nextRunTime = nextRun + datetime.timedelta(minutes=dca_interval_int)

                newSession.dca_nextRun = nextRunTime
                newSession.dca_lastRun = currentDate #always true execution time
                db.session.commit()

                current_app.logger.info("Succeeded instance: {}".format(subQuery.id))

                return True

            else:
                current_app.logger.warning("Failed order placement for instance: {}".format(subQuery.id))
                raise Exception("Order failed!")

        else:
            current_app.logger.info("async_placeMarketOrder_updateDb Not ready yet Instance: {}".format(subQuery.id))

    except ccxt.InsufficientFunds as e:
        current_app.logger.warning("run_dcaSchedule InsufficientFunds")
        
        newSession.isActive = False
        db.session.commit()
        current_app.logger.info("run_dcaSchedule set to false now!")
        
        send_order_notification(user, exchange_class_name, dcaAmount, trading_pair,errorMsg=e)

    except ccxt.AuthenticationError as e:
        current_app.logger.warning("run_dcaSchedule AuthenticationError")
        
        newSession.isActive = False
        db.session.commit()
        current_app.logger.info("run_dcaSchedule set to false now!")
        
        send_order_notification(user, exchange_class_name, dcaAmount, trading_pair,errorMsg=e)

    except Exception as e:
        current_app.logger.exception("async_place_market_order GeneralException")

        if async_placeMarketOrder_updateDb.request.retries == async_placeMarketOrder_updateDb.max_retries:
            newSession.isActive = False
            db.session.commit()
            current_app.logger.info("run_dcaSchedule set to false now!")
            send_order_notification(user, exchange_class_name, dcaAmount, trading_pair,errorMsg=e)

        raise Exception("Something went wrong with async_place_market_order!")

@celery.task(serializer='pickle',autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_dcaSchedule():
    current_app.logger.info("Starting dcaSchedule")

    try:

        #heartbeat for status tracking
        url = "https://betteruptime.com/api/v1/heartbeat/sCfdXErPZKA4ritfadPQt7pt"
        resp = requests.get(url)

        getAll = db.session.query(dcaSchedule).all()
        current_app.logger.info("Retrieved query of size: {}".format(len(getAll)))
        
        for subQuery in getAll:
            if datetime.datetime.now() > subQuery.dca_nextRun and subQuery.isActive == True: #check if it's ready

                current_app.logger.info("Running schedule for instance {}".format(subQuery.id))

                #make this async so we can spawn multiple workers and do better order notifs
                async_placeMarketOrder_updateDb.delay(subQuery,User.get_user(subQuery.user_id))

            else:
                current_app.logger.info("Not ready yet Instance: {}".format(subQuery.id))

        db.session.close()

    except Exception as e:
        current_app.logger.exception("dca scheduled failed!")          

        raise Exception("run_dcaSchedule Something went wrong !")


