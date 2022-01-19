from flask_mail import Message
from flask import render_template
from project import mail,celery, DEBUG_MODE
from flask import current_app



@celery.task(serializer='pickle',autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def send_async_email(msg):

    if not DEBUG_MODE:
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.exception("async mail error: {}".format(msg))
    else:
        current_app.logger.info("Mocking email: {}".format(msg))
    
def receive_contact_message(userEmail, msgSubject, msgBody):

    msg = Message()
    msg.subject = msgSubject
    msg.sender = current_app.config['ADMINS'][0]
    msg.recipients = [current_app.config['ADMINS'][0]]
    msg.body = "Message received from {} about {}".format(userEmail, msgBody)

    current_app.logger.info("Sending contact form: {}".format(userEmail))
    send_async_email.delay(msg)

def send_reset_password(user):
    token = user.get_reset_token()

    msg = Message()
    msg.subject = "DCA Stack Password Reset"
    msg.sender = current_app.config['ADMINS'][0]
    msg.recipients = [user.email]
    msg.html = render_template('authy/reset_email.html', user=user, token=token)

    

    current_app.logger.info("Sending reset password: {}".format(user.email))
    send_async_email.delay(msg)
    

def send_order_notification(user, exchange, dcaAmount, crypto, price=None,cryptoAmount=None,errorMsg=None):
    msg = Message()
    msg.subject = "{} Order Placed".format(crypto)
    msg.sender = current_app.config['ADMINS'][0]
    msg.recipients = [user.email]


    msg.body = "We placed an order on {} for {} with your DCA budget of ${}!".format(exchange, crypto, dcaAmount)
    
    if errorMsg:
        msg.body = "Error placing order on {} for {} with your DCA budget of ${} due to {}. Instance will be paused until you click resume.".format(exchange,crypto, dcaAmount, errorMsg)

    if price and cryptoAmount:
        msg.body = "We placed an order on {} with your DCA budget of ${} at a price per ${} for {} {}!".format(exchange, dcaAmount, price, cryptoAmount, crypto)
        
    
    current_app.logger.info("send_order_notification: {}".format(user.email))
    send_async_email.delay(msg)
