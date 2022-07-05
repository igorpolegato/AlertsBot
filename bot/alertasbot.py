from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from data import *

from datetime import datetime
from traceback import print_exc
from random import randrange as rd, choice

import mysql.connector
import threading

app = Client("GSorteio",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token)


with app:
    pass

lock = threading.Lock()
add_produto = []
dados = lambda mensagem: [mensagem.chat.id, mensagem.chat.first_name, mensagem.text]
################## MySQL #################

def bd():
    global con, cur1, cur2, cur3

    con = mysql.connector.connect(
        host=dbhost,
        user=dbuser,
        password=dbpasswd,
        database=dbname
    )

    cur = con.cursor(buffered=True) # cursor para criar tabelas
    cur1 = con.cursor(buffered=True) # cursor para tabela clientes
    cur2 = con.cursor(buffered=True) # cursor para tabela pchaves
    cur3 = con.cursor(buffered=True) # 

    cur.execute(
        "create table if not exists clientes("
        "id int auto_increment primary key,"
        "nome varchar(30) not null,"
        "cod bigint not null,"
        "unique(cod))"
    )

    cur.execute(
        "create table if not exists pchaves("
        "id int auto_increment primary key,"
        "user_cod bigint not null,"
        "produto varchar(100) not null)"
    )

############## COMANDOS ####################

@app.on_message(filters.private & filters.command("start")) #Resposta para o comando start, que é enviado quando um usuário inicia o bot
def start(bot, mensagem):
    user_id = mensagem.chat.id
    fname = str(mensagem.chat.first_name)

    registrar(user_id, fname)
    helpC(bot, mensagem)

@app.on_message(filters.private & filters.command("help")) #Resposta para o comando help, que consulta a maioria dos comando disponíveis do bot
def helpC(bot, mensagem):
    user_id = mensagem.chat.id
    fname = mensagem.chat.first_name

    btns = [
        [InlineKeyboardButton("Cadastrar produto", callback_data="help_cpd"), InlineKeyboardButton("Apagar produto", callback_data="help_delpd")],
        [InlineKeyboardButton("Meus produtos", callback_data="help_mypd")]
    ]

    markup = InlineKeyboardMarkup(btns)

    app.send_message(user_id, "Esses são meus comandos, clique neles para usa-los!", reply_markup=markup)
    print(f"O usuário {fname}({user_id}) consultou os comandos --> /help\n")

@app.on_message(filters.private & filters.command("consultar"))
def consultar(bot, mensagem):
    user_id = dados(mensagem)[0]
    #btns = []
    produtos = [p[0] for p in bdMap(2, "select produto from pchaves where user_cod=%s", [user_id])]

    if len(produtos) > 0:
        #for produto in produtos:
            #btns.append([InlineKeyboardButton(produto)])
        
        msg = "Esses são os produtos que você possui cadastrado: \n\n" + ', '.join(produtos)

        #markup = InlineKeyboardMarkup(btns)

        app.send_message(user_id, msg)
    
    else:
        app.send_message(user_id, "Você não possui produtos cadastrados!")

@app.on_message(filters.command("teste"))
def teste(bot, mensagem):
    user_id, fname, produto = dados(mensagem)
    print(user_id, fname, produto)

@app.on_message(filters.private)
def interact(bot, mensagem):
    user_id, fname, produto = dados(mensagem)

    ########### Adicionar produto ###########

    if user_id in add_produto:
        pc = len(bdMap(2, "select * from pchaves where user_cod=%s and produto=%s", [user_id, produto]))

        if pc == 0:
            bdMap(2, "insert into pchaves(user_cod, produto) values(%s, %s)", [user_id, produto], "insert")
            app.send_message(user_id, f"{produto} registrado!")
            print(f"O usuário {fname}({user_id}) cadastrou um novo produto ({produto})\n")

        else:
            app.send_message(user_id, f"{produto} já está registrado!")
        
        add_produto.remove(user_id)

