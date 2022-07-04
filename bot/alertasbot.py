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
        "palavras varchar(100) not null)"
    )

############## COMANDOS ####################

@app.on_message(filters.private & filters.command("start")) #Resposta para o comando start, que é enviado quando um usuário inicia o bot
def start(bot, mensagem):
    m_id = mensagem.id
    user_id = mensagem.chat.id
    fname = str(mensagem.chat.first_name)

    registrar(user_id, fname)
    #helpC(bot, mensagem)

@app.on_message(filters.private & filters.command("help")) #Resposta para o comando help, que consulta a maioria dos comando disponíveis do bot
def helpC(bot, mensagem):
    user_id = mensagem.chat.id
    fname = mensagem.chat.first_name

    btns = [
        [InlineKeyboardButton("Sorteios", callback_data="help_sorteios"), InlineKeyboardButton("Cupons", callback_data="help_cupons")],
        [InlineKeyboardButton("Registrar Sorteio", callback_data="help_regsorteio"), InlineKeyboardButton("Apagar sorteio", callback_data="help_rmsorteio")],
        [InlineKeyboardButton("Sortear", callback_data="help_sortear"), InlineKeyboardButton("Atualizar regras", callback_data="help_atregras")],
        [InlineKeyboardButton("Indicação", callback_data="help_ind")]

    ]

    markup = InlineKeyboardMarkup(btns)

    app.send_message(user_id, "Esses são meus comandos, clique neles para usa-los!\n\nPara pegar um cupom, veja os sorteios disponiveis", reply_markup=markup)
    print(f"O usuário {fname}({user_id}) consultou os comandos --> /help\n")


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

############## INICIALIZAÇÃO ####################

if __name__ == "__main__":
    bd()
    print("+----------------+\n"
          "|  BOT INICIADO  |\n"
          "+----------------+\n")
    app.run()
