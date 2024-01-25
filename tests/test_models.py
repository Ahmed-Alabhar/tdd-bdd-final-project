# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
from decimal import Decimal
from unittest.mock import patch
import unittest

from service import app
from service.models import Product, Category, db, DataValidationError
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods


class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_update_nonexistent_product(self):
        """It should raise DataValidationError when updating a nonexistent Product"""
        non_existent_product = Product(
                id=None,
                name="NonExistent",
                description="Does not exist",
                price=0,
                available=False,
                category=Category.UNKNOWN)
        with self.assertRaises(DataValidationError) as context:
            non_existent_product.update()

        self.assertIn("Update called with empty ID field", str(context.exception))

    def test_deserialize_invalid_boolean(self):
        """It should raise DataValidationError for invalid boolean value"""
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "10.00",
            "available": "invalid_boolean_value",  # Not a boolean
            "category": "CLOTHS",
        }
        with self.assertRaises(DataValidationError):
            product = Product()
            product.deserialize(data)

    def test_deserialize_type_error(self):
        """It should raise DataValidationError for TypeError during deserialization"""
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "10.00",
            "available": True,
            "category": "CLOTHS",
        }

        # Create a Product instance
        product = Product()

        # Set up a mock to simulate a TypeError during deserialization
        with patch.object(Product, "__setattr__", side_effect=TypeError("Test Type Error")):
            with self.assertRaises(DataValidationError):
                # Trigger the deserialization with the mocked behavior
                product.deserialize(data)

    def test_deserialize_attribute_error(self):
        """It should raise DataValidationError for AttributeError during deserialization"""
        data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "10.00",
            "available": True,
            "category": "CLOTHS",
        }

        # Create a Product instance
        product = Product()

        # Set up a mock to simulate an AttributeError during deserialization
        with patch.object(Product, "__setattr__", side_effect=AttributeError("Test Attribute Error")):
            with self.assertRaises(DataValidationError):
                # Trigger the deserialization with the mocked behavior
                product.deserialize(data)

    def test_find_by_price(self):
        """It should Find Products by Price"""
    # Create 5 Products with a specific price
        target_price = Decimal("20.00")
        for _ in range(5):
            product = ProductFactory(price=target_price)
            product.create()

    # Create an additional product with a different price
        different_price = Decimal("25.00")
        different_product = ProductFactory(price=different_price)
        different_product.create()

    # Query for products with the target price
        found_products = Product.find_by_price(target_price)

    # Assert that the correct number of products with the target price is returned
        self.assertEqual(found_products.count(), 5)

    # Assert that all returned products indeed have the target price
        for product in found_products:
            self.assertEqual(product.price, target_price)

    # Query for products with the different price
        found_different_products = Product.find_by_price(different_price)

    # Assert that the correct number of products with the different price is returned
        self.assertEqual(found_different_products.count(), 1)

    # Assert that the returned product indeed has the different price
        self.assertEqual(found_different_products[0].price, different_price)

    def test_find_by_price_with_string_price(self):
        """It should Find Products by Price when price is passed as a string"""
        # Create a product with a specific price
        target_price = Decimal("20.00")
        product = ProductFactory(price=target_price)
        product.create()
        # Query for products with the target price as a string
        found_products = Product.find_by_price(' "20.00" ')
        # Assert that the correct number of products with the target price is returned
        self.assertEqual(found_products.count(), 1)
        # Assert that the returned product indeed has the target price
        self.assertEqual(found_products[0].price, target_price)
