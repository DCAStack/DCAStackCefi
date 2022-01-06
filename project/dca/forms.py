import ccxt
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, validators
from project import DEBUG_MODE, SANDBOX_MODE

class DCA_Form(FlaskForm):

    allExchanges = []
    allExchanges.extend(ccxt.exchanges)

    sandbox_exchanges = ["coinbasepro","kucoin","gemini","binance","phemex","wavesexchange"]

    exchangeList = allExchanges
    if SANDBOX_MODE:
        exchangeList = sandbox_exchanges

    exchange_id = SelectField(
        'exchange_id', choices=exchangeList, default='coinbasepro')

    dca_instance = StringField('DCA_INSTANCE', [validators.DataRequired()])

    trading_pairs = StringField(
        'autocomplete', [validators.DataRequired()], id='autocomplete')

    dayChoices = [str(x) + " Days" for x in range(1, 31)]
    minuteChoice = ["1 Min Blast"]

    allChoices = dayChoices
    if DEBUG_MODE:
        allChoices = minuteChoice+dayChoices

    dca_interval = SelectField('dca_interval', choices=allChoices)

    api_key = StringField('API_KEY', [validators.DataRequired()])
    api_secret = StringField('API_SECRET', [validators.DataRequired()])
    api_pass = StringField('API_PASS')
    api_uid = StringField('API_UID')
    dca_amount = IntegerField(
        'dca_amount',  [validators.NumberRange(min=1), validators.DataRequired()])