from flask import (
    render_template,
    request,
    Flask,
    Blueprint,
    flash,
    url_for,
    redirect,
    session,
)
from DAO import *
from hashlib import sha256
from envio_email import gerar_codigo, enviar_email

codigos_de_verificacao = {}

auth = Blueprint("auth", __name__, template_folder="templates")
app = Flask(__name__)


@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    senha = sha256(request.form.get("senha").encode("utf-8")).hexdigest()

    count = CheckLogin(email, senha)

    # Se não logar...
    if count == 0:
        flash("Senha e/ou Email incorretos")
        return redirect(url_for("auth.login"))

    # se logar...
    session["loggedin"] = True
    session["id"] = selectFromWhere("tb_usuario", "user_email", email, "user_id")
    session["nome"] = selectFromWhere("tb_usuario", "user_email", email, "user_name")
    session["email"] = email

    return redirect(url_for("home"))


@auth.route("/cadastro")
def cadastro():
    return render_template("Cadastro.html")


@auth.route("/cadastro", methods=["POST"])
def registro_post():
    email = request.form.get("email")
    senha = request.form.get("senha")
    nome1 = request.form.get("nome1")
    nome2 = request.form.get("nome2")
    cpf = request.form.get("cpf")

    checkEmail = CheckCadastro("user_email", email)
    checkCPF = CheckCadastro("user_cpf", cpf)

    if checkEmail >= 1:
        flash("Email já cadastrado!")
        return redirect(url_for("auth.cadastro"))
    elif checkCPF >= 1:
        flash("CPF já cadastrado")
        return redirect(url_for("auth.cadastro"))
    elif not email or not senha or not nome1 or not nome2 or not cpf:
        flash("Preencha o formulário todo!")
        return redirect(url_for("cadastro"))

    else:
        senhaHash = sha256(senha.encode("utf-8")).hexdigest()
        insertCadastro(email, senhaHash, nome1, nome2, cpf)
        flash("Cadastrado com sucesso!")
        return redirect(url_for("auth.login"))


@auth.route("/recuperar_senha")
def recuperar_senha():
    return render_template("ES_addEmail.html")


@auth.route("/recuperar_senha", methods=["POST"])
def recuperar_senha_post():
    email = request.form.get("user_email")

    count = CheckCadastro("user_email", email)

    if count >= 1:

        codigo_verificacao = gerar_codigo()
        expiration_time = 10

        checkCodigo = selectFromWhere("tb_verificacao_senha", "user_email", email)

        if checkCodigo is not None:
            deleteCodigo(email)
        envio_email = enviar_email(codigo_verificacao, email)

        if  envio_email[1] == 0:
            flash(envio_email[0])
            return redirect(url_for("auth.recuperar_senha"))
        
        else:
            insertCodigo(email, codigo_verificacao, expiration_time)

            session["EmailVerificadoReset"] = True

            flash(envio_email[0])
            return redirect(url_for("auth.ES_6digito", email=email))

    else:
        flash("Email não cadastrado!")
        return redirect(url_for("auth.recuperar_senha"))


@auth.route("/verificar_codigo/<email>")
def verificar_codigo(email):
    if "EmailVerificadoReset" in session and session["EmailVerificadoReset"] is True:
        return render_template("ES_6digito.html", email=email)
    else:
        return redirect(url_for("auth.login"))


# Rota para verificar o código de verificação inserido pelo usuário
@auth.route("/verificar_codigo", methods=["POST"])
def verificar_codigo_post():
    codigo_inserido = ''
    email = request.form.get("email")
    for num in range(1, 7):
        codigo_inserido += str(request.form.get(f"number_{num}"))


    codigo_gerado = selectFromWhere(
        "tb_verificacao_senha", "user_email", email, "verification_code"
    )

    if codigo_gerado == int(codigo_inserido):
        deleteCodigo(email)
        # session.pop("EmailVerificadoReset", None)
        return redirect(url_for("auth.Rota_da_nova_senha", email=email))

    else:
        flash("Código de verificação incorreto. Por favor, tente novamente.")
        return redirect(url_for("auth.verificar_codigo", email=email))
