# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
import random
import re
import secrets
import string
from config import config

app = Flask(__name__)

# Load configuration
app.config.from_object(config['development'])  # Change to 'production' for production

mysql = MySQL(app)

# Helper Functions
def generate_account_id():
    """Generate unique 10-digit account number"""
    cursor = mysql.connection.cursor()
    while True:
        account_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (account_id,))
        if not cursor.fetchone():
            cursor.close()
            return account_id
        cursor.close()

def generate_security_pin():
    """Generate a secure 6-digit PIN"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def validate_mobile(mobile):
    """Validate mobile number (10 digits)"""
    return re.match(r'^\d{10}$', mobile)

def validate_email(email):
    """Validate email format"""
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

def validate_pin(pin):
    """Validate that PIN is exactly 6 digits"""
    return re.match(r'^\d{6}$', pin) is not None

def check_mobile_exists(mobile):
    """Check if mobile number already exists"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT account_id FROM accounts WHERE mobile_number = %s", (mobile,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists

def check_email_exists(email):
    """Check if email already exists"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT account_id FROM accounts WHERE email = %s", (email,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists

def get_account_details(account_id):
    """Get account details by account ID"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_id = %s", (account_id,))
    account = cursor.fetchone()
    cursor.close()
    return account

def login_required(f):
    """Decorator to require login for certain routes"""
    def decorated_function(*args, **kwargs):
        if 'account_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # Get form data
        name = request.form['name'].upper().strip()
        gender = request.form['gender']
        mobile = request.form['mobile'].strip()
        email = request.form['email'].strip().lower()
        initial_deposit = float(request.form.get('initial_deposit', 0))
        
        # Validation
        errors = []
        
        if not name or len(name) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        if gender not in ['MALE', 'FEMALE', 'OTHER']:
            errors.append("Please select valid gender")
        
        if not validate_mobile(mobile):
            errors.append("Invalid mobile number (must be 10 digits)")
        elif check_mobile_exists(mobile):
            errors.append("Mobile number already registered")
        
        if not validate_email(email):
            errors.append("Invalid email format")
        elif check_email_exists(email):
            errors.append("Email already registered")
        
        if initial_deposit < 0:
            errors.append("Initial deposit cannot be negative")
        
        if errors:
            return render_template('create_account.html', errors=errors, form_data=request.form)
        
        # Generate account ID and security PIN
        account_id = generate_account_id()
        security_pin = generate_security_pin()
        
        # Insert into database
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO accounts 
                (account_id, name, gender, available_balance, mobile_number, email, security_pin, last_transaction_datetime, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_id, name, gender, initial_deposit, mobile, email, security_pin,
                  datetime.now() if initial_deposit > 0 else None, 'ACTIVE'))
            
            mysql.connection.commit()
            
            # Store in session
            session.permanent = True
            session['account_id'] = account_id
            session['name'] = name
            session['security_pin'] = security_pin
            session['pin_verified'] = True
            session['show_pin'] = True
            
            flash(f"✅ Account created successfully!", 'success')
            
            return redirect(url_for('account_credentials'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error creating account: {str(e)}", 'error')
            return render_template('create_account.html', form_data=request.form)
        finally:
            cursor.close()
    
    return render_template('create_account.html')

@app.route('/account-credentials')
@login_required
def account_credentials():
    """Display account credentials including PIN (shown only once)"""
    if not session.get('show_pin', False):
        return redirect(url_for('dashboard'))
    
    account = get_account_details(session['account_id'])
    security_pin = session.get('security_pin', '')
    
    session['show_pin'] = False
    session.pop('security_pin', None)
    
    return render_template('account_credentials.html', account=account, security_pin=security_pin)

@app.route('/dashboard')
@login_required
def dashboard():
    account = get_account_details(session['account_id'])
    
    if not account or account['status'] != 'ACTIVE':
        session.clear()
        flash('Account not found or inactive', 'error')
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', account=account)

@app.route('/balance-inquiry')
@login_required
def balance_inquiry():
    account = get_account_details(session['account_id'])
    return render_template('balance_inquiry.html', account=account)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash("Amount must be greater than 0", 'error')
            return redirect(url_for('deposit'))
        
        if amount < app.config['MIN_DEPOSIT_AMOUNT']:
            flash(f"Minimum deposit amount is ₹{app.config['MIN_DEPOSIT_AMOUNT']}", 'error')
            return redirect(url_for('deposit'))
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE accounts 
                SET available_balance = available_balance + %s,
                    last_transaction_datetime = %s
                WHERE account_id = %s AND status = 'ACTIVE'
            """, (amount, datetime.now(), session['account_id']))
            
            if cursor.rowcount == 0:
                flash("Account not found or inactive", 'error')
                return redirect(url_for('deposit'))
            
            mysql.connection.commit()
            
            cursor.execute("SELECT available_balance FROM accounts WHERE account_id = %s", (session['account_id'],))
            new_balance = cursor.fetchone()['available_balance']
            
            flash(f"₹{amount:,.2f} deposited successfully! New balance: ₹{new_balance:,.2f}", 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error processing deposit: {str(e)}", 'error')
        finally:
            cursor.close()
        
        return redirect(url_for('balance_inquiry'))
    
    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        
        if amount <= 0:
            flash("Amount must be greater than 0", 'error')
            return redirect(url_for('withdraw'))
        
        if amount > app.config['MAX_WITHDRAWAL_PER_TRANSACTION']:
            flash(f"Maximum withdrawal per transaction is ₹{app.config['MAX_WITHDRAWAL_PER_TRANSACTION']:,.2f}", 'error')
            return redirect(url_for('withdraw'))
        
        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute("SELECT available_balance FROM accounts WHERE account_id = %s AND status = 'ACTIVE'", 
                          (session['account_id'],))
            account = cursor.fetchone()
            
            if not account:
                flash("Account not found or inactive", 'error')
                return redirect(url_for('withdraw'))
            
            if account['available_balance'] < amount:
                flash(f"Insufficient balance. Available: ₹{account['available_balance']:,.2f}", 'error')
                return redirect(url_for('withdraw'))
            
            cursor.execute("""
                UPDATE accounts 
                SET available_balance = available_balance - %s,
                    last_transaction_datetime = %s
                WHERE account_id = %s
            """, (amount, datetime.now(), session['account_id']))
            
            mysql.connection.commit()
            
            cursor.execute("SELECT available_balance FROM accounts WHERE account_id = %s", (session['account_id'],))
            new_balance = cursor.fetchone()['available_balance']
            
            flash(f"₹{amount:,.2f} withdrawn successfully! New balance: ₹{new_balance:,.2f}", 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error processing withdrawal: {str(e)}", 'error')
        finally:
            cursor.close()
        
        return redirect(url_for('balance_inquiry'))
    
    return render_template('withdraw.html')

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        to_account = request.form['to_account'].strip()
        amount = float(request.form['amount'])
        remarks = request.form.get('remarks', '')
        
        if amount <= 0:
            flash("Amount must be greater than 0", 'error')
            return redirect(url_for('transfer'))
        
        if amount > app.config['MAX_TRANSFER_PER_TRANSACTION']:
            flash(f"Maximum transfer per transaction is ₹{app.config['MAX_TRANSFER_PER_TRANSACTION']:,.2f}", 'error')
            return redirect(url_for('transfer'))
        
        if to_account == session['account_id']:
            flash("Cannot transfer to your own account", 'error')
            return redirect(url_for('transfer'))
        
        if not re.match(r'^\d{10}$', to_account):
            flash("Invalid beneficiary account number (must be 10 digits)", 'error')
            return redirect(url_for('transfer'))
        
        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute("START TRANSACTION")
            
            cursor.execute("SELECT available_balance, status FROM accounts WHERE account_id = %s", 
                          (session['account_id'],))
            sender = cursor.fetchone()
            
            if not sender or sender['status'] != 'ACTIVE':
                flash("Your account is not active", 'error')
                return redirect(url_for('transfer'))
            
            if sender['available_balance'] < amount:
                flash(f"Insufficient balance. Available: ₹{sender['available_balance']:,.2f}", 'error')
                return redirect(url_for('transfer'))
            
            cursor.execute("SELECT status FROM accounts WHERE account_id = %s", (to_account,))
            dest_account = cursor.fetchone()
            
            if not dest_account:
                flash("Destination account not found", 'error')
                return redirect(url_for('transfer'))
            
            if dest_account['status'] != 'ACTIVE':
                flash("Destination account is not active", 'error')
                return redirect(url_for('transfer'))
            
            cursor.execute("""
                UPDATE accounts 
                SET available_balance = available_balance - %s,
                    last_transaction_datetime = %s
                WHERE account_id = %s
            """, (amount, datetime.now(), session['account_id']))
            
            cursor.execute("""
                UPDATE accounts 
                SET available_balance = available_balance + %s,
                    last_transaction_datetime = %s
                WHERE account_id = %s
            """, (amount, datetime.now(), to_account))
            
            mysql.connection.commit()
            
            flash(f"₹{amount:,.2f} transferred successfully to account {to_account}!", 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error processing transfer: {str(e)}", 'error')
        finally:
            cursor.close()
        
        return redirect(url_for('balance_inquiry'))
    
    return render_template('transfer.html')

@app.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        confirmation = request.form.get('confirmation', '')
        reason = request.form.get('reason', '')
        
        if confirmation != 'DELETE':
            flash("Please type DELETE to confirm", 'error')
            return redirect(url_for('delete_account'))
        
        cursor = mysql.connection.cursor()
        
        try:
            # Check balance
            cursor.execute("SELECT available_balance, name, mobile_number, email FROM accounts WHERE account_id = %s", 
                          (session['account_id'],))
            account = cursor.fetchone()
            
            if not account:
                flash("Account not found", 'error')
                return redirect(url_for('delete_account'))
            
            if account['available_balance'] > 0:
                flash("Cannot delete account with positive balance. Please withdraw all funds first.", 'error')
                return redirect(url_for('delete_account'))
            
            # Log the deletion for audit purposes (optional)
            app.logger.info(f"Account DELETED - ID: {session['account_id']}, Name: {account['name']}, Mobile: {account['mobile_number']}, Reason: {reason}")
            
            # HARD DELETE - Permanently remove from database
            cursor.execute("DELETE FROM accounts WHERE account_id = %s", (session['account_id'],))
            
            mysql.connection.commit()
            
            # Clear session
            session.clear()
            flash("✅ Your account has been permanently deleted from our system", 'success')
            flash("Thank you for banking with us. We're sorry to see you go!", 'info')
            return redirect(url_for('index'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error deleting account: {str(e)}", 'error')
            app.logger.error(f"Deletion error for account {session['account_id']}: {str(e)}")
        finally:
            cursor.close()
    
    return render_template('delete_account.html')

@app.route('/verify-contact', methods=['GET', 'POST'])
@login_required
def verify_contact():
    return render_template('verify_contact.html')

@app.route('/transaction-history')
@login_required
def transaction_history():
    account = get_account_details(session['account_id'])
    return render_template('transaction_history.html', account=account)

@app.route('/change-pin', methods=['GET', 'POST'])
@login_required
def change_pin():
    if request.method == 'POST':
        current_pin = request.form['current_pin'].strip()
        new_pin = request.form['new_pin'].strip()
        confirm_pin = request.form['confirm_pin'].strip()
        
        if not validate_pin(current_pin) or not validate_pin(new_pin):
            flash("PIN must be 6 digits", 'error')
            return redirect(url_for('change_pin'))
        
        if new_pin != confirm_pin:
            flash("New PIN and confirm PIN do not match", 'error')
            return redirect(url_for('change_pin'))
        
        weak_pins = ['123456', '111111', '000000', '123123', '654321']
        if new_pin in weak_pins:
            flash("Please choose a stronger PIN. Avoid sequential or repeated numbers.", 'error')
            return redirect(url_for('change_pin'))
        
        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT account_id FROM accounts 
                WHERE account_id = %s AND security_pin = %s AND status = 'ACTIVE'
            """, (session['account_id'], current_pin))
            
            if not cursor.fetchone():
                flash("Current PIN is incorrect", 'error')
                return redirect(url_for('change_pin'))
            
            if current_pin == new_pin:
                flash("New PIN must be different from current PIN", 'error')
                return redirect(url_for('change_pin'))
            
            cursor.execute("""
                UPDATE accounts 
                SET security_pin = %s
                WHERE account_id = %s
            """, (new_pin, session['account_id']))
            
            mysql.connection.commit()
            flash("✅ PIN changed successfully! Use your new PIN for next login.", 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error changing PIN: {str(e)}", 'error')
        finally:
            cursor.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('change_pin.html')

# API Routes for AJAX calls
@app.route('/check-mobile', methods=['POST'])
def check_mobile():
    data = request.get_json()
    mobile = data.get('mobile')
    exists = check_mobile_exists(mobile)
    return jsonify({'exists': exists})

@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    exists = check_email_exists(email)
    return jsonify({'exists': exists})

@app.route('/login', methods=['POST'])
def login():
    account_id = request.form['account_id'].strip()
    security_pin = request.form['security_pin'].strip()
    
    if not re.match(r'^\d{10}$', account_id):
        flash("Invalid account number format", 'error')
        return redirect(url_for('index'))
    
    if not re.match(r'^\d{6}$', security_pin):
        flash("Invalid PIN format (must be 6 digits)", 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE account_id = %s 
        AND security_pin = %s 
        AND status = 'ACTIVE'
    """, (account_id, security_pin))
    
    account = cursor.fetchone()
    cursor.close()
    
    if account:
        session.permanent = True
        session['account_id'] = account['account_id']
        session['name'] = account['name']
        session['pin_verified'] = True
        session['show_pin'] = False
        
        flash(f"✅ Welcome back, {account['name']}!", 'success')
        flash("🔒 Remember: Never share your PIN with anyone", 'warning')
        return redirect(url_for('dashboard'))
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s", (account_id,))
        account_exists = cursor.fetchone()
        cursor.close()
        
        if account_exists:
            flash("❌ Invalid Security PIN. Please try again.", 'error')
            app.logger.warning(f"Failed login attempt for account: {account_id}")
        else:
            flash("❌ Account not found or inactive", 'error')
        
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", 'success')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)