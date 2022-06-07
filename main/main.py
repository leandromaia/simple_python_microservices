import sys
import os
import logging
from dataclasses import dataclass

from flask import Flask, jsonify, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
import requests

from producer import publish

#Global object used to logger the hard code messages
logger = None

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

CORS(app)

db = SQLAlchemy(app)


@dataclass
class Product(db.Model):
    id: int
    title: str
    image: str

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(200))
    image = db.Column(db.String(200))


@dataclass
class ProductUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)

    UniqueConstraint('user_id', 'product_id', name='user_product_unique')


@app.route('/api/products')
def index():
    return jsonify(Product.query.all())


@app.route('/api/products/<int:id>/like', methods=['POST'])
def like(id):
    logger.debug("Starting like process of product id %s", id)
    json = _get_users()

    try:
        productUser = ProductUser(user_id=json['id'], product_id=id)
        db.session.add(productUser)
        db.session.commit()

        publish('product_liked', id)
    except:
        logger.error("Failed like product with id %s", id)
        abort(400, 'You already liked this product')

    return jsonify({
        'message': 'success'
    })

def _get_users():
    logger.debug("Starting get products from admin")
    req = requests.get('http://localhost:8000/api/user')

    if req.status_code == 200:
        return req.json()
    else:
        abort(404, 'Products not found!')

def _create_db():
    if len(sys.argv) > 1:
        if sys.argv[1]:
            print('Creting database')
            db.create_all()


def _setup_logger():
    global logger
    logFormatter = '> %(levelname)s - %(message)s'
    logging.basicConfig(format=logFormatter, level=logging.DEBUG)
    logger = logging.getLogger(__name__)


if __name__ == '__main__':
    _create_db()
    _setup_logger()
    app.run(debug=True, host='0.0.0.0', port=8001)
