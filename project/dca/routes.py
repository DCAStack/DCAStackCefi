from ccxt.base.errors import AuthenticationError, InsufficientFunds, InvalidOrder, NetworkError
from flask import render_template, redirect, url_for, flash, session, request, jsonify
from project import db
from flask_login import login_required
import ccxt
from project.models import dcaSchedule
from project.models import User
import datetime
from project.services.ccxtHelper import create_exchangeConnection, place_market_order
from flask import current_app
from project.services import dcaService
from project.dca import bp
from project.dca.forms import DCA_Form
from project.services.dcaService import async_placeMarketOrder_updateDb
import ast
from project.models import dcaSchedule
from project.services.sentryService import capture_err

@bp.route('/exchangeinfo/trading_pairs/<exchange_id>')
@login_required
def get_trading_pairs(exchange_id):
    exchange_class = getattr(ccxt, exchange_id)
    exchange_pairs = list(exchange_class().load_markets().keys())

    exchange_arr = []
    for stuff in exchange_pairs:
        exchangeObj = {}
        exchangeObj['exchange_id'] = exchange_id
        exchangeObj['trading_pair'] = stuff
        exchange_arr.append(exchangeObj)

    return jsonify({'trading_pair': exchange_arr})


@bp.route('/autocomplete', methods=['GET'])
@login_required
def autocomplete():
    search = request.args.get('q')
    usingExchangeId = request.args.get('exchange_id')
    exchange_class = getattr(ccxt, usingExchangeId)
    searchThis = list(exchange_class().load_markets().keys())
    matching = [s for s in searchThis if search.upper() in s]
    results = [mv for mv in matching]
    return jsonify(matching_results=results)


@bp.route('/exchangeinfo/exchange_api/<exchange_id>')
@login_required
def get_exchange_apiNeededCreds(exchange_id):
    exchange_class = getattr(ccxt, exchange_id)
    exchange_neededCreds = exchange_class().requiredCredentials

    return jsonify({'exchange_apiNeeded': exchange_neededCreds})


@bp.route('/dcaschedule/delete/<id>', methods=['POST'])
@login_required
def delete_dcaSchedule(id):
    if request.method == 'POST':

        try:
            instanceObj = {}
            entry = dcaSchedule.query.filter_by(user_id=session['_user_id']).all()
            for x in entry:
                if x.id == int(id):
                    db.session.delete(dcaSchedule.query.get(id))
                    db.session.commit()

                    instanceObj["status"] = "Delete"
                    instanceObj["name"] = x.dca_instance

            return redirect(url_for("dca.dcaSetup",instanceStatus=instanceObj))

        except Exception as e:
            capture_err(e,session=session)
            current_app.logger.exception("Could not delete schedule {}!".format(id))
            db.session.rollback()
            return redirect(url_for('dca.dcaSetup'))


@bp.route('/dcaschedule/resume/<id>', methods=['POST'])
@login_required
def resume_dcaSchedule(id):

    if request.method == 'POST':

        try:
            try: 
                form = DCA_Form()
                entry = dcaSchedule.query.filter_by(user_id=session['_user_id']).all()
                instanceObj = {}
                for subQuery in entry:
                    if subQuery.id == int(id):

                        #run synchronosly cause we need results in realtime and bypass async checks
                        subQuery.isActive = True
                        subQuery.dca_nextRun = datetime.datetime.now() #move next run to current date so that it will update
                        db.session.commit()
                        instanceStatus = async_placeMarketOrder_updateDb.run(subQuery,User.get_user(subQuery.user_id),True)

                        if not instanceStatus:
                            instanceStatus = "Error"
                            subQuery.isActive = False #should probs rollback instead
                            db.session.commit()

                        instanceObj["status"] = str(instanceStatus)
                        instanceObj["name"] = subQuery.dca_instance

            except:
                instanceStatus = "Error" #commonize this 
                instanceObj["status"] = str(instanceStatus)
                instanceObj["name"] = subQuery.dca_instance
                subQuery.isActive = False
                db.session.commit()

            return redirect(url_for("dca.dcaSetup",instanceStatus=instanceObj))

        except Exception as e:
            capture_err(e,session=session)
            current_app.logger.exception("Could not start schedule {}!".format(id))
            db.session.rollback()
            return redirect(url_for('dca.dcaSetup'))

@bp.route('/dcaschedule/pause/<id>', methods=['POST'])
@login_required
def pause_dcaSchedule(id):
    if request.method == 'POST':

        try:
            instanceObj = {}
            entry = dcaSchedule.query.filter_by(user_id=session['_user_id']).all()
            for x in entry:
                if x.id == int(id):
                    x.isActive = False
                    db.session.commit()
                    instanceObj["status"] = "Pause"
                    instanceObj["name"] = x.dca_instance

            return redirect(url_for("dca.dcaSetup",instanceStatus=instanceObj))

        except Exception as e:
            capture_err(e,session=session)
            current_app.logger.exception("Could not pause schedule {}!".format(id))
            db.session.rollback()
            return redirect(url_for('dca.dcaSetup'))


def fetch_dcaSchedules():
    dca_scheduleQuery = dcaSchedule.query.filter_by(
        user_id=session['_user_id']).all()
    for x in dca_scheduleQuery:
        if x.isActive == None or x.isActive == False:
            x.isActive = "Paused"
        else:
            x.isActive = "Running"

    return dca_scheduleQuery


