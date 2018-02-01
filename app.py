import os
import errno
import sqlite3
import socket
import re
from flask import Flask, jsonify, request, abort, make_response, render_template, url_for
from datetime import datetime, timedelta

# Flask light-weight web server.
server = Flask(__name__)
server_name = 'sos'
host = os.getenv('VCAP_APP_HOST', '0.0.0.0')
port = int(os.getenv('VCAP_APP_PORT', '80')) # So cloud foundry can insert the right port
debug = True


# In-memory Databases - Dynamic Dictionaries
orders = dict()
products = ['Error_Test', 'Piano', 'Saxophone', 'Flute', 'Base', 'Drums', 'Viola', 'Violin']
bad_states = ['CA','TX','FL']

# Local Storage DB
db_name = '{0}.db'.format(server_name)
db_location = os.getenv('SQLITE_DB_LOCATION', '/var/lib/sqlite/')
db_file = os.path.normpath(os.path.join(db_location, db_name))
db_conn = None 

##########################
##### REST SERVICES ######
##########################

# Helper function for generating 404 errors
@server.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# Returns the main form. Utilizes the oep.html template
@server.route('/', methods=['GET'])
def get_root():
    return render_template('oep.html', entries=products, server_name=str(server_name).upper())

# Returns the hostname.
@server.route('/hostname', methods=['GET'])
def get_hostname():
    print(url_for('static', filename='style.css'))
    return render_template('hostname.html', hostname=str(socket.gethostname()))

# Get a specific order by calling /{server_name}/orders/<order_id>
@server.route('/{0}/orders/<order_id>'.format(server_name), methods=['GET'])
def get_order(order_id):
    db_conn = sqlite3.connect(db_file)
    try:
        c = db_conn.cursor()
        t = (int(order_id),)
        c.execute('SELECT * FROM orders WHERE id=?', t)
        order = c.fetchone()
        # if the id is on our 'orders' database return it, if not, return 404
        if order:
            new_order = dict()
            new_order['_id'] =          order[0]
            new_order['id'] =       str(order[0])
            new_order['name'] =         order[1]
            new_order['address'] =      order[2]
            new_order['city'] =         order[3]
            new_order['state'] =        order[4]
            new_order['zipcode'] =      order[5]
            new_order['dueDate'] =      order[6]
            new_order['productType'] =  order[7]
            return jsonify({'order': new_order})
        else:
            abort(404)
    finally:
        if db_conn:
            db_conn.close()


# Get all orders by calling /{server_name}/orders
@server.route('/{0}/orders'.format(server_name), methods=['GET'])
def get_all_order():
    db_conn = sqlite3.connect(db_file)
    print('in get_all_order')
    c = db_conn.cursor()
    new_orders = []
    try:
        for row in c.execute('SELECT * FROM orders ORDER BY id'):
            new_order = dict()
            new_order['_id'] =          row[0]
            new_order['id'] =       str(row[0])        
            new_order['name'] =         row[1]
            new_order['address'] =      row[2]
            new_order['city'] =         row[3]
            new_order['state'] =        row[4]
            new_order['zipcode'] =      row[5]
            new_order['dueDate'] =      row[6]
            new_order['productType'] =  row[7]
            new_orders.append(new_order)
    finally:
        if db_conn:
            db_conn.close()

    # return everything in our 'orders' database
    return jsonify({'orders': new_orders})


# Post new order
@server.route('/{0}/orders'.format(server_name), methods=['POST'])
def post_order():
    db_conn = sqlite3.connect(db_file)
    # Get the Json order from the request
    if (request.headers['Content-Type'] == 'application/json'): # if already json, parse it as such
        new_order = request.json
    elif (request.headers['Content-Type'] == 'application/x-www-form-urlencoded'): # if post params, parse into json
        new_order = dict()
        new_order['name'] = request.form['name']
        new_order['address'] = request.form['address']
        new_order['city'] = request.form['city']
        new_order['state'] = request.form['state']
        new_order['zipcode'] = request.form['zipcode']
        print(str(request.form['dueDate']))
        new_order['dueDate'] = get_date(str(request.form['dueDate'])).strftime('%m/%d/%Y')
        new_order['productType'] = request.form['productType']

    # call the order validation function
    valid,error_msg = order_field_validation(new_order)

    # If not valid, return status 400 (bad request) with a json body containing the error message.
    if not valid:
        return jsonify({'error': error_msg}), 400

    # Instert into database
    try:
        c = db_conn.cursor()
        rows = (
            'name', 
            'address', 'city', 
            'state', 'zipcode', 
            'dueDate', 'productType', 
        )
        values = (
            new_order['name'], 
            new_order['address'], new_order['city'], 
            new_order['state'], new_order['zipcode'], 
            new_order['dueDate'], new_order['productType'], 
        )
        order_id = insert(db_conn, 'orders', rows, values)
        
        # Get order id (by rowid)
        new_order['_id'] = order_id     # Integer id
        new_order['id'] = str(order_id)  # String id
    finally:
        if db_conn:
            db_conn.close()

    # Return the order created with generated ID
    return jsonify(new_order)




