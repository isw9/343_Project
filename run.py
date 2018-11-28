import configparser
from flask import Flask, render_template, request, session
import mysql.connector
import random

# Read configuration from file.
config = configparser.ConfigParser()
config.read('config.ini')

# Set up application server.
app = Flask(__name__)
#set secret key
app.secret_key = 'df934_f8s9f#450sdfcn'

# Create a function for fetching data from the database.
def sql_query(sql):
    db = mysql.connector.connect(**config['mysql.connector'])
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result


def sql_execute(sql):
    db = mysql.connector.connect(**config['mysql.connector'])
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    cursor.close()
    db.close()

# For this example you can select a handler function by
# uncommenting one of the @app.route decorators.


@app.route('/')
def template_response():
    return render_template('landing.html');

@app.route('/register_customer.html', methods=['GET', 'POST'])
def customer_register():
    print(request.form)
    # check no duplicate username
    sql_string = "select username from customer where username='%s'" %(request.form["username"])
    existing_usernames1 = sql_query(sql_string)

    sql_string = "select username from employee where username='%s'" %(request.form["username"])
    existing_usernames2 = sql_query(sql_string)
    
    # return to landing page, taken username
    if len(existing_usernames1) != 0 or len(existing_usernames2) != 0:
        return render_template('landing.html', success="Username already taken.");
    
    sql_string = "insert into customer (name, credit_card_num, street_address, city, state, username, password) values ('%s', %s, '%s', '%s', '%s', '%s', '%s')" % (request.form["name"], request.form["credit_card_num"], request.form["street_address"], request.form["city"], request.form["state"], request.form["username"], request.form["password"])

    sql_execute(sql_string)
    return render_template('landing.html', success="Success. Account created.")

@app.route('/register_employee.html', methods=['GET', 'POST'])
def employee_register():
    print(request.form)
    # check no duplicate username
    sql_string = "select username from employee where username='%s'" %(request.form["username"])
    existing_usernames1 = sql_query(sql_string)

    sql_string = "select username from customer where username='%s'" %(request.form["username"])
    existing_usernames2 = sql_query(sql_string)

    # return to landing page, taken username
    if len(existing_usernames1) != 0 or len(existing_usernames2) != 0 :
        return render_template('landing.html', success="Username already taken.")
    
    sql_string = "insert into employee (name, position, username, password) values ('%s', '%s', '%s', '%s')" %(request.form["name"], request.form["position"], request.form["username"], request.form["password"])

    sql_execute(sql_string)
    return render_template('landing.html', success='Success. Account created.')

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    # validate credentials
    sql_string = "select username from %s where username='%s' and password='%s'" %(request.form["role"], request.form["username"], request.form["password"])
    exists = sql_query(sql_string)
    if len(exists) == 0: #invalid combo
        session.clear()
        return render_template('landing.html', success="Invalid username or password.")
    else:
        # set cookie information
        session.clear()
        session["username"] = request.form["username"]
        session["role"] = request.form["role"]
    
        sql_string = "select id, name from %s where username='%s'" %(request.form["role"], request.form["username"])
        name_id = sql_query(sql_string);
        session["id"] = name_id[0][0];
        session["name"] = name_id[0][1];

        if ( session["role"] == "employee" ):
            sql_string = "select position from employee where id=%s" %(session["id"])
            session["position"] = sql_query(sql_string)[0][0];
            
        # add position if user is an employee
        if request.form["role"] == "customer":
            return render_template('customer_dashboard.html', name=session["name"])#name=request.form["name"])
        elif request.form["role"] == "employee":
            return load_employee_dashboard()
            #return render_template('employee_dashboard.html', name=session["name"])#name=request.form["name"])

@app.route('/employee_dashboard.html', methods=['GET', 'POST'])
def load_employee_dashboard():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info();
    template_data["position"] = session.get("position")

    '''
    if session.get("position") == "manager":
        return load_manager_dashboard()
    elif session.get("position") == "retail":
        return load_retail_dashboard()
    '''
    return render_template('employee_dashboard.html', data = template_data)

@app.route('/show_stores.html', methods=['GET', 'POST'])
def show_stores():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info();
    template_data["position"] = session.get("position")

    sql_string = "select id, name from location"
    template_data["stores"] = sql_query(sql_string)

    return render_template('show_stores.html', data = template_data)

@app.route('/view_store.html', methods=['GET', 'POST'])
def view_store():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info();
    template_data["position"] = session.get("position")

    store_id = request.form["store_id"]
    # gather store information
    sql_string = "select name, street_address, city, state from location where id=%s" %(store_id)
    template_data["store_info"] = sql_query(sql_string)[0]

    return render_template('view_store.html', data = template_data)

@app.route('/create_store.html', methods=['GET', 'POST'])
def create_store():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info();
    template_data["position"] = session.get("position")
    
    # create store using sql
    if "store_name" in request.form:
        sql_string = "insert into location (name, street_address, city, state) values ('%s', '%s', '%s', '%s')" %(request.form["store_name"], request.form["address"], request.form["city"], request.form["state"])
        sql_execute(sql_string)

        template_data['message'] = "Created new store."
        return render_template('employee_dashboard.html', data = template_data)
    
    # render form to choose store name
    else:
        return render_template('create_store.html', data = template_data)


