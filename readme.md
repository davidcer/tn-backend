

0 - Clone project repos:
- backend:
- frontend:

1 - Create your virtual enviroment:
python3 -m venv/bin/activate

2- Install requirement
pip install -r requirements.txt

3 - setup .env configuration:
- database

4 - build react app

5 - export to public template

6 - set-up nginx server

7 - har code costs.

8 - implement tests


@ grabing ideas from...
https://dev.to/nagatodev/how-to-connect-flask-to-reactjs-1k8i


Self comments:

* from flask_migrate import Migrate
migrate = Migrate(app, db)
* this comes with sql lite. further upgrades can be shared.

requirements:
- hook function user_credit()
- node, python3.x, 
- nums, separated by ;, decimal by ,
- primero validar el crédito después ejecutar la función.
- implement logger
- remover dependencias
- instalar git
- set password hash for user
- add message to log in when rejected


# @app.error(400)
# @app.error(500)