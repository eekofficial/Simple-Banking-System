import random
import sqlite3

DATABASE_NAME = 'card.s3db'

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS card (
    id INTEGER PRIMARY KEY,
    number TEXT,
    pin TEXT,
    balance INTEGER DEFAULT 0
    );
"""

CREATE_CARD_SQL = """
INSERT INTO card(id, number, pin)
    VALUES(null,?,?);
"""

SELECT_PIN_BY_NUMBER_SQL = """
SELECT pin FROM card WHERE number=(?);
"""

UPDATE_BALANCE_SQL = """
UPDATE card SET balance = balance + (?) WHERE number = (?);
"""

SELECT_BALANCE = """
SELECT balance FROM card WHERE number=(?);
"""

SELECT_NUMBER_SQL = """
SELECT number FROM card WHERE number=(?);
"""

DELETE_NUMBER_SQL = """
DELETE FROM card WHERE number=(?);
"""

class States:
    MAIN_MENU = True
    ENTER_NUMBER = False
    ENTER_PIN = False
    ACCOUNT_MENU = False
    ENTER_INCOME = False
    ENTER_NUMBER_FOR_TRANSFER = False
    ENTER_MONEY_FOR_TRANSFER = False

class BankSystem:
    entered_number = ''
    entered_pin = ''
    number_for_transfer = ''
    def __init__(self, db_name):
        self.conn = self.create_connection(db_name)
        self.create_table(self.conn)

    def __del__(self):
        self.close_connection(self.conn)

    def process_input(self, input_string):
        if input_string == '0':
            self.print_bye_message()
            return False

        if States.MAIN_MENU:
            if input_string == '1':
                card_number, pin = self.issue_card()
                self.print_cards_data(card_number, pin)
            elif input_string == '2':
                States.MAIN_MENU = False
                States.ENTER_NUMBER = True
        elif States.ENTER_NUMBER:
            self.entered_number = input_string
            States.ENTER_NUMBER = False
            States.ENTER_PIN = True
        elif States.ENTER_PIN:
            self.entered_pin = input_string
            if self.validate_data(self.entered_number, self.entered_pin):
                self.print_success_message()
                States.ACCOUNT_MENU = True
            else:
                self.print_wrong_message()
                States.MAIN_MENU = True
            States.ENTER_PIN = False
        elif States.ACCOUNT_MENU:
            if input_string == '1':
                self.print_balance(self.entered_number)
            elif input_string == '2':
                States.ACCOUNT_MENU = False
                States.ENTER_INCOME = True
            elif input_string == '3':
                States.ACCOUNT_MENU = False
                States.ENTER_NUMBER_FOR_TRANSFER = True
            elif input_string == '4':
                self.delete_number(self.conn, self.entered_number)
                self.print_delete()
            elif input_string == '5':
                self.print_logout_message()
                States.ACCOUNT_MENU = False
                States.MAIN_MENU = True
        elif States.ENTER_INCOME:
            self.update_balance(self.conn, self.entered_number, input_string)
            self.print_income_added_message()
            States.ENTER_INCOME = False
            States.ACCOUNT_MENU = True
        elif States.ENTER_NUMBER_FOR_TRANSFER:
            States.ENTER_NUMBER_FOR_TRANSFER = False
            States.ACCOUNT_MENU = True
            self.number_for_transfer = input_string
            if input_string == self.entered_number:
                self.print_transfering_yourself_error()
            elif not self.check_by_luhn_algorithm(input_string):
                self.print_luhn_error()
            elif not self.exist_card_number(self.conn, input_string):
                self.print_card_not_exist()
            else:
                States.ENTER_MONEY_FOR_TRANSFER = True
                States.ACCOUNT_MENU = False
        elif States.ENTER_MONEY_FOR_TRANSFER:
            if self.enough_money(input_string):
                self.update_balance(self.conn, self.number_for_transfer, input_string)
                self.update_balance(self.conn, self.entered_number, '-' + input_string)
                self.print_success()
            else:
                self.print_not_enough_money()
            States.ENTER_MONEY_FOR_TRANSFER = False
            States.ACCOUNT_MENU = True

        return True

    def print_delete(self):
        print('The account has been closed!')

    def print_not_enough_money(self):
        print('Not enough money!')

    def print_success(self):
        print('Success!')

    def enough_money(self, money_for_tranfer):
        balance = int(self.select_balance(self.conn, self.entered_number))
        print(balance)
        print(money_for_tranfer)
        if balance - int(money_for_tranfer) >= 0:
            return True
        return False

    def print_card_not_exist(self):
        print('Such a card does not exist')

    def print_luhn_error(self):
        print('Probably you made mistake in card number. Please try again!')

    def print_transfering_yourself_error(self):
        print("You can't transfer money to the same account!")

    def print_income_added_message(self):
        print('Income was added!')

    def print_bye_message(self):
        print('Bye!')

    def print_logout_message(self):
        print('You have successfully logged out!')

    def print_balance(self, card_number):
        balance = self.select_balance(self.conn, card_number)
        print('Balance: {}'.format(self.balance))

    def validate_data(self, card_number, pin):
        pin_rows = self.select_pin_by_number(self.conn, card_number)
        if len(pin_rows) > 0 and pin_rows[0][0] == pin:
            return True
        return False

    def print_success_message(self):
        print('You have successfully logged in!')

    def print_wrong_message(self):
        print('Wrong card number or PIN!')

    def issue_card(self):
        card_number, pin = self.generate_number(), self.generate_pin()
        self.create_card(self.conn, (card_number, pin))
        return card_number, pin

    def print_cards_data(self, card_number, pin):
        print('Your card has been created')
        print('Your card number:')
        print(card_number)
        print('Your card PIN:')
        print(pin)

    def generate_can(self):
        can = ''
        for _ in range(9):
            digit = random.randint(0, 9)
            can += str(digit)
        return can

    def generate_number(self):
        iin = '400000'
        can = self.generate_can()
        card_number = iin + can
        check_sum = self.find_check_sum(card_number)
        card_number += check_sum
        return card_number

    def find_check_sum(self, card_number):
        current_sum = self.luhn_algorithm(card_number)
        check_sum = 0
        while current_sum % 10 != 0:
            current_sum += 1
            check_sum += 1
        return str(check_sum)

    def luhn_algorithm(self, card_number):
        card_number_list = [int(digit) for digit in card_number]
        for i in range(len(card_number_list)):
            if i % 2 == 0:
                card_number_list[i] *= 2
                if card_number_list[i] > 9:
                    card_number_list[i] -= 9
        return sum(card_number_list)

    def check_by_luhn_algorithm(self, card_number):
        luhn_res = self.luhn_algorithm(card_number)
        if luhn_res % 10 == 0:
            return True
        return False

    def generate_pin(self):
        pin = ''
        for _ in range(4):
            digit = random.randint(0, 9)
            pin += str(digit)
        return pin

    def print_main_menu(self):
        print('1. Create an account')
        print('2. Log into account')
        print('0. Exit')

    def print_enter_number(self):
        print('Enter your card number:')

    def print_enter_pin(self):
        print('Enter your PIN:')

    def print_account_menu(self):
        print('1. Balance')
        print('2. Add income')
        print('3. Do transfer')
        print('4. Close account')
        print('5. Log out')
        print('0. Exit')

    def create_connection(self, db_file):
        return sqlite3.connect(db_file)

    def close_connection(self, connection_obj):
        connection_obj.close()

    def create_table(self, connection_obj):
        c = connection_obj.cursor()
        c.execute(CREATE_TABLE_SQL)
        connection_obj.commit()

    def create_card(self, connection_obj, card_info):
        c = connection_obj.cursor()
        c.execute(CREATE_CARD_SQL, card_info)
        connection_obj.commit()

    def select_pin_by_number(self, connection_obj, number):
        c = connection_obj.cursor()
        c.execute(SELECT_PIN_BY_NUMBER_SQL, (number,))
        rows = c.fetchall()
        return rows

    def update_balance(self, connection_obj, card_number, amount):
        c = connection_obj.cursor()
        c.execute(UPDATE_BALANCE_SQL, (amount, card_number))
        connection_obj.commit()

    def select_balance(self, connection_obj, card_number):
        c = connection_obj.cursor()
        c.execute(SELECT_BALANCE, (card_number,))
        rows = c.fetchall()
        return rows[0][0]

    def exist_card_number(self, connection_obj, card_number):
        c = connection_obj.cursor()
        c.execute(SELECT_NUMBER_SQL, (card_number,))
        rows = c.fetchall()
        if len(rows) > 0:
            return True
        return False

    def delete_number(self, connection_obj, card_number):
        c = connection_obj.cursor()
        c.execute(DELETE_NUMBER_SQL, (card_number,))
        connection_obj.commit()

    def print_enter_income(self):
        print('Enter income:')

    def print_enter_number_for_transfer(self):
        print('Transfer')
        print('Enter card number:')

    def print_enter_money_for_transfer(self):
        print('Enter how much money you want to transfer:')


def main():
    bank_system = BankSystem(DATABASE_NAME)
    response = True
    while response:
        if States.MAIN_MENU:
            bank_system.print_main_menu()
        elif States.ENTER_NUMBER:
            bank_system.print_enter_number()
        elif States.ENTER_PIN:
            bank_system.print_enter_pin()
        elif States.ACCOUNT_MENU:
            bank_system.print_account_menu()
        elif States.ENTER_INCOME:
            bank_system.print_enter_income()
        elif States.ENTER_NUMBER_FOR_TRANSFER:
            bank_system.print_enter_number_for_transfer()
        elif States.ENTER_MONEY_FOR_TRANSFER:
            bank_system.print_enter_money_for_transfer()
        response = bank_system.process_input(input())
main()