@bp.route('/dca', methods=['GET', 'POST'])
@login_required
def dcaSetup():

    form = DCA_Form()

    if request.method == 'POST':

        dca_instance = form.dca_instance.data
        exchange_id = form.exchange_id.data
        trading_pairs = str(form.trading_pairs.data).upper()
        api_key = str(form.api_key.data).strip() #whitespace filtering
        api_secret = str(form.api_secret.data).strip()
        api_pass = str(form.api_pass.data).strip() if form.api_pass.data else None
        api_uid = str(form.api_uid.data).strip() if form.api_uid.data else None
        dca_amount = form.dca_amount.data
        dca_interval = form.dca_interval.data
        dca_interval_int = [int(s)
                            for s in dca_interval.split() if s.isdigit()][0]

        # in case connection fails
        repopulateForm = DCA_Form()
        repopulateForm.dca_instance.data = form.dca_instance.data
        repopulateForm.exchange_id.data = form.exchange_id.data
        repopulateForm.trading_pairs.data = form.trading_pairs.data
        repopulateForm.api_key.data = form.api_key.data
        repopulateForm.api_secret = form.api_secret
        repopulateForm.api_pass.data = form.api_pass.data if form.api_pass.data else None
        repopulateForm.api_uid.data = form.api_uid.data if form.api_uid.data else None
        repopulateForm.dca_amount.data = form.dca_amount.data
        repopulateForm.dca_interval.data = form.dca_interval.data

        try:

            #create exchange connection
            exchange_class_set = create_exchangeConnection(exchange_id,api_key, api_secret,api_pass,api_uid,isEncrypted=False)

            #verify user input trading pair is in our list
            exchange_class = getattr(ccxt, exchange_id)
            if trading_pairs in list(exchange_class().load_markets().keys()):

                # first run DCA
                orderStatus = place_market_order(exchange_class_set,
                                  trading_pairs, dca_amount,User.get_user(session['_user_id']))

                # if all success, add to DB
                if orderStatus:
                    
                    currentDate = datetime.datetime.now()
                    if "Days" in dca_interval:
                        current_app.logger.info("dca first run set nextRunTime on DAYS")
                        nextRunTime = currentDate + datetime.timedelta(days=dca_interval_int)
                    else:
                        current_app.logger.info("dca first run set nextRunTime on MINUTE BLAST")
                        nextRunTime = currentDate + datetime.timedelta(minutes=dca_interval_int)

                    #encrypt as we add
                    addStatus = dcaSchedule.create_schedule(user_id=session['_user_id'], exchange_id=exchange_id, 
                                                            api_key=api_key, api_secret=api_secret, api_uid=api_uid, api_pass=api_pass, 
                                                            dca_interval=dca_interval, trading_pairs=trading_pairs,
                                                            currentDate=currentDate, nextRunTime=nextRunTime,
                                                            dca_instance=dca_instance, dca_amount=dca_amount)

                    if addStatus:
                        instanceObj = {}
                        instanceObj["status"] = "True"
                        instanceObj["name"] = dca_instance
                    else:
                        raise Exception

                    return render_template('user/dca.html', form=form, dca_scheduleQuery=fetch_dcaSchedules(), instanceStatus=instanceObj)


                flash('Could not place order, please try again or contact us!')
                return render_template('user/dca.html', instanceStatus=None,form=repopulateForm, dca_scheduleQuery=fetch_dcaSchedules())

            repopulateForm.trading_pairs.data = ''
            flash('Please choose a trading pair in the list!')
            return render_template('user/dca.html', form=repopulateForm, instanceStatus=None,dca_scheduleQuery=fetch_dcaSchedules())

        except AuthenticationError as e:
            current_app.logger.warning("create_exchangeConnection AuthenticationError")
            flash('Please recheck your API details.')

            return render_template('user/dca.html', form=repopulateForm,instanceStatus=None, dca_scheduleQuery=fetch_dcaSchedules())

        except InsufficientFunds as e:
            current_app.logger.warning("create_exchangeConnection InsufficientFunds")
            flash('Please ensure you have enough funds to place an order.')

            return render_template('user/dca.html', form=repopulateForm, instanceStatus=None,dca_scheduleQuery=fetch_dcaSchedules())

        except InvalidOrder as e:
            current_app.logger.warning("create_exchangeConnection InvalidOrder")
            flash('Please increase purchase amount or contact us for further assistance!')
            return render_template('user/dca.html', form=repopulateForm, instanceStatus=None,dca_scheduleQuery=fetch_dcaSchedules())

        except NetworkError as e:
            current_app.logger.warning("create_exchangeConnection NetworkError")
            flash('Could not connect because exchange is unreachable. Please try again later.')
            return render_template('user/dca.html', form=repopulateForm, instanceStatus=None,dca_scheduleQuery=fetch_dcaSchedules())

        except Exception as e:
            capture_err(e,session=session)
            current_app.logger.exception("create_exchangeConnection GeneralException")
            flash('Connection issue, please double check your API details or contact us!')
            return render_template('user/dca.html', form=repopulateForm, instanceStatus=None,dca_scheduleQuery=fetch_dcaSchedules())

    instanceObj = ast.literal_eval(request.args.get('instanceStatus')) if request.args.get('instanceStatus') else None
    return render_template('user/dca.html', form=form, dca_scheduleQuery=fetch_dcaSchedules(), instanceStatus=instanceObj)
