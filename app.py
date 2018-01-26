from flask import Flask, jsonify, request, abort, make_response, render_template
from datetime import datetime, timedelta
import uuid, re

# Flask light-weight web server.
server = Flask(__name__)


# In-memory Databases - Dynamic Dictionaries
orders = dict()
products = ['Movie','Song', 'Photo']
bad_states = ['CA','TX','FL']

##########################
##### REST SERVICES ######
##########################

# For load-balancing checks
@server.route('/', methods=['GET'])
def get_root():
    return render_template('oep.html', entries=products)


# Get a specific order by calling /ovs/orders/<order_id>
@server.route('/ovs/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    # if the id is on our 'orders' database return it, if not, return 404
    if orders.has_key(str(order_id)):
        return jsonify({'order': orders.get(str(order_id))})
    else:
        abort(404)


# Get all orders by calling /ovs/orders/
@server.route('/ovs/orders', methods=['GET'])
def get_all_order():
    # return everything in out 'orders' database
    return jsonify({'orders': orders.values()})


# Order Validation Service
@server.route('/ovs/orders', methods=['POST'])
def post_order():

    # Get the Json order from the request
    if (request.headers['Content-Type'] == 'application/json'):
        new_order = request.json
    elif (request.headers['Content-Type'] == 'application/x-www-form-urlencoded'):
        new_order = dict()
        new_order['name'] = request.form['name']
        new_order['address'] = request.form['address']
        new_order['city'] = request.form['city']
        new_order['state'] = request.form['state']
        new_order['zipcode'] = request.form['zipcode']
        new_order['dueDate'] = request.form['dueDate']

    # validate order
    valid,error_msg = order_field_validation(new_order)
    if not valid:
        return jsonify({'error': error_msg}), 400

    # Generate an ID for this order.
    order_id = uuid.uuid4()
    # Add the ID to the order json object
    new_order['id'] = str(order_id.hex)
    # Add the order to the database
    orders[str(order_id.hex)] = new_order
    # Returns the order created with generated ID
    return jsonify(new_order)



##########################
#### HELPER FUNCTIONS ####
##########################

# Order Validation, returns a tuple, (boolean,string)
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

# CHeck if the order is not empty.
def validate_empty_order(order={}):
    if not order:
        return False, 'order is empty'
    else:
        return True, ''

# Check if the state is not part of the bad states
def validate_states(order={}):
    if order['state'] in bad_states:
        return False, 'state not in service'
    else:
        return True, ''

# Check if the due date is not too early (or in the past!)
def validate_due_date(order={}):
    if (datetime.strptime(order['dueDate'],"%m/%d/%Y") - datetime.now()).days < 5:
        return False, 'due date is too early'
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


# Helper respond method for 404 errors
@server.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=80, debug=True)