@app.on_message(filters.channel)
def monitor(bot, mensagem):
    m_id = mensagem.id
    group_id = mensagem.chat.id
    title = mensagem.chat.title
    media = str(mensagem.media).replace("MessageMediaType.", "").lower()
    url = f"https://t.me/c/{str(group_id)[3:]}/{m_id}"
    produtos = {p[1]: p[2].split() for p in bdMap(2, "select * from pchaves")}

    if media == "none":
        text = mensagem.text.lower()
    
    else:
        text = mensagem.caption.lower()

        for k, v in produtos.items():
            if all(p.lower() in text for p in v):
                markup = InlineKeyboardMarkup([[InlineKeyboardButton("Ir para a mensagem", url=url)]])

                app.send_message(k, f"🚨 O produto {' '.join(v)} foi mencionado em {title}.\n\nNão deixe de conferir!", reply_markup=markup)
    
    
############# UTILS #############

def registrar(user_id, fname): #Registrar novo usuário
    try:
        r = bdMap(1, "insert into clientes(cod, nome) values(%s, %s)", [user_id, fname], "insert")
        if r == "duplicate":
            app.send_message(user_id, "Usuário já cadastrado!")
        else:
            app.send_message(user_id, "Usuário cadastrado!")
    except Exception as errorrg:
        print(errorrg)

    print(f"O usuário {fname}({user_id}) foi registrado\n")

def rList(user_id):
    produtos = [p[0] for p in bdMap(2, "select produto from pchaves where user_cod=%s", [user_id])]
    btns = []

    if len(produtos) > 0:
        for produto in produtos:
            btns.append([InlineKeyboardButton(produto, callback_data=f"rlist_{produto}")])

        markup = InlineKeyboardMarkup(btns)
        app.send_message(user_id, "Esses são os produtos que você possui cadastrados!\n\nSelecione o produto que deseja remover", reply_markup=markup)
    
    else:
        app.send_message(user_id, "Você não possui produtos cadastrados!")

def deletePd(user_id, fname, produto):
    bdMap(2, "delete from pchaves where produto=%s", [produto], "delete")

    app.send_message(user_id, f"{produto} foi removido da sua lista!")
    print(f"O usuário {fname}({user_id}) removeu um produto da lista ({produto})\n")

def registrado(user_id):
    user = bdMap(1, "select * from clientes where cod=%s")

    if len(user) > 0:
        return True
    else:
        return False

def bdMap(c, sql, var=None,  method="select"): #Interações com banco de dados
    cursors = {
        1: cur1,
        2: cur2,
        3: cur3,
    }

    lock.acquire(True)
    log(f"Executando {c}, {sql}, {var}, {method}\n")
    try:
        if method == "select":
            if var is None:
                cursors[c].execute(sql)
                item = cursors[c].fetchall()
            else:
                cursors[c].execute(sql, var)
                item = cursors[c].fetchall()
            return item
        else:
            if var is None:
                cursors[c].execute(sql)
            else:
                cursors[c].execute(sql, var)
            con.commit()
    except Exception as e:
        log(f"Erro: {e}\n")
        con.rollback()
        if "Duplicate entry" in str(e):
            return "duplicate"
    finally:
        log(f"Executado {c}, {sql}, {var}, {method}\n\n")
        lock.release()

def log(texto):
    with open("log.txt", "a+", encoding="utf-8") as arq:
        arq.write(f"[{datetime.now().strftime('%x %X.%f')}] ")
        arq.write(texto)

############## CALLBACKS ####################

@app.on_callback_query(filters.regex("^rlist\S"))
def callDelete(bot, call):
    user_id, fname = dados(call.message)[0:2]
    produto = call.data[6:]

    deletePd(user_id, fname, produto)

@app.on_callback_query(filters.regex("^help_cpd"))
def callRpd(bot, call):
    user_id = call.from_user.id

    add_produto.append(user_id)
    app.send_message(user_id, "Envie o produto que deseja cadastrar")

@app.on_callback_query(filters.regex("^help_delpd"))
def callRlist(bot, call):
    user_id = dados(call.message)[0]
    rList(user_id)

@app.on_callback_query(filters.regex("^help_mypd"))
def callConsultar(bot, call):
    consultar(bot, call.message)

############## INICIALIZAÇÃO ####################

if __name__ == "__main__":
    bd()
    print("+----------------+\n"
          "|  BOT INICIADO  |\n"
          "+----------------+\n")
    app.run()
