""" Main backend application file """

import sys
import logging
import json
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values

from flask import Flask, request, jsonify

from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    unset_jwt_cookies,
    jwt_required,
    JWTManager,
)
from db.models import Users, session, get_user_balance

from routes_v1 import routes_v1

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = dotenv_values(".env")["JWT_SECRET_KEY"]

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)

jwt = JWTManager(app)


@app.after_request
def refresh_expiring_jwts(response):
    """ " refresh token when due time stamp is closser"""
    session.close()
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=2))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if isinstance(data, dict):
                data["access_token"] = access_token
                data["expiration"] = get_jwt()["exp"]
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        logger.critical("error on jwt generation", exc_info=sys.exc_info())

    session.close()
    return response


app.register_blueprint(routes_v1, url_prefix="/api/v1")

@app.route("/")
@jwt_required()
def index():
    """system should ask to be logged in to access. This route is held by react"""

    return {}, 200


@app.route("/ping")
@jwt_required()
def ping():
    """dummy query runs after request to refresh token"""
    return {}, 200


@app.route("/create_user", methods=["POST"])
def create_user():
    """log out"""
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if email is None or password is None:
        return {"messages": "not valid data provided"}, 400

    if Users.query.filter_by(email=email).first():
        return {"message": "user already exists"}, 400

    user = Users(email=email, password=password)
    session.add(user)
    session.commit()

    access_token = create_access_token(identity=email)

    return {"email": user.email, "access_token": access_token}, 200


@app.route("/profile")
@jwt_required()
def get_profile():
    """get user profile data"""
    user = Users.query.filter_by(email=get_jwt_identity()).first()

    if user:
        return {
            "user": user.email,
            "user_credit": get_user_balance(
                get_jwt_identity(), dotenv_values(".env")["INITIAL_BALANCE"]
            ),
        }
    return {"messages":"user not found"}, 401


@app.route("/token", methods=["POST"])
def set_token():
    """create token"""
    if request.json:
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        if Users.query.filter_by(email=email, password=password).first():
            access_token = create_access_token(identity=email)
            token = {"access_token": access_token}
            return jsonify(token)

    return {"messages": "access field were missings or incorrect"}, 401


@app.route("/logout", methods=["POST"])
def logout():
    """log out function"""
    response = jsonify({"messages": "logout successful"})
    unset_jwt_cookies(response)
    return response, 200


