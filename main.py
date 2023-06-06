from flask import Flask, render_template, redirect, request, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import now

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT

from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash
##### Day 68 Authentication
##### Day 69 Blog Adding


app = Flask(__name__)


host = 'YOUR SERVER'
user = 'YOUR USER'
password = 'YOUR PASSWORD'
database = 'YOUR DATABASE NAME'
port = 3306 ### usually 3306 but it can be a different one

### esto es para el FlaskLogin, sin esto genera error
app.config['SECRET_KEY'] = 'YOUR SECRET KEY'

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{user}:{password}@{host}:{port}/{database}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



db = SQLAlchemy(app)

#### LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # return User.get(user_id)
    return UserToDoWeb.query.filter_by(id=user_id).first() ### así se hizo en la
    # leccion 68
    # return UserToDoWeb.get_id(user_id) ### asì dice el manual


class UserToDoWeb(UserMixin, db.Model):
    __tablename__ = 'UserToDoWeb'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    
    ### relation with the other table
    todo_rel = relationship('TodoWeb', back_populates='owner')


class TodoWeb(db.Model):
    __tablename__ = 'Todo_Web'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    # created_by = db.Column(db.Integer, nullable=False, ForeignKey("UserTodo_Web.id"))
    created_by = db.Column(db.Integer, db.ForeignKey('UserToDoWeb.id'))
    created_at = db.Column(db.DateTime(), server_default=now())
    description = db.Column(db.String(250), nullable=False)
    completed = db.Column(TINYINT(1))

    #### relation with the other table
    owner = relationship('UserToDoWeb', back_populates='todo_rel')



### este crea las bases de datos en caso de no existir.
### sion el with, hay que comentarlo porque genera error
### si ya existen, es decir al segundo arranque

with app.app_context():
    db.create_all()




@app.route('/')
def home():

    if current_user.is_authenticated:
        return redirect(url_for('todoweb'))
    else:
        return render_template("index.html", logged_in=current_user.is_authenticated)



@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        #### find the user
        # find_user = db.session.execute(db.select(UserToDoWeb).filter_by(email=email)).first()        

        find_user = UserToDoWeb.query.filter_by(email=email).first()


        # print(find_user.email)
        # print(find_user.password)

        if not find_user:
            flash("That email does not exist. Please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(find_user.password, password):
            flash("Email or Password incorrect, please try again")
            return redirect(url_for('login'))
        else:
            login_user(find_user)
            return redirect(url_for('todoweb'))
        


    return render_template('login.html', logged_in=current_user.is_authenticated)





#### aquí muestro el listado
@app.route('/todoweb/', methods=['GET', 'POST'])
def todoweb():

    if current_user.is_authenticated:

        ### este if es sí hace un post nuevo con el boton y el espacio    
        if request.method == 'POST':
        
            
            #### cuando es nuevo, description viene con valor desde el HTML

            if request.form.get('description') != None:
                new_todo = TodoWeb(
                    description = request.form.get('description'),
                    created_by = current_user.get_id(),
                    completed = 0,
                )                 

                try:
                    db.session.add(new_todo)
                    db.session.commit()

                    return redirect(url_for('todoweb'))

                except Exception as e:
                    print("Error exception", e)
                    return redirect(url_for('home'))

            else:
                
                todo_id = request.args['todo_id']

                edit_entry = db.get_or_404(TodoWeb, todo_id)
                
                print("Edit entry ", edit_entry.completed)

                if edit_entry.completed == 0:
                    edit_entry.completed = 1
                else:
                    edit_entry.completed = 0
                
                db.session.commit()


                return redirect(url_for('todoweb'))

        
        
        
        ### aquí traigo lo que hay en DB para mostrar
        todo_show = db.session.execute(db.select(TodoWeb).filter_by(created_by=current_user.get_id())).scalars().all()
        # print(todo_show  
        return render_template('todoweb.html', logged_in=current_user.is_authenticated, todo_show=todo_show)


    else:
        return redirect(url_for('login'))




@app.route('/register', methods=['GET', 'POST'])
def register():

    ### lanzar el formulario de registro verificando sí está registrado
    if request.method == 'POST':
        
        ### verifico sì el email ya está en DB
        find_email = db.session.execute(db.select(UserToDoWeb).filter_by(email=request.form.get('email'))).first()
        #print("Find email",find_email)
        
        ### no está en DB, procedo a meterlo
        if find_email == None:
            ### cambio a has password seguridad
            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=16
                
            )
            
            new_user = UserToDoWeb(
                name = request.form.get('name'),
                email = request.form.get('email'),
                password = hash_and_salted_password  ### el generado antes
            )
        
            ### ahora intento colocar la info en DB

            try:
                db.session.add(new_user)
                db.session.commit()

                ### dejar al usuario loggeado
                login_user(new_user)

                ### redirijo inicialmente al 
                return redirect(url_for('todoweb'))

            except Exception as e:
                print(e)
                return redirect(url_for('home'))


        flash("You've already signed up with that email, log in instead")
        return redirect('login')


        
    return render_template('register.html')




@app.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
