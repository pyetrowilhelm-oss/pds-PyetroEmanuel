import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

BANCO = "petshop.db"


def conectar():
    conexao = sqlite3.connect(BANCO)
    # Habilita o suporte a chaves estrangeiras no SQLite
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def init_db():
    """Cria as tabelas automaticamente caso não existam."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            idade INTEGER NOT NULL,
            dono_id INTEGER NOT NULL,
            FOREIGN KEY (dono_id) REFERENCES donos (id) ON DELETE CASCADE
        );
    """)
    conexao.commit()
    conexao.close()


# Inicializa o banco de dados ao subir a aplicação
init_db()


# ---------------------------------------------------------------
# ROTAS DE DONOS
# ---------------------------------------------------------------


@app.route("/donos", methods=["GET"])
def listar_donos():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, telefone FROM donos")
    linhas = cursor.fetchall()
    conexao.close()

    donos = [{"id": l[0], "nome": l[1], "telefone": l[2]} for l in linhas]
    return jsonify(donos), 200


@app.route("/donos/<int:dono_id>", methods=["GET"])
def buscar_dono(dono_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, telefone FROM donos WHERE id = ?", (dono_id,))
    linha = cursor.fetchone()
    conexao.close()

    if linha is None:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    return jsonify({"id": linha[0], "nome": linha[1], "telefone": linha[2]}), 200


@app.route("/donos", methods=["POST"])
def criar_dono():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict) or "nome" not in dados or "telefone" not in dados:
        return jsonify({"erro": "Informe nome e telefone em formato JSON valido"}), 400

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO donos (nome, telefone) VALUES (?, ?)",
        (dados["nome"], dados["telefone"])
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()

    return jsonify({"id": novo_id, "nome": dados["nome"], "telefone": dados["telefone"]}), 201


@app.route("/donos/<int:dono_id>", methods=["PUT"])
def atualizar_dono(dono_id):
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict) or "nome" not in dados or "telefone" not in dados:
        return jsonify({"erro": "Informe nome e telefone em formato JSON valido"}), 400

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE donos SET nome = ?, telefone = ? WHERE id = ?",
        (dados["nome"], dados["telefone"], dono_id)
    )
    conexao.commit()
    alterados = cursor.rowcount
    conexao.close()

    if alterados == 0:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    return jsonify({"id": dono_id, "nome": dados["nome"], "telefone": dados["telefone"]}), 200


@app.route("/donos/<int:dono_id>", methods=["DELETE"])
def remover_dono(dono_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM donos WHERE id = ?", (dono_id,))
    conexao.commit()
    removidos = cursor.rowcount
    conexao.close()

    if removidos == 0:
        return jsonify({"erro": "Dono nao encontrado"}), 404

    return jsonify({"mensagem": "Dono removido com sucesso"}), 200


# ---------------------------------------------------------------
# ROTAS DE PETS
# ---------------------------------------------------------------


@app.route("/pets", methods=["GET"])
def listar_pets():
    dono_id = request.args.get("dono_id")

    conexao = conectar()
    cursor = conexao.cursor()

    sql = """
        SELECT pets.id, pets.nome, pets.especie, pets.idade, pets.dono_id, donos.nome AS dono_nome
        FROM pets
        INNER JOIN donos ON pets.dono_id = donos.id
    """
    parametros = []

    if dono_id:
        sql += " WHERE pets.dono_id = ?"
        parametros.append(dono_id)

    cursor.execute(sql, parametros)
    linhas = cursor.fetchall()
    conexao.close()

    pets = [
        {
            "id": l[0],
            "nome": l[1],
            "especie": l[2],
            "idade": l[3],
            "dono_id": l[4],
            "dono_nome": l[5]
        }
        for l in linhas
    ]

    return jsonify(pets), 200


@app.route("/pets/<int:pet_id>", methods=["GET"])
def buscar_pet(pet_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT pets.id, pets.nome, pets.especie, pets.idade, pets.dono_id, donos.nome AS dono_nome
        FROM pets
        INNER JOIN donos ON pets.dono_id = donos.id
        WHERE pets.id = ?
        """,
        (pet_id,)
    )
    linha = cursor.fetchone()
    conexao.close()

    if linha is None:
        return jsonify({"erro": "Pet nao encontrado"}), 404

    return jsonify({
        "id": linha[0],
        "nome": linha[1],
        "especie": linha[2],
        "idade": linha[3],
        "dono_id": linha[4],
        "dono_nome": linha[5]
    }), 200


@app.route("/pets", methods=["POST"])
def criar_pet():
    dados = request.get_json(silent=True)

    campos = ["nome", "especie", "idade", "dono_id"]
    if not isinstance(dados, dict) or not all(k in dados for k in campos):
        return jsonify({"erro": "Informe nome, especie, idade e dono_id"}), 400

    conexao = conectar()
    cursor = conexao.cursor()

    # Valida se o dono_id existe antes de inserir
    cursor.execute("SELECT id FROM donos WHERE id = ?", (dados["dono_id"],))
    if cursor.fetchone() is None:
        conexao.close()
        return jsonify({"erro": "O dono_id informado nao existe"}), 400

    cursor.execute(
        "INSERT INTO pets (nome, especie, idade, dono_id) VALUES (?, ?, ?, ?)",
        (dados["nome"], dados["especie"], dados["idade"], dados["dono_id"])
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()

    return jsonify({
        "id": novo_id,
        "nome": dados["nome"],
        "especie": dados["especie"],
        "idade": dados["idade"],
        "dono_id": dados["dono_id"]
    }), 201


@app.route("/pets/<int:pet_id>", methods=["PUT"])
def atualizar_pet(pet_id):
    dados = request.get_json(silent=True)

    campos = ["nome", "especie", "idade", "dono_id"]
    if not isinstance(dados, dict) or not all(k in dados for k in campos):
        return jsonify({"erro": "Informe nome, especie, idade e dono_id"}), 400

    conexao = conectar()
    cursor = conexao.cursor()

    # Valida se o dono_id existe antes de atualizar
    cursor.execute("SELECT id FROM donos WHERE id = ?", (dados["dono_id"],))
    if cursor.fetchone() is None:
        conexao.close()
        return jsonify({"erro": "O dono_id informado nao existe"}), 400

    cursor.execute(
        "UPDATE pets SET nome = ?, especie = ?, idade = ?, dono_id = ? WHERE id = ?",
        (dados["nome"], dados["especie"], dados["idade"], dados["dono_id"], pet_id)
    )
    conexao.commit()
    alterados = cursor.rowcount
    conexao.close()

    if alterados == 0:
        return jsonify({"erro": "Pet nao encontrado"}), 404

    return jsonify({
        "id": pet_id,
        "nome": dados["nome"],
        "especie": dados["especie"],
        "idade": dados["idade"],
        "dono_id": dados["dono_id"]
    }), 200


@app.route("/pets/<int:pet_id>", methods=["DELETE"])
def remover_pet(pet_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
    conexao.commit()
    removidos = cursor.rowcount
    conexao.close()

    if removidos == 0:
        return jsonify({"erro": "Pet nao encontrado"}), 404

    return jsonify({"mensagem": "Pet removido com sucesso"}), 200


if __name__ == "__main__":
    # Configurado para expor no GitHub Codespaces
    app.run(host="0.0.0.0", port=5000, debug=True)
