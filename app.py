import requests
from bs4 import BeautifulSoup as bS
from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo

users = {'admin': {'password': 'admin', 'email': 'admin@flasktest.ru'}}  # "База" пользователей
all_exchanges = {}  # Словарь для хранения выгруженных курсов валют
choices = []  # Список для заполнения SelectField

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret_key"


def show_currency(input_str: str):
    """Возвращает строку с курсом по переданному коду валюты"""
    currency = all_exchanges[input_str]
    return f"{currency['count']} {currency['long_name']}: {currency['rate']} руб."


def find_all_currencys():
    """Парсинг сайта ЦБР и сохранение всех курсов валют в словарь"""
    link = "https://cbr.ru/currency_base/daily/"
    with requests.get(link, stream=True) as res:
        soup = bS(res.text, "html.parser")
        table = soup.find_all('tr')
        for tr in table[1:]:
            n, short_name, count, *long_name, rate = tr.text.split()
            all_exchanges[short_name] = dict([('count', count), ('long_name', ' '.join(long_name)), ('rate', rate)])


@app.route('/', methods=['GET', 'POST'])
def index_page():
    form = LoginForm()
    if form.validate_on_submit():
        login = form.login.data
        password = form.password.data
        if login not in users or users[login]['password'] != password:
            # При отсутствии пользователя в базе или несовпадении пароля
            flash("Неправильный логин или пароль", category="alert-danger")
            return render_template('index.html', form=form)
        # Успешная авторизация, парсинг курсов валют
        flash(f"Добро пожаловать, {login}!", category='alert-success')
        global choices
        find_all_currencys()
        choices = [(curr, all_exchanges[curr]['long_name']) for curr in all_exchanges]
        return redirect('/main_page/empty')
    return render_template('index.html', form=form)


@app.route('/main_page/<path:curr>', methods=['GET', 'POST'])
def main_page(curr):
    message = ""
    if curr != 'empty':
        if curr in all_exchanges:
            message = show_currency(curr)
        else:
            message = "Не найдена указанная валюта."
    form = CurrencyForm()
    form.curr.choices = choices
    if form.validate_on_submit():
        return redirect('/main_page/' + form.curr.data)
    return render_template('main_page.html', form=form, currency=message)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        login = form.login.data
        password = form.password.data
        email = form.e_mail.data
        if login in users:
            flash("Этот логин уже занят", category="alert-danger")
        else:
            users[login] = dict([('password', password), ('email', email)])
            flash("Регистрация успешна", category="alert-success")
            return redirect(url_for('index_page'))
    return render_template('register.html', form=form)


class LoginForm(FlaskForm):
    login = StringField("Логин: ", validators=[DataRequired()])
    password = PasswordField("Пароль: ", validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    login = StringField("Логин: ", validators=[DataRequired()])
    e_mail = EmailField("E-mail: ", validators=[DataRequired(), Email()])
    password = PasswordField('Пароль: ', [DataRequired(), EqualTo('confirm', message='Пароли не совпадают')])
    confirm = PasswordField('Повторите пароль: ')
    submit = SubmitField('Регистрация')


class CurrencyForm(FlaskForm):
    curr = SelectField(
        'Выберите необходимую валюту',
        coerce=str,
        render_kw={'class': 'form-control'},
        validators=[DataRequired()]
    )
    submit = SubmitField('Показать')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
