from flask import jsonify
from datetime import datetime
import re

EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
USER_PATTERN = r'^[a-zA-Z0-9]{3,50}$'


def valid_email(email):
    return bool(re.fullmatch(EMAIL_PATTERN, email))

def valid_user(user):
    return bool(re.fullmatch(USER_PATTERN, user))

def valid_password(password):
    return len(password) > 5

def valid_date(project_date):
    try:
        return datetime.strptime(project_date, '%Y-%m-%d').date()
    except ValueError:
        return None