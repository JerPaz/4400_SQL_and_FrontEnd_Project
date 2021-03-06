from flask import (Flask, session, redirect, url_for,
                   request, render_template, flash, Response)
import pymysql
import re
import os
import json
from datetime import date, timedelta, datetime
app = Flask(__name__)

conn = pymysql.connect(host='localhost', user='root',
                       db='cs4400spring2020', passwd='password')

c = conn.cursor()

# ===============================================
# UTILITY
# ===============================================


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

# ===============================================
# GENERAL USER MGMT AND HOME
# ===============================================


@app.route("/")
def home():
    if session.get('username'):
        if 'Admin' in session.get('userType'):
            print ("dbg: home admin screen")
            return render_template('home_admin.html')
        if 'Manager' in session.get('userType'):
            print ("dbg: home manager screen")
            return render_template('home_manager.html')
        if 'Staff' in session.get('userType'):
            print ("dbg: home customer/staff screen")
            return render_template('home_customer.html')
        if 'Customer' in session.get('userType'):
            print ("dbg: home customer screen")
            return render_template('home_customer.html')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        sql = ("CALL login('{u}', '{p}');".format(
            u=request.form['username'], p=request.form['password']))
        result = c.execute(sql)

        if result:
            # retrieve username and usertype
            c.execute("SELECT * FROM login_result;")
            row = c.fetchone()
            flash('You were logged in', 'alert-success')
            session['username'] = row[0]
            session['userType'] = row[1]
            print("redirecting to home")
            return redirect(url_for('home'))
        else:
            flash('Incorrect login', 'alert-error')

    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    session.pop('userType', None)
    session.pop('selected_food_truck', None)
    flash('Logout Success', 'alert-success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if session.get('username'):
        return redirect(url_for('home'))
    print("dbg1")
    if request.method == 'POST':
        print("dbg2")
        if request.form['password'] != request.form['passwordconf']:
            flash('Passwords do not match!', 'alert-error')
            return render_template('register.html', error=error)

        print("dbg5")

        # get values
        username = request.form['username']
        print("dbg6")
        email = request.form['email']
        print("dbg7")
        lastName = request.form['lastName']
        print("dbg8")
        firstName = request.form['firstName']
        print("dbg9")
        password = request.form['password']
        print("dbg10")
        balance = request.form['balance']
        print("dbg11")
        userType = request.form['userType']
        print("dbg11")

        # TODO check if combination of first
        # and last name is unique for all users

        print(balance)
        if 'Customer' in userType and balance == '':
            flash('Must have a balance if a customer', 'alert-error')
            return render_template('register.html', error=error)
        try:
            balance = int(balance)
        except:
            balance = 0
        if 'Customer' in userType and balance < 1:
            flash('balance must be positive!', 'alert-error')
            return render_template('register.html', error=error)
        if len(password) < 8:
            flash('password must be atleast 8 characters long!', 'alert-error')
            return render_template('register.html', error=error)
        if not re.search("[^@]+@[^@]+\.[^@]+", email):
            flash('provide a proper email!', 'alert-error')
            return render_template('register.html', error=error)

        sql = "CALL register('{u}', '{e}', '{f}', '{l}', '{p}', {b}, '{t}');".format(
            u=username, e=email, f=firstName, l=lastName, p=password, b=balance, t=userType)

        # dbg
        print("dbg3")
        print(sql)

        try:
            result = c.execute(sql)
            conn.commit()
        except pymysql.err.IntegrityError:
            flash('Username exists!', 'alert-error')
            return render_template('register.html', error=error)
        except:
            flash('Something happened!', 'alert-error')
            return render_template('register.html', error=error)

        print("dbg4")

        flash('Registered', 'alert-success')
        return redirect(url_for('login'))
    return render_template('register.html', error=error)

# ===========================================
# MY MEMBER FUNCTIONS
# ===========================================

############################manager#########


@app.route('/manager_manage_food_truck', methods=['GET'])
def manager_manage_food_truck():
    error = None
    return render_template('manager_manage_food_truck', error=error)


@app.route('/manager_food_truck_summary', methods=['GET'])
def manager_food_truck_summary():
    return

############################admin###########


@app.route('/admin_manage_building_and_station', methods=['GET', 'POST'])
def admin_manage_building_and_station():

    filter_building_station_sql = "CALL ad_filter_building_station('', '', '', NULL, NULL);"
    c.execute(filter_building_station_sql)
    filter_building_station_table_sql = "SELECT * FROM ad_filter_building_station_result;"
    c.execute(filter_building_station_table_sql)
    filter_table = c.fetchall()
    filter_dict_list = []
    building_name_list = []
    station_name_list = []
    for i in range (len(filter_table)):
        filter_dict = {'building_name': filter_table[i][0], 'building_tags': filter_table[i][1], 
        'station_name': filter_table[i][2], 'capcity': filter_table[i][3],
        'food_truck_names': filter_table[i][4]}
        #if filter_table[i][1] != None:
            #filter_dict[i][1] = filter_table[i][1].replace(",", ", ")
        if filter_table[i][4] != None:
            filter_dict['food_truck_names'] = filter_table[i][4].replace(",", ", ")
        filter_dict_list.append(filter_dict)
    for i in range (len(filter_dict_list)):
        if filter_dict_list[i]['building_name'] != None:
            building_name_list.append(filter_dict_list[i]['building_name'])
        if filter_dict_list[i]['station_name'] != None:
            station_name_list.append(filter_dict_list[i]['station_name'])

    if not request.method == 'POST':
        return render_template('/admin_manage_building_and_station.html', filter_dict_list=filter_dict_list,
        building_name_list=building_name_list, station_name_list=station_name_list, error=None)

    if request.method == 'POST':
        if 'filter_input_reset' in request.form:
            return (redirect(url_for('admin_manage_building_and_station')))

        if 'filter_input' in request.form:
            print(building_name_list)
            print(station_name_list)
            building_name = request.form['building_name']
            station_name = request.form['station_name']
            building_tag = request.form['building_tag']
            min_capacity = request.form['min_capacity_input']
            max_capacity = request.form['max_capacity_input']
            if min_capacity == '' and max_capacity == '':
                min_capacity = None
                max_capacity = None
            elif min_capacity != '' and max_capacity == '':
                max_capcity = None
            elif min_capacity == '' and max_capacity != '':
                min_capacity = None
            if min_capacity != None and max_capacity != None:
                if min_capacity > max_capacity:
                    flash('Max capacity cannot be greater than min capacity in range', 'alert-error')
                    return redirect(url_for('admin_manage_building_and_station'))   
            # better way to format an SQL statement and execute it
            filter_building_station_sql = "CALL ad_filter_building_station(%s, %s, %s, %s, %s)"
            c.execute(filter_building_station_sql, (building_name, building_tag, station_name, min_capacity, max_capacity))
            filter_building_station_table_sql = "SELECT * FROM ad_filter_building_station_result;"
            c.execute(filter_building_station_table_sql)
            filter_table = c.fetchall()
            filter_dict_list = []
            for i in range (len(filter_table)):
                filter_dict = {'building_name': filter_table[i][0], 'building_tags': filter_table[i][1].replace(",", ", "), 
                'station_name': filter_table[i][2], 'capcity': filter_table[i][3],
                'food_truck_names': filter_table[i][4]}
                if filter_table[i][4] != None:
                    filter_dict['food_truck_names'] = filter_table[i][4].replace(",", ", ")
                filter_dict_list.append(filter_dict)
            return render_template('/admin_manage_building_and_station.html', filter_dict_list=filter_dict_list,
            building_name_list=building_name_list, station_name_list=station_name_list, error=None)
        
        # TODO implement update and create building functions

        if 'create_building_input' in request.form:
            return redirect(url_for('admin_create_building'))
        
        if 'delete_building_input' in request.form:
            session['admin_select_building'] = request.form['radiobutton']
            return redirect(url_for('admin_update_building'))

        if 'delete_building_input' in request.form:
            try:
                selected_building = request.form['radiobutton']
            except:
                flash('Must go back to the home page or select one of the choices to delete building', 'alert-error')
                return(redirect(url_for('admin_manage_building_and_station')))
            delete_building_sql = "CALL ad_delete_building(%s);"
            try:
                c.execute(delete_building_sql, selected_building)
            except:
                flash('If deleting a building, must make sure no remaining food trucks are connected to it', 'alert-error')
                return redirect(url_for('admin_manage_building_and_station'))
            conn.commit()
            flash('You have deleted building {}'.format(selected_building))
            return redirect(url_for('admin_manage_building_and_station'))

        
        if 'delete_station_input' in request.form:
            try:
                selected_building = request.form['radiobutton']
                selected_station = ''
                for i in range(len(filter_dict_list)):
                    #print(filter_dict_list[i])
                    if filter_dict_list[i]['building_name'] == selected_building:
                        print(filter_dict_list[i])
                        selected_station = filter_dict_list[i]['station_name']
            except:
                flash('Must go back to the home page or select on of the choices to delete station', 'alert-error')
                return(redirect(url_for('admin_manage_building_and_station')))
            print(selected_station)
            delete_station_sql = "CALL ad_delete_station(%s);"
            try:
                c.execute(delete_station_sql, selected_station)
            except:
                flash('If deleting a station, must make sure there are no remaining food trucks connected to it', 'alert-error')
                return (redirect(url_for('admin_manage_building_and_station')))
            conn.commit()
            flash('You have deleted station {}'.format(selected_station))
            return redirect(url_for('admin_manage_building_and_station'))

        return redirect(url_for('admin_manage_building_and_station'))

    return redirect(url_for('admin_manage_building_and_station'))

@app.route('/admin_create_building', methods=['GET', 'POST'])
def admin_create_building():
    error = None

    if not request.method == 'POST':
        tag_list = []
        index = 0
        return render_template('admin_create_building.html', error=error)

    if request.method == 'POST':
        if 'create_building_input' in request.form:
            building_name = request.form['building_name_input']
            description = request.form['description_input']
            tag_list = []
            index = 0
            while True:
                try:
                    tag_list.append(request.form['hidden_input_{}'.format(index)])
                    index += 1
                except:
                    break
            try:
                create_building_sql = "CALL ad_create_building(%s, %s)"
                c.execute(create_building_sql, (building_name, description))
                conn.commit()
            except:
                flash('Builindg already exist.', 'alert-error')
                return redirect(url_for('admin_create_building'))
            for i in range(len(tag_list)):
                add_tag_sql = "CALL ad_add_building_tag(%s, %s)"
                c.execute(add_tag_sql, (building_name, description))
                conn.commit()
            return redirect(url_for('admin_create_building'))
            
    return redirect(url_for('admin_create_building'))

@app.route('/admin_update_building', methods=['GET','POST'])
def admin_update_building():
    error = None

    if request.method != 'POST':
        return render_template('admin_update_building.html', error=error)
    
    if request.method == 'POST':
        return redirect(url_for('admin_update_building'))

    return redirect(url_for('admin_update_building'))

@app.route('/admin_create_food', methods=['GET', 'POST'])
def admin_create_food():
    error = None

    if not request.method == 'POST':
        return render_template('/admin_create_food.html', error=error)

    if request.method == 'POST':
        food_input = request.form['create_food_input']
        try:
            # Still a bug since  I do not check case sensitivity; I know the fix
            # but maybe for a later implementation
            c.execute("INSERT INTO Food(foodName) VALUES('{f_n}');".format(
                f_n=food_input))
            conn.commit()
            flash('{f_n} successfully created'.format(f_n=food_input))
        except:
            print("dbg 12: excepted")
            flash('Food already exist.', 'alert-error')
        print(food_input)
        return redirect(url_for('admin_create_food'))

    return redirect(url_for('admin_create_food'))

############################customer########


@app.route('/customer_explore', methods=['GET', 'POST'])
def customer_explore():
    error = None

    name_list_sql = "SELECT * FROM cs4400spring2020.Station;"
    c.execute(name_list_sql)
    name_list_tuple = c.fetchall()
    name_dict_list = []
    for i in range(len(name_list_tuple)):
        name_dict = {'station_name': name_list_tuple[i][1], 'building_name': name_list_tuple[i][0]}
        name_dict_list.append(name_dict)

    if not request.method == 'POST':
        filter_explore_sql = "CALL cus_filter_explore('', '', '', '', '');"
        c.execute(filter_explore_sql)
        filter_explore_table = "SELECT * FROM cus_filter_explore_result;"
        c.execute(filter_explore_table)
        filter_table = c.fetchall()
        filter_dict_list = []
        for i in range(len(filter_table)):
            filter_dict = {'station': filter_table[i][0], 'building': filter_table[i][1], 
            'food_truck_name': filter_table[i][2].replace(',', ', '),'food':filter_table[i][3].replace(',', ', ')}
            filter_dict_list.append(filter_dict)
        # print(filter_dict_list)
        return render_template('/customer_explore.html', filter_dict_list=filter_dict_list, name_dict_list=name_dict_list, error=error)
    
    if request.method == 'POST':
        if 'filter_input' in request.form:
            print("dbg: it works")
            station_name = request.form['station_name']
            building_name = request.form['building_name']
            building_tag = request.form['building_tag']
            food_truck_name = request.form['food_truck_name']
            food_name = request.form['food']

            filter_explore_sql = "CALL cus_filter_explore('{s_n}', '{b_n}', '{b_t}', '{f_t_n}', '{f_n}');".format(
                s_n=station_name, b_n=building_name, b_t=building_tag, f_t_n=food_truck_name, f_n=food_name)
            c.execute(filter_explore_sql)
            filter_explore_table = "SELECT * FROM cus_filter_explore_result;"
            c.execute(filter_explore_table)
            filter_table = c.fetchall()
            filter_dict_list = []
            for i in range(len(filter_table)):
                filter_dict = {'station': filter_table[i][0], 'building': filter_table[i][1], 
                'food_truck_name': filter_table[i][2].replace(',', ', '),'food':filter_table[i][3].replace(',', ', ')}
                filter_dict_list.append(filter_dict)
            print(filter_dict_list)
            return render_template('/customer_explore.html', filter_dict_list=filter_dict_list, name_dict_list=name_dict_list, error=error)
        elif 'location_input' in request.form:
            try:
                selected_station = request.form['radiobutton']
            except:
                flash('Must go back to the home page or select one of the choices', 'alert-error')
                return redirect(url_for('customer_explore'))
            print(selected_station)
            select_location_sql = "CALL cus_select_location ('{cus_user}', '{station_name}');".format(
                cus_user=session['username'], station_name=selected_station)
            c.execute(select_location_sql)
            conn.commit()
            flash('You have set your location to the {}'.format(selected_station))
        return redirect(url_for('customer_current_information'))
    
    return redirect(url_for('customer_explore'))

@app.route('/customer_current_info', methods=['GET', 'POST'])
def customer_current_information():
    error = None
    
    cur_info_sql = "CALL cus_current_information_basic('{cus_user}');".format(
        cus_user=session['username'])
    c.execute(cur_info_sql)
    cur_info_table_sql = "SELECT * FROM cs4400spring2020.cus_current_information_basic_result;"
    c.execute(cur_info_table_sql)
    cus_info_tuple = c.fetchall()
    info_row = cus_info_tuple[0]
    cus_info_dict = {'station': info_row[0], 'building': info_row[1], 'building_tags': info_row[2], 'building_description': info_row[3], 'balance': info_row[4]}
    
    cur_ft_info = "CALL cus_current_information_foodTruck('{cus_user}');".format(
        cus_user=session['username'])
    c.execute(cur_ft_info)
    cur_ft_info_table = "SELECT * FROM cs4400spring2020.cus_current_information_foodTruck_result"
    c.execute(cur_ft_info_table)
    ft_info_table = c.fetchall()
    ft_dict_list = []
    for i in range(len(ft_info_table)):
        ft_dict = {'food_truck_name': ft_info_table[i][0], 'manager_name': ft_info_table[i][1], 'food_names': ft_info_table[i][2].replace(",", ", ")}
        ft_dict_list.append(ft_dict)
    
    if not request.method == 'POST':
        return render_template('/customer_current_info.html', cus_info_dict=cus_info_dict, ft_dict_list=ft_dict_list, error=error) 

    if request.method == 'POST':
        try:
            session['selected_food_truck'] = str(request.form['radiobutton'])
        except:
            flash('Must go back to the home page or select one of the choices', 'alert-error')
            return redirect(url_for('customer_current_information'))
        return redirect('/customer_order')

    return redirect('/customer_current_info')

#For form submitting, look at PRG design pattern (post, redirect, get)
#Add food_truck information
@app.route('/customer_order', methods=['GET', 'POST'])
def customer_order():
    error = None
    send_order = False
    order_date = str(date.today())
    order_dict_list = []
    order_foods = []
    order_prices = []
    
    # Go back to commit 4c675f57469d27840e17dfbcee2fe3ab63586012 () to see previous massive overhaul
    # order displays ALL food trucks at the station
    try:
        food_sql = "SELECT foodName, price FROM cs4400spring2020.MenuItem WHERE foodTruckName = '{ft}';".format(
            ft=str(session['selected_food_truck']))
    except:
        flash('Must first select a food truck to order', 'alert-error')
        return redirect(url_for('customer_current_information'))
    c.execute(food_sql)
    food_column = c.fetchall()
    food_dict_list = []
    # the 'food_name_input_{}' is very important in distinguishing tags to manipulate
    for i in range(len(food_column)):
        food_dict = {'food_name': food_column[i][0], 'food_price': food_column[i][1], 'food_truck': session['selected_food_truck'],
            'food_name_input': 'food_name_input_{}'.format(i), 'purchase_quantity_input': 'purchase_quantity_input_{}'.format(i)}
        food_dict_list.append(food_dict)

    # When page initial loads, so it doesn't go into an infinite redirect
    if not request.method == 'POST':
        send_order = False
        order_date = str(date.today())
        order_dict_list = []
        order_foods = []
        order_prices = []
        return render_template('customer_order.html', food_dict_list=food_dict_list,
            food_truck = session['selected_food_truck'], error=error)

    # When a form is being submitted
    if request.method == 'POST':
        for i in range(len(food_dict_list)):
            food_name_input = str(
                request.form['purchase_quantity_input_{}'.format(i)])
            print(request.form['purchase_quantity_input_{}'.format(i)])
            if request.form.get('food_name_input_{}'.format(i)):
                if (food_name_input != ''):
                    try:
                        order_foods.append(food_dict_list[i]['food_name'])
                        order_prices.append(
                            int(food_name_input) * food_dict_list[i]['food_price'])
                        order_dict_list.append(
                            {'order_food': food_dict_list[i]['food_name'],
                            'order_quantity': int(food_name_input),
                            'order_food_truck': food_dict_list[i]['food_truck']})
                        send_order = True
                    except:
                        print('dbg: MUST HAVE INTEGER PURCHASE QUANTITIES | REDO ORDER')
                        flash('Quantities must be whole numbers. Please redo order.', 'alert-error')
                        return redirect(url_for('customer_order'))
                else:
                    # print('dbg2: CANNOT HAVE EMPTY INPUTS | REDO ORDER')
                    flash('Must purchase at least one item. Please redo order.', 'alert-error')
                    return redirect(url_for('customer_order'))
        if send_order is False:
            # print("dbg3: MUST BE CHECKED | REDO ORDER")
            flash('Items for purchase are not checked. Please redo order.', 'alert-error')
            return redirect(url_for('customer_order'))
        if send_order and len(order_dict_list) > 0:
            c.execute("SELECT balance FROM cs4400spring2020.Customer WHERE username='{cus_user}';".format(
                cus_user=session['username']))
            current_balance = c.fetchall()[0][0]
            if (current_balance < sum(order_prices)):
                flash("Balance is too low. Please refill balance.", 'alert-error')
                return redirect(url_for('customer_order'))
            order_insert_sql = "CALL cus_order('{o_date}', '{cus_order}');".format(
                o_date=order_date, cus_order=session['username'])
            c.execute(order_insert_sql)
            get_order_id_sql = "SELECT max(orderID) FROM cs4400spring2020.Orders WHERE customerUsername = '{cus_user}';".format(
                cus_user=session['username'])
            c.execute(get_order_id_sql)
            order_id = c.fetchone()[0]
            for i in range(len(order_dict_list)):
                print(order_dict_list[i])
                print(order_dict_list[i]['order_food'])
                print(order_dict_list[i]['order_quantity'])
                print(order_id)
                order_detail_insert_sql = "CALL cus_add_item_to_order('{ft}', '{f}', '{pq}', '{o_id}');".format(
                    ft=order_dict_list[i]['order_food_truck'], f=order_dict_list[i]['order_food'],
                    pq=order_dict_list[i]['order_quantity'], o_id=str(order_id))
                c.execute(order_detail_insert_sql)
            conn.commit()
            send_order = False
            flash("Order Successful!")
            print("dbg 11")
            return redirect(url_for('customer_order_history'))

    # NEEDS to be a redirect so it doesn't resubmit previous
    return redirect(url_for('customer_order'))


@app.route('/customer_order_history', methods=['GET'])
def customer_order_history():
    error = None

    cus_order_history_sql = "CALL cus_order_history('{}');".format(session['username'])
    c.execute(cus_order_history_sql)
    cus_order_history_table_sql = "SELECT * FROM cus_order_history_result;"
    c.execute(cus_order_history_table_sql)
    orhist_table = c.fetchall()
    orhist_dict_list = []
    for i in range(len(orhist_table)):
        orhist_dict = {'date': orhist_table[i][0], 'order_id': orhist_table[i][1],
            'order_total': orhist_table[i][2], 'food': orhist_table[i][3].replace(",", ", "),
            'food_quantity': orhist_table[i][4]}
        orhist_dict_list.append(orhist_dict)

    return render_template('/customer_order_history.html', orhist_dict_list=orhist_dict_list, error=error) 


# ===========================================
# MEMBER FUNCTIONS
# ===========================================


@app.route('/plans', methods=['GET'])
def plans():
    if not session.get('username'):
        return redirect(url_for('login'))

    sql = "SELECT * FROM drivingplan"
    c.execute(sql)
    rows = c.fetchall()
    return render_template('plans.html', rows=rows)


@app.route('/personal_info', methods=['GET', 'POST'])
def personal_info():

    if request.method == 'POST':

        for k, v in request.form.iteritems():
            if not v:
                flash('Please fill out everything completely!')
                return redirect(url_for('personal_info'))

        card_sql = ("INSERT INTO credit_card(CardNo, Name, CVV, ExpiryDate, BillingAdd) "
                    "VALUES ({cardno}, '{name}', {cvv}, '{exp_year}-{exp_mo}-01', '{billing}') ON DUPLICATE KEY UPDATE "
                    "Name='{name}', CVV={cvv}, ExpiryDate='{exp_year}-{exp_mo}-01', BillingAdd='{billing}'"
                    .format(cardno=request.form['cardno'],
                            name=request.form['name'],
                            cvv=request.form['cvv'],
                            exp_year=request.form['exp_year'],
                            exp_mo=request.form['exp_mo'],
                            billing=request.form['billingadd']))
        print(card_sql)

        user_sql = ("UPDATE member SET FirstName='{firstname}', LastName='{lastname}', MiddleInit='{middle}', "
                    "Address='{addr}', PhoneNo={phone}, EmailAddress='{email}', CardNo={cardno}, DrivingPlan='{drivingplan}' "
                    "WHERE username='{username}'".format(username=session['username'],
                                                         firstname=request.form['firstname'],
                                                         lastname=request.form['lastname'],
                                                         middle=request.form['middleinit'],
                                                         addr=request.form['address'],
                                                         phone=request.form['phone'],
                                                         email=request.form['email'],
                                                         cardno=request.form['cardno'],
                                                         drivingplan=request.form['plan']))

        try:
            c.execute(card_sql)
            c.execute(user_sql)
            # conn.commit()
        except pymysql.err.IntegrityError:
            flash("IntegrityError!", 'alert-error')

        flash('Updated!', 'alert-success')

    user_sql = "SELECT * FROM member WHERE username='{username}'".format(
        username=session['username'])

    r = c.execute(user_sql)
    if not r:
        flash('You are not a member', 'alert-error')
        return redirect(url_for('home'))

    user_row = c.fetchone()

    # Get driving plans available.
    plans_sql = "SELECT Type FROM drivingplan"
    c.execute(plans_sql)
    plans = c.fetchall()

    # Get card info, if exists
    card = ('', '', '', '')
    if user_row[7]:
        card_sql = "SELECT Name, CVV, ExpiryDate, BillingAdd FROM credit_card WHERE CardNo={cardno}".format(
            cardno=user_row[7])
        r = c.execute(card_sql)
        card = c.fetchone()

    if card[2]:
        year = card[2].year
        month = card[2].month
    else:
        year = ''
        month = ''

    return render_template('personal_info.html', user=user_row, plans=plans, card=card, year=year, month=month)


@app.route('/rent', methods=['GET', 'POST'])
def rent():
    if session['userType'] != 'member':
        return redirect(url_for('home'))

    locations = "SELECT LocationName FROM location"
    m = "SELECT Distinct CarModel FROM car GROUP BY CarModel"
    t = "SELECT Distinct Type FROM car GROUP BY Type"

    c.execute(locations)
    locations = c.fetchall()

    c.execute(m)
    models = c.fetchall()

    c.execute(t)
    types = c.fetchall()

    dates = [x.strftime("%Y-%m-%d")
             for x in daterange(date.today(), date.today() + timedelta(365))]

    return render_template('rent.html', locations=locations, models=models, types=types, dates=dates)


@app.route('/availability', methods=['GET', 'POST'])
def availability():

    # Selecting what you want
    if request.method == 'POST':

        vsn = request.form['car']
        pickdatetime = request.form['pickdatetime']
        returndatetime = request.form['returndatetime']
        sql = """INSERT INTO reservation(Username, PickUpDateTime, ReturnDateTime, ReturnStatus, EstimatedCost, ReservationLocation, VehicleSno)
                    VALUES ('{user}', '{pickup}', '{returnd}', 'out', {cost}, '{location}', {vsn})""".format(user=session.get('username'), pickup=pickdatetime, returnd=returndatetime,
                                                                                                             cost=request.form[vsn+'cost'], location=request.form[vsn+'location'], vsn=vsn)

        c.execute(sql)
        # conn.commit()

        flash("You have rented a car!")

        return redirect(url_for('home'))

    # Getting args

    pickdate = request.args.get('pickdate', '')
    pickhour = request.args.get('pickhour', '')
    pickmin = request.args.get('pickmin', '')
    pickdatetime = datetime(int(pickdate[0:4]), int(pickdate[5:7]), int(
        pickdate[8:10]), int(pickhour), int(pickmin))

    returndate = request.args.get('returndate', '')
    returnhour = request.args.get('returnhour', '')
    returnmin = request.args.get('returnmin', '')
    returndatetime = datetime(int(returndate[0:4]), int(returndate[5:7]), int(
        returndate[8:10]), int(returnhour), int(returnmin))

    location = request.args.get('location', '')
    model = request.args.get('model', '')
    car_type = request.args.get('types', '')

    delta = returndatetime - pickdatetime

    # making sure the date is less than two
    if delta.days > 2:
        flash("You cannot rent a car for more than two days")
        return redirect(url_for('rent'))

    # Setting the sql for the table
    if car_type:
        sql = """SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE  CarLocation='{l}' AND Type='{car_type}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ) desired_location
                    UNION ALL
                    SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE CarLocation != '{l}' AND Type='{car_type}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ORDER BY CarLocation) extra""".format(l=location, pickdatetime=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'), returndatetime=returndatetime.strftime('%Y-%m-%d %H:%M:%S'), car_type=car_type)

    elif model:
        sql = """SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE  CarLocation='{l}' AND CarModel = '{model}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ) desired_location
                    UNION ALL
                    SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE CarLocation != '{l}' AND CarModel = '{model}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ORDER BY CarLocation) extra""".format(l=location, pickdatetime=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'), returndatetime=returndatetime.strftime('%Y-%m-%d %H:%M:%S'), model=model)

    else:
        sql = """SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE  CarLocation='{l}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ) desired_location
                    UNION ALL
                    SELECT * FROM
                    (SELECT VehicleSno,CarModel,Type,CarLocation,Color,HourlyRate,DailyRate,Seating_Capacity,Transmission_Type,BluetoothConnectivity,Auxiliary_Cable
                        FROM car WHERE CarLocation != '{l}'
                        AND VehicleSno NOT IN (
                            SELECT VehicleSno FROM reservation
                            WHERE ('{pickdatetime}' > PickUpDateTime AND '{pickdatetime}' < ReturnDateTime)
                            OR ('{returndatetime}' > PickUpDateTime AND '{returndatetime}' < ReturnDateTime)
                        )
                    ORDER BY CarLocation) extra""".format(l=location, pickdatetime=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'), returndatetime=returndatetime.strftime('%Y-%m-%d %H:%M:%S'))
    print(sql)
    c.execute(sql)
    cars = c.fetchall()
    dic = {}
    vsnos = []
    for item in cars:
        vsnos.append(item[0])
        dic[item[0]] = "N/A"

    sql = "SELECT Distinct VehicleSno,PickUpDateTime FROM reservation where PickUpDateTime > '{pickdatetime}'".format(
        pickdatetime=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'))
    c.execute(sql)
    avail = c.fetchall()

    for x in vsnos:
        for y in avail:
            if str(x) == str(y[0]):
                dic[x] = y[1]
            else:
                if x in dic == False:
                    dic[x] = 'N/A'

    discount = None
    # Getting the user's plan info so I can make an estimate of the cost
    user = session.get('username')
    userType = session.get('userType')
    sql = "SELECT Discount FROM drivingplan JOIN member ON member.DrivingPlan = drivingplan.Type WHERE Username='{u}'".format(
        u=user)

    c.execute(sql)
    try:
        discount = c.fetchone()[0]
    except:
        if userType != 'emp':
            flash("You need to set up a plan!")
            return(redirect(url_for('home')))
        else:
            flash("Searching for available reservations")

    if discount:
        discount = (100.0 - discount)/100.0
    else:
        discount = 1
    print(vsnos)
    print(dic)

    return render_template('availability.html', location=location,
                           pickdatetime=pickdatetime.strftime(
                               '%Y-%m-%d %H:%M:%S'),
                           returndatetime=returndatetime.strftime(
                               '%Y-%m-%d %H:%M:%S'),
                           cars=cars, discount=discount, hours=delta.seconds/3600, days=delta.days,
                           dic=dic)


@app.route('/rental_info', methods=['GET', 'POST'])
def rental_info():
    if not session.get('userType') == 'member':
        return redirect(url_for('home'))

    dates = [x.strftime("%Y-%m-%d")
             for x in daterange(date.today(), date.today() + timedelta(365))]
    if request.method == 'POST':

        if not request.form.get('extend'):
            flash('You must select a reservation to modify')
            return redirect(url_for('rental_info'))

        extenddate = request.form['extenddate']
        extendhour = request.form['extendhour']
        extendmin = request.form['extendmin']
        resid = request.form['extend']

        extenddatetime = datetime(int(extenddate[0:4]), int(extenddate[5:7]), int(
            extenddate[8:10]), int(extendhour), int(extendmin))

        sql = """SELECT ReturnDateTime, VehicleSno FROM reservation WHERE ResID={resid}""".format(
            resid=resid)

        c.execute(sql)
        curr_res = c.fetchone()
        if curr_res[0] > extenddatetime:
            flash(
                'To extend you must choose a time past your current return time', 'alert-error')
            return redirect(url_for('rental_info'))

        vsn = curr_res[1]

        sql = """SELECT PickUpDateTime FROM reservation
                WHERE VehicleSno={vsn} AND PickUpDateTime < '{extend}'
                AND PickUpDateTime > '{orig_return}'""".format(vsn=vsn,
                                                               extend=extenddatetime.strftime(
                                                                   '%Y-%m-%d %H:%M:%S'),
                                                               orig_return=curr_res[0].strftime('%Y-%m-%d %H:%M:%S'))

        c.execute(sql)
        collision = c.fetchall()
        if collision:
            flash('Someone else has already reserved that car at {date}'.format(
                date=collision[0][0]), 'alert-error')
            return redirect(url_for('rental_info'))

        sql = """INSERT INTO reservation_extended_time
                VALUES ({resid}, '{extend}')""".format(resid=resid, extend=extenddatetime.strftime('%Y-%m-%d %H:%M:%S'))
        c.execute(sql)
        # conn.commit()

        flash('Reservation successfully extended!', 'alert-success')
        return redirect(url_for('rental_info'))

    user = session.get('username')
    sql = """SELECT PickUpDateTime,ReturnDateTime,CarModel,ReservationLocation,EstimatedCost, ReturnStatus, Extended_Time
            FROM reservation r1 NATURAL JOIN car LEFT JOIN reservation_extended_time r2 ON r2.ResID = r1.ResID
            WHERE Username='{u}'""".format(u=user)

    c.execute(sql)
    all_res = c.fetchall()

    sql = """SELECT r1.ResID, PickUpDateTime, ReturnDateTime, CarModel, ReservationLocation, EstimatedCost, ReturnStatus, Extended_Time
            FROM reservation r1 NATURAL JOIN car LEFT JOIN reservation_extended_time r2 ON r2.ResID = r1.ResID
            WHERE Username='{u}' AND PickUpDateTime < NOW() AND ReturnDateTime > NOW()""".format(u=user)

    print(sql)
    c.execute(sql)
    current = c.fetchall()

    return render_template('rental_info.html', current=current, all_res=all_res, dates=dates)


# ===========================================
# ADMIN FUNCTIONS
# ===========================================

@app.route('/admin/reports', methods=['GET'])
def admin_reports():
    if not session.get('userType') == 'admin':
        return redirect(url_for('home'))

    sql = """SELECT reservation.VehicleSno, Type, CarModel, SUM(EstimatedCost) , SUM(LateFees) FROM  `reservation` JOIN `car` ON reservation.VehicleSno = car.VehicleSno
            WHERE PickUpDateTime > DATE_SUB(NOW() ,INTERVAL 3 MONTH) AND PickUpDateTime < NOW()
            GROUP BY reservation.VehicleSno ORDER BY Type"""
    c.execute(sql)
    data = c.fetchall()

    return render_template('admin_report.html', data=data)


# ===========================================
# EMPLOYEE FUNCTIONS
# ===========================================

@app.route('/car_data', methods=['GET'])
def car_data():
    if not session.get('userType') == 'emp':
        abort(401)

    if request.args.get('location', ''):
        # location request, serve up cars in this location
        sql = """SELECT *,
                CAST(Transmission_Type AS unsigned integer) as trans,
                CAST(Auxiliary_Cable AS unsigned integer) as aux,
                CAST(BluetoothConnectivity AS unsigned integer) as blue,
                CAST(UnderMaintenanceFlag AS unsigned integer) as maint
                FROM car WHERE CarLocation = '{location}'""".format(location=request.args.get('location', ''))

    elif request.args.get('vsn', ''):
        # Specific request, serve up a car based on this request.
        sql = """SELECT *,
                CAST(Transmission_Type AS unsigned integer) as trans,
                CAST(Auxiliary_Cable AS unsigned integer) as aux,
                CAST(BluetoothConnectivity AS unsigned integer) as blue,
                CAST(UnderMaintenanceFlag AS unsigned integer) as maint
                FROM car WHERE VehicleSno = {vsn}""".format(vsn=request.args.get('vsn', ''))

    c.execute(sql)
    cars = c.fetchall()
    js = []
    for (vsn, aux_bit, trans_bit, cap, blue_bit, daily, hourly, color, cartype, model, maint_bit, loc, trans, aux, blue, maint) in cars:
        js.append({"vsn": vsn,
                   "aux": aux,
                   "trans": trans,
                   "cap": cap,
                   "blue": blue,
                   "daily": daily,
                   "hourly": hourly,
                   "color": color,
                   "type": cartype,
                   "model": model,
                   "maint": maint,
                   "location": loc})

    return Response(json.dumps(js),  mimetype='application/json')


@app.route('/manage_cars', methods=['GET', 'POST'])
def manage_cars():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    locations = "SELECT LocationName FROM location"
    c.execute(locations)
    locations = c.fetchall()

    t = "SELECT Distinct Type FROM car GROUP BY Type"
    c.execute(t)
    types = c.fetchall()

    models = "SELECT Distinct CarModel FROM car GROUP BY CarModel"
    c.execute(models)
    models = c.fetchall()

    if request.method == "POST":
        car_sql = ("INSERT INTO car(VehicleSno,Auxiliary_Cable,Transmission_Type,Seating_Capacity,BluetoothConnectivity,DailyRate,HourlyRate,Color,Type,CarModel,CarLocation) VALUES ({VehicleSno},{Auxiliary_Cable},{Transmission_Type},{Seating_Capacity},{BluetoothConnectivity},{DailyRate},{HourlyRate},'{Color}','{Type}','{CarModel}', '{CarLocation}')"
                   .format(VehicleSno=request.form['vsno'],
                           Auxiliary_Cable=request.form['aux'],
                           Transmission_Type=request.form['trans'],
                           Seating_Capacity=request.form['seat'],
                           BluetoothConnectivity=request.form['blue'],
                           DailyRate=request.form['daily'],
                           HourlyRate=request.form['hr'],
                           Color=request.form['color'],
                           Type=request.form['type'],
                           CarModel=request.form['model'],
                           CarLocation=request.form['location'],))

        try:
            c.execute(car_sql)
            # conn.commit()
            flash('Car Inserted!')
        except pymysql.err.IntegrityError:
            flash("IntegrityError!", 'alert-error')

        return render_template('manage_cars.html', locations=locations, types=types)

    return render_template('manage_cars.html', models=models, locations=locations, types=types)


@app.route('/update_car', methods=['GET', 'POST'])
def update_car():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['transType'] == 'Manual':
            trans = 1
        else:
            trans = 0

        car_sql = """UPDATE car SET CarLocation = '{l}', Type = '{t}', Color = '{c}', Seating_Capacity = {capacity},
                    Transmission_Type = ({trans}) WHERE VehicleSno = {vsn}""".format(t=request.form['carType'],
                                                                                     c=request.form['color'],
                                                                                     capacity=request.form['seatCap'],
                                                                                     trans=trans,
                                                                                     l=request.form['newLocation'],
                                                                                     vsn=request.form['vsn'])
        c.execute(car_sql)
        # conn.commit()
        flash('Car updated!')

    return redirect(url_for('manage_cars'))


@app.route('/maint_request', methods=['GET', 'POST'])
def maint_request():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    locations = "SELECT LocationName FROM location"
    c.execute(locations)
    locations = c.fetchall()

    if request.method == 'POST':
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        maint_req = """INSERT INTO maintenance_request
                        VALUES ({vsn}, '{now}', '{user}')""".format(vsn=request.form['vsn'], now=now, user=session.get('username'))

        c.execute(maint_req)

        maint_prob = """INSERT INTO maintenance_request_problems
                        VALUES ({vsn}, '{now}', '{prob}')""".format(vsn=request.form['vsn'], now=now, user=session.get('username'), prob=request.form['problems'])
        c.execute(maint_prob)

        update_flag = """UPDATE car SET UnderMaintenanceFlag=(1) WHERE VehicleSno={vsn}""".format(
            vsn=request.form['vsn'])
        c.execute(update_flag)

        # conn.commit()
        flash('Your report has been submitted', 'alert-success')

    return render_template('maint_request.html', locations=locations)


@app.route('/rental_change', methods=['GET', 'POST'])
def rental_change():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    dates = [x.strftime("%Y-%m-%d")
             for x in daterange(date.today(), date.today() + timedelta(365))]

    if request.method == 'POST':
        pickdate = request.form['pickdate']
        pickhour = request.form['pickhour']
        pickmin = request.form['pickmin']

        currdate = request.form['currdate']
        currhour = request.form['currhour']
        currmin = request.form['currmin']

        resid = request.form['resid']

        pickdatetime = datetime(int(pickdate[0:4]), int(pickdate[5:7]), int(
            pickdate[8:10]), int(pickhour), int(pickmin))
        currdatetime = datetime(int(currdate[0:4]), int(currdate[5:7]), int(
            currdate[8:10]), int(currhour), int(currmin))
        late_by = pickdatetime - currdatetime
        late_by = late_by.seconds/3600

        if pickdatetime < currdatetime:
            flash('You must pick a time after the current one', 'alert-error')
            return redirect(url_for('rental_change'))

        sql = """INSERT INTO reservation_extended_time
                VALUES ({resid}, '{extended}')""".format(resid=resid, extended=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'))

        c.execute(sql)
        # conn.commit()

        sql = """SELECT Username, PickUpDateTime, ReturnDateTime, EmailAddress, PhoneNo, ResID, ReservationLocation FROM reservation
                NATURAL JOIN member
                WHERE PickUpDateTime < '{overlap}'
                AND PickUpDateTime > '{curr}'""".format(overlap=pickdatetime.strftime('%Y-%m-%d %H:%M:%S'),
                                                        curr=currdatetime.strftime('%Y-%m-%d %H:%M:%S'))

        overlap = None
        c.execute(sql)
        overlap = c.fetchone()
        if overlap:
            sql = """UPDATE reservation SET LateFees={latefee} WHERE ResID={resid}""".format(
                latefee=50*late_by, resid=resid)
            c.execute(sql)
            # conn.commit()

            flash(
                'The new time has overlapped with an existing reservation, please amend')

        flash('The user reservation has been extended', 'alert-success')
        return render_template('rental_change.html', dates=dates, overlap=overlap)

    if request.args.get('username', ''):
        rental_info = """SELECT car.CarModel , car.CarLocation, reservation.ReturnDateTime, reservation.resID FROM car
                        INNER JOIN reservation ON reservation.VehicleSno = car.VehicleSno
                        WHERE reservation.Username = '{user}' AND reservation.PickUpDateTime<now()
                        AND reservation.ReturnDateTime>now()""".format(user=request.args.get('username', ''))
        # rental_info selects the data needed to auto populate the text boxes
        c.execute(rental_info)
        current = c.fetchone()

        if current:
            model, location, retdate, resid = current
            curr_date = retdate.strftime("%Y-%m-%d")
            curr_hour = retdate.hour
            curr_min = retdate.minute
        else:
            flash('No current reservation for user: {user}'.format(
                user=request.args.get('username', '')))
            curr_date = ''
            curr_hour = ''
            curr_min = ''

        return render_template('rental_change.html', resid=resid, dates=dates, model=model, curr_date=curr_date, curr_hour=curr_hour, curr_min=curr_min, username=request.args.get('username', ''))

    return render_template('rental_change.html', dates=dates)


@app.route('/delete_rental', methods=['POST'])
def del_rental():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    resid = request.form['overlapid']

    sql = """DELETE FROM reservation WHERE ResID = {resid}""".format(
        resid=resid)
    print(sql)
    c.execute(sql)
    # conn.commit()

    flash('The users conflicting reservation has been deleted', 'alert-success')

    return redirect(url_for('rental_change'))


@app.route('/loc_prefs', methods=['GET'])
def loc_prefs():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    sql = """SELECT mon_name, ReservationLocation, ResCount, total_hours
            FROM (
                SELECT COUNT( ResID ) AS ResCount, SUM( TIMESTAMPDIFF( HOUR , PickUpDateTime, ReturnDateTime ) ) AS total_hours, MONTHNAME( PickUpDateTime ) AS mon_name, ReservationLocation
                    FROM reservation
                    WHERE PickUpDateTime > DATE_SUB( NOW( ) , INTERVAL 3
                    MONTH )
                    AND PickUpDateTime < NOW( )
                    GROUP BY YEAR( PickUpDateTime ) , MONTH( PickUpDateTime ) , ReservationLocation
                ) AS thing1
            WHERE (
                thing1.mon_name, thing1.ResCount
            )
            IN (
                SELECT mon_name, MAX( ResCount )
                FROM (

                SELECT COUNT( ResID ) AS ResCount, SUM( TIMESTAMPDIFF( HOUR , PickUpDateTime, ReturnDateTime ) ) AS total_hours, MONTHNAME( PickUpDateTime ) AS mon_name, ReservationLocation
                    FROM reservation
                    WHERE PickUpDateTime > DATE_SUB( NOW( ) , INTERVAL 3
                    MONTH )
                    AND PickUpDateTime < NOW( )
                    GROUP BY YEAR( PickUpDateTime ) , MONTH( PickUpDateTime ) , ReservationLocation
                    ) AS thing
                GROUP BY mon_name
            )"""

    c.execute(sql)

    return render_template('loc_prefs.html', data=c.fetchall())


@app.route('/freq_users', methods=['GET'])
def freq_users():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    # SQL to grab all the stuff
    sql = ("SELECT username, COUNT(*) FROM (user NATURAL JOIN reservation) GROUP BY username ORDER BY COUNT(*) DESC")
    c.execute(sql)
    tupe = c.fetchall()
    data = list(tupe)

    # If the list of data is more than five, it shortens it down to only the top five
    # You can use the databse LIMIT param
    try:
        data = data[0:4]
    except:
        pass
    # This part adds in the member's plan
    for x in range(len(data)):
        data[x] = list(data[x])
        sql = "SELECT DrivingPlan FROM member where username ='{u}'".format(
            u=data[x][0])
        c.execute(sql)
        tupe = c.fetchall()
        plan = tupe[0][0]
        data[x].insert(1, plan)

    return render_template('freq_users.html', data=data)


@app.route('/maint_history', methods=['GET'])
def maint_history():
    if not session.get('userType') == 'emp':
        return redirect(url_for('home'))

    sql = """SELECT CarModel,RequestDateTime,Username,Problem FROM (Select VehicleSno, CarModel, RequestDateTime, Username,Problem
            FROM car NATURAL JOIN maintenance_request
            NATURAL JOIN maintenance_request_problems) as T Natural Join
            (SELECT VehicleSno, count(*) AS total FROM maintenance_request GROUP BY VehicleSno ORDER BY total ASC) as J
            ORDER BY total Desc"""

    c.execute(sql)
    data = list(c.fetchall())
    print(data)

    return render_template('maint_history.html', data=data)


if __name__ == "__main__":
    app.secret_key = 'sekret'
    app.run(debug=True)
