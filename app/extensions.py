from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
ma = Marshmallow()
login_manager = LoginManager()
jwt = JWTManager()
