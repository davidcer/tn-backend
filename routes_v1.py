
""" v1 of relevant api routes"""
import sys
from functools import reduce
import logging

from operator import add, sub, truediv, mul
import math

import requests

from flask_jwt_extended import jwt_required, get_jwt_identity

from flask import Blueprint, jsonify, request
from sqlalchemy import text
from dotenv import dotenv_values

from db.models import Operation, Users, Record, session, get_user_balance


logger = logging.getLogger(__name__)

routes_v1 = Blueprint("api_first_version", __name__)

@routes_v1.route("/operations")
def operation_types_get():
    """provides information to the user about costs of operations"""
    try:
        operations = [o.to_json() for o in Operation.query.all()]
        operations = {"data": operations}

        return jsonify(operations), 200
    except:
        logger.critical("error when retrieving operation information", exc_info=sys.exc_info())
        return jsonify({"messages":"error when retrieving operation information"}), 503

@routes_v1.route("/profile/records", methods=["POST"])
@jwt_required()
def records_get():
    """ user operation listing and filtering"""
    user = Users.query.filter_by(email=get_jwt_identity()).first()

    args = request.get_json()

    page_number = 1
    per_page = 5
    if "page_number" in args and type(args["page_number"] == "int"):
        page_number = args["page_number"]
        slc = max(0, page_number - 1)

    if "sort_criteria" in args:
        sort = args["sort_criteria"]["column"] + (
            " desc" if args["sort_criteria"]["order"] == "down" else " asc"
        )
    else:
        sort = "id asc"
    sort = text(sort)

    filters = []
    if not user:
        return jsonify({"messages": "user not detected"}), 401

    filters.append(getattr(Record, "users_id") == user.id)

    if "filter_operation_type" in args:
        types = args["filter_operation_type"]
        filters.append(
            getattr(Record, "operation_id").in_([t["id"] for t in types if t["status"]])
        )

    total_items = Record.query.filter(*filters).count()
    total_pages = math.ceil(total_items / per_page)
    records = (
        Record.query.filter(*filters)
        .order_by(sort)
        .slice((slc) * per_page, (slc * per_page) + per_page)
        .all()
    )

    prev_range = list(range(max(1, page_number - 4), page_number))
    #[i for i in range(max(1, page_number - 4), page_number)]
    next_range = list(range(page_number + 1, min(page_number + 4, total_pages + 1)))
    #[i for i in range(page_number + 1, min(page_number + 4, total_pages + 1))]
    page = {
        "paginator": {
            "page_number": page_number,
            "pages": total_pages,
            "total_items": total_items,
            "next_page": min(page_number + 1, total_pages),
            "previous_page": max(page_number - 1, 1),
            "prev_range": prev_range,
            "next_range": next_range,
        },
        "records": [r.to_json() for r in records],
    }

    return jsonify(page), 200

@routes_v1.route("/service/calc", methods=["POST"])
@jwt_required()
def service_calc():
    """ calculator endpoint. manages credits and returns output to user"""
    args = request.get_json()

    try:
        user_credit = get_user_balance(
            get_jwt_identity(), dotenv_values(".env")["INITIAL_BALANCE"]
        )

        if "nums" in args:
            nums = args["nums"]

            if len(nums) == 0:
                return {"messages": "you didnt specified any input"}, 500

            nums = nums.replace(" ", "").split(",")
            res = all(ele.isdigit() for ele in nums)

            if res:
                nums = list(map(float, nums))
            else:
                return {"messages": "invalid data provided at estimation"}, 500
        else:
            nums = None

        if "ops" in args:
            ops = args["ops"]
        else:
            ops = {}

        if (
            "operation" in args
        ):
            operation = Operation.query.filter_by(alias=args["operation"]).first()

            if not operation:
                return {"response": "","messages": "non valid operation selected"}, 400

            if user_credit == 0 or user_credit < operation.cost:
                return (
                    jsonify(
                        {"response": "", "messages": "not enough credit for requested operation"}
                    ),
                    402,
                )

            # consumes credit
            user_credit -= operation.cost

            # Executes calc
            if operation:
                if args["operation"] in  "add":
                    output_fn = reduce(add, nums)
                elif args["operation"] == "sub":
                    output_fn = reduce(sub, nums)
                elif args["operation"] == "mul":
                    output_fn = reduce(mul, nums)
                elif args["operation"] == "div":
                    output_fn = reduce(truediv, nums)
                elif args["operation"] == "sqr":
                    output_fn = [str(round(o ** (1 / 2), 3) if o >= 0 else 0) for o in nums]
                    output_fn = ",".join(output_fn)
                elif args["operation"] == "rand":
                    ops["randomstrings"] = 1 # number of random strings'
                    output_fn = generate_random_word(ops)
                    if output_fn == "":
                        return {"messages":"something went wrong on api call to random"}, 502
            else:
                # If by any reason calculator fails.
                # none cost is going to be charged to user
                # changes are not commited
                return {"message": "operation was reverted"}, 400

        else:
            logger.warning("calc was not made because none opt type was valid")
            return {"response": 0, "message": ["not valid operation"]}, 400
    except:
        logger.critical("error on calc", exc_info=sys.exc_info())

    try:
        new_record = Record(
            operation_id=operation.id,
            users_id=1,
            amount=operation.cost,
            user_balance=user_credit,
            operation_response={
                "response": output_fn,
                "input": ops if args["operation"] == "random_word" else nums,
            },
        )
        session.add(new_record)
        session.commit()
    except:
        logger.critical("Problems when registering on database", exc_info=sys.exc_info())
        session.rollback()
        return {
            "messages": "operation rejected by database"
        }, 500

    return jsonify({"output": output_fn,
                 "user_credit": user_credit,
                 "response": new_record.to_json()}), 200

def generate_random_word(args):
    """ consumes random function from random.org
        there is a max quota per day: 1.000 daily consumption)
        options are hardcoded on a first version
        latter can be implemented:        

        options:    
        randomstrings = 1  # number of random strings
        characterlong = 20  # each string should be character longs
        characteristic_digits = 1  # allow digits
        characteristic_uppercase = 1  # allow uppercase
        characteristic_lowercase = 1  # allow lowercase
        uniqueness = 1
        output = 0  # ouput as text/plain
        randomization = 0  # 1 own , 2 pregenerated , 3 pregenerated randomization
    """

    url = (
        "https://www.random.org/strings/?num="
        + str(args["randomstrings"])
        + "&len=20"
        + "&digits=on"
        + "&upperalpha=on"
        + "&loweralpha=on"
        + "&unique=on"
        + "&format=plain"
        + "&rnd=new"
    )
    res = requests.get(url, timeout=10)

    if res.status_code == 200:
        res = res.content.decode("utf-8")
        return res
    return ""
