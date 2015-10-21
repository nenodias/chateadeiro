import sqlite3
conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE mensagem ( msg VARCHAR(5000) );')
conn.commit()

if __name__ == '__main__':
	c.execute('SELECT ROWID, * FROM mensagem ORDER BY ROWID DESC LIMIT 10')
	print(c.fetchall())


def get_ultimas_mensagens():
	c.execute('SELECT ROWID, * FROM mensagem ORDER BY ROWID DESC LIMIT 10')
	return c.fetchall()

def grava(mensagem):
	c.execute('INSERT INTO mensagem VALUES ( :mensagem )', { "mensagem" : mensagem } )
	conn.commit()
