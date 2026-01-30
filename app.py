from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM login WHERE username = %s AND passw = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            return redirect(url_for('index'))
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/product')
def index():
    connection = create_connection()
    if connection is None:
        return "Error connecting to the database", 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT productID, productNAME, pricePERunit, unitID FROM products")
        products = cursor.fetchall()
        
        # Map unitID to unitTYPE manually, if necessary
        for product in products:
            if product['unitID'] == 1:
                product['unitTYPE'] = "Per Item"
            elif product['unitID'] == 2:
                product['unitTYPE'] = "Per KG"
            else:
                product['unitTYPE'] = "Unknown"  # Handle other potential unit types if needed
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error fetching products", 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
    return render_template('productlist.html', data=products)


@app.route('/add_product')
def add_product():
    return render_template('add_product.html')

@app.route('/save_product', methods=['POST'])
def save_product():
    productNAME = request.form['productNAME']
    pricePERunit = request.form['pricePERunit']
    unitID = request.form['unitID']

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO products (productNAME, pricePERunit, unitID) VALUES (%s, %s, %s)", (productNAME, pricePERunit, unitID))
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('index'))

@app.route('/delete_product', methods=['POST'])
def delete_product():
    productNAME = request.form['productNAME']

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM products WHERE productNAME = %s", (productNAME,))
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('index'))

@app.route('/customer_list')
def customer_list():
    connection = create_connection()
    if connection is None:
        return "Error connecting to the database", 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers")
        customers = cursor.fetchall()
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error fetching products", 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('customerlist.html', data=customers)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    customerNAME = request.form.get('customerNAME')
    customerEMAIL = request.form.get('customerEMAIL')
    customerPHONE = request.form.get('customerPHONE')

    connection = create_connection()
    if connection is None:
        return "Error connecting to the database", 500

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO customers (customerNAME, customerEMAIL, customerPHONE) VALUES (%s, %s, %s)",
            (customerNAME, customerEMAIL, customerPHONE)
        )
        connection.commit()
        return "Customer added successfully.", 200
    except Error as e:
        connection.rollback()
        return f"Error: {str(e)}", 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/order_list')
def order_list():
    connection = create_connection()
    if connection is None:
        return "Error connecting to the database", 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders")
        orders = cursor.fetchall()
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error fetching orders", 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
    return render_template('orderlist.html', data=orders)



@app.route('/add_order', methods=['GET'])
def add_order():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT productID, productNAME FROM products")
        products = cursor.fetchall()  # Fetch all products to populate dropdown
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error fetching products", 500
    finally:
        cursor.close()
        connection.close()

    return render_template('add_order.html', products=products)



@app.route('/save_order', methods=['POST'])
def save_order():
    customerID = request.form['customerID']
    orderDate = request.form['orderDate']
    productNames = request.form.getlist('productNames[]')
    quantities = request.form.getlist('quantities[]')

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch products for the dropdown in case of error
    cursor.execute("SELECT productNAME FROM products")
    products = cursor.fetchall()

    try:
        # Check if the customer ID exists
        cursor.execute("SELECT * FROM customers WHERE customerID = %s", (customerID,))
        customer = cursor.fetchone()
        if not customer:
            error_message = "Error: Customer ID does not exist."
            return render_template('add_order.html', products=products, error_message=error_message)

        # Create a new order entry in `orders` table
        cursor.execute("INSERT INTO orders (customerID, orderDate) VALUES (%s, %s)", (customerID, orderDate))
        orderID = cursor.lastrowid

        # Loop through products to add them to `order_items`
        for productName, quantity in zip(productNames, quantities):
            # Look up the product ID from the product name
            cursor.execute("SELECT productID FROM products WHERE productNAME = %s", (productName,))
            product = cursor.fetchone()
            if not product:
                error_message = f"Error: Product '{productName}' does not exist."
                return render_template('add_order.html', products=products, error_message=error_message)

            productID = product['productID']
            cursor.execute(
                "INSERT INTO order_items (orderID, productID, quantity) VALUES (%s, %s, %s)",
                (orderID, productID, quantity)
            )

        connection.commit()
        return redirect(url_for('order_list'))

    except Error as e:
        print(f"The error '{e}' occurred")
        connection.rollback()
        return "An error occurred while saving the order.", 500
    finally:
        cursor.close()
        connection.close()


@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    connection = create_connection()
    if connection is None:
        return "Error connecting to the database", 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Fetch order details
        cursor.execute("""
            SELECT o.orderID, o.customerID, o.orderDate, p.productNAME, oi.quantity, p.pricePERunit
            FROM orders o
            JOIN order_items oi ON o.orderID = oi.orderID
            JOIN products p ON oi.productID = p.productID
            WHERE o.orderID = %s
        """, (order_id,))
        
        order_items = cursor.fetchall()
        total_price = 0
        for item in order_items:
            item['total_price'] = item['pricePERunit'] * item['quantity']
            total_price += item['total_price']

    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error fetching order details", 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('order_details.html', order_id=order_id, order_items=order_items, total_price=total_price)





if __name__ == "__main__":
    app.run()
