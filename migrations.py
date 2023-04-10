from db.models import *

if __name__ == "__main__":
    Base.metadata.create_all(engine)

    if not Operation.query.filter_by(alias="add").first():
        session.add(Operation(operation_type="addition", alias="add", cost=10))
    if not Operation.query.filter_by(alias="sub").first():
        session.add(Operation(operation_type="substraction", alias="sub", cost=10))
    if not Operation.query.filter_by(alias="div").first():
        session.add(Operation(operation_type="division", alias="div", cost=10))
    if not Operation.query.filter_by(alias="mul").first():
        session.add(Operation(operation_type="multiplication", alias="mul", cost=10))
    if not Operation.query.filter_by(alias="rand").first():
        session.add(Operation(operation_type="random_string", alias="rand", cost=50))
    if not Operation.query.filter_by(alias="random_string").first():
        session.add(Operation(operation_type="square_root", alias="sqr", cost=40))

    session.commit()
