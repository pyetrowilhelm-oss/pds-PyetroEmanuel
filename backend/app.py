from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///petshop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Dono(db.Model):
    __tablename__ = "donos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    pets = db.relationship("Pet", backref="dono")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "telefone": self.telefone}


class Pet(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    dono_id = db.Column(db.Integer, db.ForeignKey("donos.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "especie": self.especie,
            "idade": self.idade,
            "dono_id": self.dono_id,
            "dono_nome": self.dono.nome,
        }


def validar_dono(dados):
    erros = []
    if not isinstance(dados, dict):
        return ["O corpo da requisicao precisa ser um JSON de objeto"]

    nome = dados.get("nome")
    if not isinstance(nome, str) or nome.strip() == "":
        erros.append("O campo nome e obrigatorio e nao pode ser vazio")

    telefone = dados.get("telefone")
    if not isinstance(telefone, str) or telefone.strip() == "":
        erros.append("O campo telefone e obrigatorio e nao pode ser vazio")

    return erros


def validar_pet(dados):
    erros = []
    if not isinstance(dados, dict):
        return ["O corpo da requisicao precisa ser um JSON de objeto"]

    nome = dados.get("nome")
    if not isinstance(nome, str) or nome.strip() == "":
        erros.append("O campo nome e obrigatorio e nao pode ser vazio")

    especie = dados.get("especie")
    if not isinstance(especie, str) or especie.strip() == "":
        erros.append("O campo especie e obrigatorio e nao pode ser vazio")

    idade = dados.get("idade")
    if not isinstance(idade, int) or idade < 0:
        erros.append("O campo idade deve ser um numero inteiro maior ou igual a zero")

    dono_id = dados.get("dono_id")
    if not isinstance(dono_id, int):
        erros.append("O campo dono_id deve ser um numero inteiro")
    elif db.session.get(Dono, dono_id) is None:
        erros.append("Nao existe dono com esse dono_id")

    return erros


@app.route("/donos", methods=["GET"])
def listar_donos():
    donos = Dono.query.all()
    return jsonify([dono.to_dict() for dono in donos]), 200


@app.route("/donos/<int:dono_id>", methods=["GET"])
def buscar_dono(dono_id):
    dono = db.session.get(Dono, dono_id)
    if dono is None:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    dados = dono.to_dict()
    dados["pets"] = [pet.to_dict() for pet in dono.pets]
    return jsonify(dados), 200


@app.route("/donos/<int:dono_id>/pets", methods=["GET"])
def listar_pets_do_dono(dono_id):
    dono = db.session.get(Dono, dono_id)
    if dono is None:
        return jsonify({"erro": "Dono nao encontrado"}), 404
    return jsonify([pet.to_dict() for pet in dono.pets]), 200


@app.route("/donos", methods=["POST"])
def criar_dono():
    dados = request.get_json(silent=True)
    erros = validar_dono(dados)
    if erros:
        return jsonify({"erros": erros}), 400

    novo_dono = Dono(nome=dados["nome"].strip(), telefone=dados["telefone"].strip())
    db.session.add(novo_dono)
    db.session.commit()
    return jsonify(novo_dono.to_dict()), 201


@app.route("/donos/<int:dono_id>", methods=["PUT"])
def atualizar_dono(dono_id):
    dados = request.get_json(silent=True)
    erros = validar_dono(dados)
    if erros:
        return jsonify({"erros": erros}), 400

    dono = db.session.get(Dono, dono_id)
    if dono is None:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    dono.nome = dados["nome"].strip()
    dono.telefone = dados["telefone"].strip()
    db.session.commit()
    return jsonify(dono.to_dict()), 200


@app.route("/donos/<int:dono_id>", methods=["DELETE"])
def remover_dono(dono_id):
    dono = db.session.get(Dono, dono_id)
    if dono is None:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    db.session.delete(dono)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"erro": "O dono possui pets cadastrados"}), 400
    return jsonify({"mensagem": "Dono removido com sucesso"}), 200


@app.route("/pets", methods=["GET"])
def listar_pets():
    dono_id = request.args.get("dono_id")
    consulta = Pet.query

    if dono_id is not None:
        try:
            dono_id = int(dono_id)
        except ValueError:
            return jsonify({"erro": "dono_id deve ser um numero inteiro"}), 400
        consulta = consulta.filter_by(dono_id=dono_id)

    pets = consulta.all()
    return jsonify([pet.to_dict() for pet in pets]), 200


@app.route("/pets/<int:pet_id>", methods=["GET"])
def buscar_pet(pet_id):
    pet = db.session.get(Pet, pet_id)
    if pet is None:
        return jsonify({"erro": "Pet nao encontrado"}), 404
    return jsonify(pet.to_dict()), 200


@app.route("/pets", methods=["POST"])
def criar_pet():
    dados = request.get_json(silent=True)
    erros = validar_pet(dados)
    if erros:
        return jsonify({"erros": erros}), 400

    novo_pet = Pet(
        nome=dados["nome"].strip(),
        especie=dados["especie"].strip(),
        idade=dados["idade"],
        dono_id=dados["dono_id"],
    )
    db.session.add(novo_pet)
    db.session.commit()
    return jsonify(novo_pet.to_dict()), 201


@app.route("/pets/<int:pet_id>", methods=["PUT"])
def atualizar_pet(pet_id):
    dados = request.get_json(silent=True)
    erros = validar_pet(dados)
    if erros:
        return jsonify({"erros": erros}), 400

    pet = db.session.get(Pet, pet_id)
    if pet is None:
        return jsonify({"erro": "Pet nao encontrado"}), 404

    pet.nome = dados["nome"].strip()
    pet.especie = dados["especie"].strip()
    pet.idade = dados["idade"]
    pet.dono_id = dados["dono_id"]
    db.session.commit()
    return jsonify(pet.to_dict()), 200


@app.route("/pets/<int:pet_id>", methods=["DELETE"])
def remover_pet(pet_id):
    pet = db.session.get(Pet, pet_id)
    if pet is None:
        return jsonify({"erro": "Pet nao encontrado"}), 404

    db.session.delete(pet)
    db.session.commit()
    return jsonify({"mensagem": "Pet removido com sucesso"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
