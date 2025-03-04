from flask import Flask, render_template, redirect, url_for, flash, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
import pandas as pd
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fleet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)

@app.route('/')
def home():
    return redirect(url_for('list_machines'))

@app.route('/machines')
def list_machines():
    machines = Machine.query.all()  # Получаем список всех машин
    return render_template('list_machines.html', machines=machines)

# Форма для добавления нового расхода
class ExpenseForm(FlaskForm):
    date = StringField('Дата', validators=[DataRequired(), Length(max=30)])
    type = SelectField('Тип', choices=[
        ('Сломанная деталь', 'Сломанная деталь'),
        ('Авария', 'Авария'),
        ('Топливо за рейс', 'Топливо за рейс'),
        ('Расходник', 'Расходник'),
        ('Прочее', 'Прочее')
    ], validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired(), Length(max=255)])
    amount = IntegerField('Сумма (€)', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')

# Путь к странице с расходами
@app.route('/machine/<int:machine_id>/expense/add', methods=['GET', 'POST'])
def add_expense(machine_id):
    form = ExpenseForm()
    if form.validate_on_submit():
        new_expense = Expense(
            machine_id=machine_id,
            date=form.date.data,
            type=form.type.data,
            description=form.description.data,
            amount=form.amount.data
        )
        db.session.add(new_expense)
        db.session.commit()
        flash("✅ Расход добавлен!", "success")
        return redirect(url_for('machine_detail', machine_id=machine_id))

    return render_template('add_expense.html', form=form, machine_id=machine_id)

# Редактирование данных о расходе
@app.route('/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseForm(obj=expense)

    if form.validate_on_submit():
        expense.date = form.date.data
        expense.type = form.type.data
        expense.description = form.description.data
        expense.amount = form.amount.data

        db.session.commit()
        flash("✅ Расход обновлен!", "success")
        return redirect(url_for('machine_detail', machine_id=expense.machine_id))

    return render_template('edit_expense.html', form=form, expense=expense)

#Удаление записи о расходе
@app.route('/expense/<int:expense_id>/delete', methods=['POST', 'GET'])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    machine_id = expense.machine_id  # Сохраняем ID машины перед удалением

    db.session.delete(expense)
    db.session.commit()
    flash("❌ Расход удален!", "success")

    return redirect(url_for('machine_detail', machine_id=machine_id))

# Форма для добавления новой машины
class MachineForm(FlaskForm):
    number = StringField('Номер машины', validators=[DataRequired(), Length(max=50)])
    brand = StringField('Марка', validators=[DataRequired(), Length(max=50)])
    model = StringField('Модель', validators=[DataRequired(), Length(max=50)])
    year = IntegerField('Год выпуска', validators=[DataRequired()])
    mileage = IntegerField('Километраж', validators=[DataRequired()])
    notes = TextAreaField('Примечания', validators=[Length(max=500)])
    submit = SubmitField('Сохранить')

@app.route('/machine/<int:machine_id>')
def machine_detail(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    trips = Trip.query.filter_by(machine_id=machine_id).all()
    maintenances = Maintenance.query.filter_by(machine_id=machine_id).all()
    expenses = Expense.query.filter_by(machine_id=machine_id).all()
    
    return render_template('machine_detail.html', machine=machine, trips=trips, maintenances=maintenances, expenses=expenses)

# Страница со всеми машинами
@app.route('/machine/<int:machine_id>/edit', methods=['GET', 'POST'])
def edit_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    form = MachineForm(obj=machine)

    if form.validate_on_submit():
        # Обновляем данные машины
        machine.number = form.number.data
        machine.brand = form.brand.data
        machine.model = form.model.data
        machine.year = form.year.data
        machine.mileage = form.mileage.data
        machine.notes = form.notes.data

        db.session.commit()
        flash('✅ Информация о машине обновлена!', 'success')
        return redirect(url_for('machine_detail', machine_id=machine.id))

    return render_template('edit_machine.html', form=form, machine=machine)

# Форма для добавления нового рейса
class TripForm(FlaskForm):
    date = StringField('Дата', validators=[DataRequired(), Length(max=30)])
    route = StringField('Маршрут', validators=[DataRequired(), Length(max=255)])
    distance = IntegerField('Километраж (км)', validators=[DataRequired()])
    fuel = IntegerField('Топливо (л)', validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')

#Добавление рейса
@app.route('/machine/<int:machine_id>/trip/add', methods=['GET', 'POST'])
def add_trip(machine_id):
    form = TripForm()
    if form.validate_on_submit():
        new_trip = Trip(
            machine_id=machine_id,
            date=form.date.data,
            route=form.route.data,
            distance=form.distance.data,
            fuel=form.fuel.data
        )
        db.session.add(new_trip)
        db.session.commit()
        flash("✅ Рейс успешно добавлен!", "success")
        return redirect(url_for('machine_detail', machine_id=machine_id))

    return render_template('add_trip.html', form=form, machine_id=machine_id)

# Редактирование данных рейса
@app.route('/trip/<int:trip_id>/edit', methods=['GET', 'POST'])
def edit_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    form = TripForm(obj=trip)

    if form.validate_on_submit():
        trip.date = form.date.data
        trip.route = form.route.data
        trip.distance = form.distance.data
        trip.fuel = form.fuel.data

        db.session.commit()
        flash("✅ История рейса обновлена!", "success")
        return redirect(url_for('machine_detail', machine_id=trip.machine_id))

    return render_template('edit_trip.html', form=form, trip=trip)

# Удаление рейса
@app.route('/trip/<int:trip_id>/delete', methods=['POST', 'GET'])
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    machine_id = trip.machine_id  # Сохраняем ID машины перед удалением

    db.session.delete(trip)
    db.session.commit()
    flash("❌ Рейс успешно удален!", "success")

    return redirect(url_for('machine_detail', machine_id=machine_id))

# Форма для добавления нового технического обслуживания
class MaintenanceForm(FlaskForm):
    date = StringField('Дата', validators=[DataRequired(), Length(max=30)])
    part = StringField('Деталь', validators=[DataRequired(), Length(max=100)])
    cost = IntegerField('Стоимость (€)', validators=[DataRequired()])
    mechanic = StringField('Механик', validators=[DataRequired(), Length(max=100)])
    location = StringField('Место ремонта', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Сохранить изменения')

# Добавление ТО
@app.route('/machine/<int:machine_id>/maintenance/add', methods=['GET', 'POST'])
def add_maintenance(machine_id):
    form = MaintenanceForm()
    if form.validate_on_submit():
        new_maintenance = Maintenance(
            machine_id=machine_id,
            date=form.date.data,
            part=form.part.data,
            cost=form.cost.data,
            mechanic=form.mechanic.data,
            location=form.location.data
        )
        db.session.add(new_maintenance)
        db.session.commit()
        flash("✅ Техническое обслуживание добавлено!", "success")
        return redirect(url_for('machine_detail', machine_id=machine_id))

    return render_template('add_maintenance.html', form=form, machine_id=machine_id)

# Редактирование данных ТО
@app.route('/maintenance/<int:maintenance_id>/edit', methods=['GET', 'POST'])
def edit_maintenance(maintenance_id):
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    form = MaintenanceForm(obj=maintenance)

    if form.validate_on_submit():
        maintenance.date = form.date.data
        maintenance.part = form.part.data
        maintenance.cost = form.cost.data
        maintenance.mechanic = form.mechanic.data
        maintenance.location = form.location.data

        db.session.commit()
        flash("✅ Данные ТО обновлены!", "success")
        return redirect(url_for('machine_detail', machine_id=maintenance.machine_id))

    return render_template('edit_maintenance.html', form=form, maintenance=maintenance)

# Удаление записи о ТО
@app.route('/maintenance/<int:maintenance_id>/delete', methods=['POST', 'GET'])
def delete_maintenance(maintenance_id):
    maintenance = Maintenance.query.get_or_404(maintenance_id)
    machine_id = maintenance.machine_id  # Сохраняем ID машины перед удалением

    db.session.delete(maintenance)
    db.session.commit()
    flash("❌ Запись о ТО удалена!", "success")

    return redirect(url_for('machine_detail', machine_id=machine_id))

# Таблица с основной информацией о машине
class Machine(db.Model): 
    __tablename__ = 'machine'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)

# Таблица с историей рейсов
class Trip(db.Model):
    __tablename__ = 'trip'
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    route = db.Column(db.String(255), nullable=False)
    distance = db.Column(db.Integer, nullable=False)
    fuel = db.Column(db.Float, nullable=False)

# Таблица с техническим обслуживанием
class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    part = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    mechanic = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)

# Таблица с расходами
class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # "Топливо" или "Запчасти"
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)

# Кнопка для экспорта данных о рейсе в Excel
@app.route('/machine/<int:machine_id>/export_trips', methods=['GET'])
def export_trips(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    trips = Trip.query.filter_by(machine_id=machine_id).all()

    if not trips:
        flash("⚠️ Нет данных о рейсах для экспорта.", "warning")
        return redirect(url_for('machine_detail', machine_id=machine_id))

    # Создаем DataFrame для записи в Excel
    data = {
        "Дата": [trip.date for trip in trips],
        "Маршрут": [trip.route for trip in trips],
        "Километраж (км)": [trip.distance for trip in trips],
        "Топливо (л)": [trip.fuel for trip in trips],
    }
    
    df = pd.DataFrame(data)
    file_path = f"exports/trips_machine_{machine_id}.xlsx"
    
    # Сохраняем файл в папку "exports/"
    df.to_excel(file_path, index=False, engine='openpyxl')

    # Отправляем файл пользователю
    return send_file(file_path, as_attachment=True, download_name=f"История_рейсов_{machine.number}.xlsx")

@app.route('/machine/add', methods=['GET', 'POST'])
def add_machine():
    form = MachineForm()
    if form.validate_on_submit():
        new_machine = Machine(
            number=form.number.data,
            brand=form.brand.data,
            model=form.model.data,
            year=form.year.data,
            mileage=form.mileage.data,
            notes=form.notes.data
        )

        db.session.add(new_machine)
        db.session.commit()
        flash("✅ Машина добавлена!", "success")
        return redirect(url_for('list_machines'))

    return render_template('add_machine.html', form=form)


@app.route('/machine/<int:machine_id>/delete', methods=['POST', 'GET'])
def delete_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    db.session.delete(machine)
    db.session.commit()
    flash("❌ Машина удалена!", "success")
    return redirect(url_for('list_machines'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
