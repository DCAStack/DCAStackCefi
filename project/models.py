from flask_login import UserMixin
from . import db
import jwt
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from project import SECRET_KEY
from Crypto.Cipher import AES
import scrypt, os, binascii
from flask import current_app
import pickle

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def __repr__(self):
        return 'User is {}'.format(self.email)

    @staticmethod
    def get_user(id):
        user = User.query.filter_by(id=id).first()
        return user

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_password(self, password, commit=False):
        self.password = generate_password_hash(password, method='sha256')

        if commit:
            db.session.commit()

    def get_reset_token(self, expires=500):
        return jwt.encode({'reset_password': self.email, 'exp': time() + expires},
                          key=SECRET_KEY)

    @staticmethod
    def verify_email(email):

        user = User.query.filter_by(email=email).first()

        return user

    @staticmethod
    def verify_reset_token(token):
        try:
            email = jwt.decode(token, key=SECRET_KEY)['reset_password']
            print(email)
        except Exception as e:
            print(e)
            return
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create_user(username, password, email):

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return False

        user = User()

        user.username = username
        user.password = user.set_password(password)
        user.email = email

        db.session.add(user)
        db.session.commit()

        return True


class dcaSchedule(db.Model):
    __tablename__ = 'dca_schedule'

    # primary keys are required by SQLAlchemy
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    dca_instance = db.Column(db.String(100))
    exchange_id = db.Column(db.String(100))
    api_key = db.Column(db.PickleType)
    api_secret = db.Column(db.PickleType)
    api_uid = db.Column(db.PickleType)
    api_passphrase = db.Column(db.PickleType)
    dca_frequency = db.Column(db.String(100))
    trading_pair = db.Column(db.String(100))
    dca_lastRun = db.Column(db.DateTime)
    dca_firstRun = db.Column(db.DateTime)
    dca_nextRun = db.Column(db.DateTime)
    dca_budget = db.Column(db.Integer)
    isActive = db.Column(db.Boolean, default=True)

    def encrypt_API(msg, password=SECRET_KEY):
        try:
            if msg:

                msg = str.encode(msg)
                kdfSalt = os.urandom(16)
                secretKey = scrypt.hash(password, kdfSalt, N=16384, r=8, p=1, buflen=32)
                aesCipher = AES.new(secretKey, AES.MODE_GCM)
                ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
                tuplified = (kdfSalt, ciphertext, aesCipher.nonce, authTag)
                return tuplified

            return None

        except Exception as e:
            current_app.logger.exception("Could not encrypt API information")
            raise Exception("Something went wrong with storing API information!")


    def decrypt_API(encryptedMsg, password=SECRET_KEY,explicitPickle=False):
        try:
            if encryptedMsg:

                if explicitPickle:
                    encryptedMsg = pickle.loads(encryptedMsg)

                (kdfSalt, ciphertext, nonce, authTag) = encryptedMsg
                secretKey = scrypt.hash(password, kdfSalt, N=16384, r=8, p=1, buflen=32)
                aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
                plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
                return plaintext.decode("utf-8")
            
            return None

        except Exception as e:
            current_app.logger.exception("Could not decrypt API information!")
            raise Exception("Something went wrong with using API information!")

    @staticmethod
    def create_schedule(user_id, exchange_id, api_key,api_secret,api_uid,api_pass,dca_interval,trading_pairs,currentDate,nextRunTime,dca_instance,dca_amount):

        try:

            new_schedule = dcaSchedule(user_id=user_id, exchange_id=exchange_id, 
                                    api_key=dcaSchedule.encrypt_API(api_key),
                                    api_secret=dcaSchedule.encrypt_API(api_secret), 
                                    api_uid=dcaSchedule.encrypt_API(api_uid), 
                                    api_passphrase=dcaSchedule.encrypt_API(api_pass), 
                                    dca_frequency=dca_interval, trading_pair=trading_pairs,
                                    dca_lastRun=currentDate, dca_firstRun=currentDate, dca_nextRun=nextRunTime,
                                    dca_instance=dca_instance, dca_budget=dca_amount, isActive=True)

            db.session.add(new_schedule)
            db.session.commit()

            return True

        except Exception as e:
            current_app.logger.exception("Could not create_schedule!")
            return False