##########################
#### HELPER FUNCTIONS ####
##########################

# Order Validation, returns a tuple, (boolean,string)
# This is doing sequential validation for now...
def order_field_validation(order={}):

    valid,error = validate_empty_order(order=order)
    if not valid:
        return valid, error

    valid,error = validate_states(order=order)
    if not valid:
        return valid, error

    valid,error = validate_due_date(order=order)
    if not valid:
        return valid, error

    valid,error = validate_zipcodes(order=order)
    if not valid:
        return valid, error

    return True, ''


# Helper: Empty request validation.
def validate_empty_order(order={}):
    if not order:
        return False, 'order is empty'
    else:
        return True, ''

# Check if the due date is not too early (or in the past!) or empty
def validate_due_date(order={}):
    if (str(order['dueDate']) is "" or order['dueDate'] is None):
        return False, 'due date is empty'
    due_date = get_date(str(order['dueDate']))
    if (due_date - datetime.now()).days < 5:
        return False, 'due date is too early'
    else:
        return True, ''


# Check if the state is not part of the bad states
def validate_states(order={}):
    if order['state'] in bad_states:
        return False, 'state not in service'
    else:
        return True, ''


# Check if the zipcode is valid
def validate_zipcodes(order={}):
    if re.match(r'(^[0-9]{5}-?[0-9]{4})$', order['zipcode']):
        return False, 'no support for zip+4'
    elif not re.match(r'^[0-9]+$', order['zipcode']):
        return False,'US zipcodes only contain digits'
    elif (not re.match('^[0-9]{5}$',order['zipcode']))\
            or (int(order['zipcode']) < 601)\
            or (int(order['zipcode']) > 99950):
        return False,'invalid zipcode'
    else:
        return True, ''


def get_date(str_date=None):
    ret_date = None
    if str_date:
        # Try to convert date
        try:
            ret_date = datetime.strptime(str_date,"%m/%d/%Y")
        except ValueError as ve:
            ret_date = datetime.strptime(str_date,"%Y-%m-%d")
        except Exception as e:
            raise
    return ret_date


# Simple insert
def insert(db_conn, table, fields=(), values=()):
    # g.db is the database connection
    cur = db_conn.cursor()
    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
        table,
        ', '.join(fields),
        ', '.join(['?'] * len(values))
    )
    cur.execute(query, values)
    db_conn.commit()
    id = cur.lastrowid
    cur.close()
    return id


# Initialize the Database
def initialize_database(db_file=None):
    '''Initialize the database, we assume that if the DB file exists then the DB was created.
    '''
    db_conn = None
    if not db_file:
        raise Exception("Database cannot be initialized: Database file was {0}.".format(db_file))
    # Check if the db file exists, if it does not, we create the entire DB
    if not os.path.exists(db_file):
        # Create the directory, don't error out if it already exists.
        try:
            os.makedirs(os.path.dirname(db_file))
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        # Create database connection
        db_conn = sqlite3.connect(db_file)
        if not db_conn:
            raise Exception("Database cannot be initialized: Database connection was {0}.".format(db_conn))
        # Now create all tables
        c = db_conn.cursor()
        # 'orders' table 
        c.execute('''CREATE TABLE orders 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name text, address text, city text, state text, zipcode text, dueDate text, productType text)''')
        print('The table "orders" has been created.')
        # Save (commit) the changes
        db_conn.commit()
        db_conn.close()
    else:
        print('Database file \'{0}\' exists, no need for initialization.'.format(db_file))


if __name__ == '__main__':
    initialize_database(db_file=db_file)
    server.run(host=host, port=port, debug=debug)
