import unittest
import json
import re
import os
from datetime import datetime, timedelta
from app import server, initialize_database, db_file
from flask import jsonify

class APITest(unittest.TestCase):

    # Template Order
    dueDate = datetime.now() + timedelta(days=6)
    template_order = dict()
    template_order['name'] = 'John Smith'
    template_order['address'] = '9684 Constitution Court'
    template_order['city'] = 'Chesapeake'
    template_order['state'] = 'VA'
    template_order['zipcode'] = '23320'
    template_order['productType'] = 'Guitar'
    template_order['dueDate'] = dueDate.strftime("%m/%d/%Y")

    @classmethod
    def setUpClass(cls):
        initialize_database(db_file=db_file)

    @classmethod
    def tearDownClass(cls):
        os.remove(db_file)

    def setUp(self):
        self.applications = server.test_client()

    def test_root(self):
        result = self.applications.get('/')
        assert 200 == result.status_code
        
    def test_valid_orders(self):
        # Testing productType: Piano
        new_order = self.template_order.copy()
        new_order['productType'] = 'Piano'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 200 == result.status_code

        # Testing productType: Saxophone
        new_order = self.template_order.copy()
        new_order['productType'] = 'Saxophone'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        # Check Results
        assert 200 == result.status_code

        # Testing productType: Violin
        new_order = self.template_order.copy()
        new_order['productType'] = 'Violin'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        # Check Results
        assert 200 == result.status_code


    def test_order_creation(self):
        # Create order
        new_order = self.template_order.copy()
        order = json.dumps(new_order)
        result_post = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result_post = json.loads(result_post.data)
        # Check Results from POST
        assert 200 == result_post.status_code
        # Get the order again via GET
        result_get = self.applications.get('/sos/orders/' + json_result_post['id'])
        json_result_get = json.loads(result_get.data)
        # Check Results from GET
        assert 200 == result_get.status_code
        assert json_result_post == json_result_get['order']



    # Testing Invalid Scenarios!
    def test_empty_order(self):
        # Testing empty order
        new_order = '{}'
        result = self.applications.post('/sos/orders', content_type='application/json', data=new_order)
        json_result = json.loads(result.data)
        # Check Results
        assert 400 == result.status_code
        assert 'error' in json_result
        assert 'order is empty' == json_result['error']

    def test_invalid_due_date(self):
        # Right now
        new_order = self.template_order.copy()
        new_order['dueDate'] = datetime.now().strftime("%m/%d/%Y")
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'due date is too early' == json_result['error']

        # 2 days from now
        new_dueDate = datetime.now() + timedelta(days=2)

    def test_invalid_state(self):
        # FL
        new_order = self.template_order.copy()
        new_order['state'] = 'FL'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'state not in service' == json_result['error']

        # CA
        new_order = self.template_order.copy()
        new_order['state'] = 'CA'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'state not in service' == json_result['error']

        # TX
        new_order = self.template_order.copy()
        new_order['state'] = 'TX'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'state not in service' == json_result['error']


    def test_invalid_zipcodes(self):
        # 4 digits
        new_order = self.template_order.copy()
        new_order['zipcode'] = '0000'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'invalid zipcode' == json_result['error']

        # under the max
        new_order = self.template_order.copy()
        new_order['zipcode'] = '00600'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'invalid zipcode' == json_result['error']

        # Over the max
        new_order = self.template_order.copy()
        new_order['zipcode'] = '99951'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'invalid zipcode' == json_result['error']

        # 6 digits
        new_order = self.template_order.copy()
        new_order['zipcode'] = '999999'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'invalid zipcode' == json_result['error']

        # zip+4
        new_order = self.template_order.copy()
        new_order['zipcode'] = '00000-0000'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'no support for zip+4' == json_result['error']

        # zip+4 no dash
        new_order = self.template_order.copy()
        new_order['zipcode'] = '000000000'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'no support for zip+4' == json_result['error']

        # not only numbers
        new_order = self.template_order.copy()
        new_order['zipcode'] = '09asd'
        order = json.dumps(new_order)
        result = self.applications.post('/sos/orders', content_type='application/json', data=order)
        json_result = json.loads(result.data)
        assert 400 == result.status_code and 'error' in json_result and 'US zipcodes only contain digits' == json_result['error']


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(APITest)
    unittest.TextTestRunner(verbosity=2).run(suite)