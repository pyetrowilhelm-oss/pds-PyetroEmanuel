from app import Dono, Pet, app, db


with app.app_context():
    db.create_all()

    if Dono.query.first() is None:
        ana = Dono(nome="Ana Paula Ribeiro", telefone="45999110001")
        bruno = Dono(nome="Bruno Martins", telefone="45999110002")
        db.session.add_all([ana, bruno])
        db.session.commit()

        pets = [
            Pet(nome="Rex", especie="cachorro", idade=4, dono=ana),
            Pet(nome="Mimi", especie="gato", idade=2, dono=ana),
            Pet(nome="Thor", especie="cachorro", idade=7, dono=bruno),
        ]
        db.session.add_all(pets)
        db.session.commit()

print("Banco criado com sucesso.")