@app.route('/new_item.html', methods=['GET', 'POST'])
def create_item():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info()
    template_data["position"] = session.get("position")

    # create item using sql
    if "item_name" in request.form:

        # if decide to drop quantity column, change string
        sql_string = "insert into items (name, price, quantity) values ('%s', '%s', 0)" %(request.form["item_name"], request.form["item_price"])
        sql_execute(sql_string)

        template_data['message'] = "Item created."
        return render_template('employee_dashboard.html', data = template_data)
    # render form to choose specify item
    else:
        return render_template('new_item.html', data = template_data)

@app.route('/stock_item.html', methods=['GET', 'POST'])
def stock_item():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info()
    template_data["position"] = session.get("position")

    # stock item using sql
    if "item_id" in request.form:
        item_id = request.form["item_id"]
        
        sql_string = "select id from location"
        store_ids = sql_query(sql_string)
        for store_id_tuple in store_ids:
            store_id = store_id_tuple[0]
            quantity_str = "%s_quantity" %(store_id)

            item_quantity = request.form[quantity_str]
            
            # obtain previous quantity
            sql_string = "select quantity from stores where location_id=%s and item_id=%s" %(store_id, item_id)
            prev_quantity_raw = sql_query(sql_string)

            # this location does not currently store this item
            if len(prev_quantity_raw) == 0:
                new_quantity = int(item_quantity)
                sql_string = "insert into stores (item_id, location_id, quantity) values (%s, %s, %s)" %(item_id, store_id, new_quantity)
                sql_execute(sql_string)
            else:
                prev_quantity = prev_quantity_raw[0][0]
                new_quantity = int(item_quantity) + int(prev_quantity)

                # update new quantity in stores table
                sql_string = "update stores set quantity=%s where location_id=%s and item_id=%s" %(new_quantity, store_id, item_id)
                sql_execute(sql_string)
        
        template_data['message'] = "Stocked item."
        return render_template('employee_dashboard.html', data = template_data)
    # render form to stock
    else:
        sql_string = "select id, name from items"
        template_data['item_list'] = sql_query(sql_string) # list of items

        sql_string = "select id, name from location"
        template_data['store_list'] = sql_query(sql_string) # list of stores
        
        return render_template('stock_item.html', data = template_data)

@app.route('/trash_item.html', methods=['GET', 'POST'])
def trash_item():
    if validate_employee() == False:
        return render_template('landing.html', success='Invalid authorization.')
    template_data = load_session_info()
    template_data["position"] = session.get("position")

    # execute sql to trash items
    if "ready to drop" in request.form:
        print(request.form)
        for store_id_raw, quantity in request.form.items():
            if store_id_raw != "ready to drop" and store_id_raw != "item_id": # ignore the confirmation key
                store_id = store_id_raw.split("_", 1)[0]

                sql_string = "select quantity from stores where item_id=%s and location_id=%s" %( request.form["item_id"], store_id)
                prev_quantity = sql_query(sql_string)[0][0]

                quantity_str = "%s_quantity" %(store_id) 
                item_quantity = request.form[quantity_str] # quantiity to remove

                new_quantity = int(prev_quantity) - int(item_quantity)
                #  if all items dropped, just remove the item from stores table
                if ( new_quantity <= 0 ):
                    sql_string = "delete from stores where item_id=%s and location_id=%s" %(request.form["item_id"], store_id)
                    sql_execute(sql_string)
                else:
                    sql_string = "update stores set quantity=%s where item_id=%s and location_id=%s" %(new_quantity, request.form["item_id"], store_id)
                    sql_execute(sql_string)

        template_data['message'] = "Item trashed."
        return render_template('employee_dashboard.html', data = template_data)
    
    # render form to choose quantities
    elif "item_id" in request.form:
        print("select quantities")
        template_data['choose_item'] = False;
        template_data['choose_quantities'] = True;

        # item name to drop
        sql_string = "select name from items where id=%s" %(request.form["item_id"])
        template_data['item_id'] = request.form["item_id"]
        template_data['item_name'] = sql_query(sql_string)[0][0]
        
        sql_string = '''select location_id, name, quantity 
from (stores cross join location) 
where item_id=%s and location_id = location.id''' %(request.form["item_id"])
        #print(sql_query(sql_string));
        template_data['store_quantities'] = sql_query(sql_string) # list of tuples

        return render_template('trash_item.html', data = template_data)
        
    # render form to choose item 
    else:
        sql_string = "select id, name from items"
        template_data['item_list'] = sql_query(sql_string) # list of items        
        template_data['choose_item'] = True;
        
        return render_template('trash_item.html', data = template_data)

    return render_template('trash_item.html', data = template_data)

@app.route('/logout.html', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('landing.html', success='Successfully logged out.')

def load_session_info():
    template_data = {}
    template_data["name"] = session.get("name")
    template_data["role"] = session.get("role")

    return template_data

# redirects to landing page if access unauthorized
def validate_employee():
    return session.get("role") == "employee"

def validate_customer():
    return session.get("role") == "customer"

#@app.route('/', methods=['GET', 'POST'])
def template_response_with_data():
    print(request.form)
    if "buy-book" in request.form:
        book_id = int(request.form["buy-book"])
        sql = "delete from book where id={book_id}".format(book_id=book_id)
        sql_execute(sql)
    template_data = {}
    sql = "select id, title from book order by title"
    books = sql_query(sql)
    template_data['books'] = books
    return render_template('home-w-data.html', template_data=template_data)

if __name__ == '__main__':
    app.run(**config['app'])