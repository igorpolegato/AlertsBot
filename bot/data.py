import configparser

config = configparser.ConfigParser()
config.read('config.ini')

bt = config['bot']
db = config['MySQL']
adm = config['adm']

api_id = bt['api_id']
api_hash = bt['api_hash']
bot_token = bt['bot_token']

dbhost = db['host']
dbuser = db['user']
dbpasswd = db['pass']
dbname = db['name']

adm_id = int(adm['user_id'])
