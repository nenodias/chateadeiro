# *-* coding:utf-8 *-*
import logging
import signal
import time
import os

from collections import defaultdict
from urllib.parse import urlparse

from tornado import template
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, parse_command_line, options
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError

import banco


define("port", default=8000, help="run on the given port", type=int)


class MessageHandler(WebSocketHandler):
    '''Trata atualizações de tempo real no quadro de tarefas'''

    def check_origin(self, origin):
        return True

    def open(self, chat):
        '''Registra-se para receber atualizações de chat em uma nova camada'''
        self.chat = chat
        self.application.add_subscriber(self.chat, self)
        lista = banco.get_ultimas_mensagens()
        lista.reverse()
        for mensagem in lista:
            self.write_message(mensagem[1])
        

    def on_message(self, message):
        '''Faz o broadcast das atualizações para outros clientes interessados'''
        self.application.broadcast(message, channel=self.chat, sender=self)
        banco.grava(message)

    def on_close(self):
        '''Remove registros'''
        self.application.remove_subscriber(self.chat, self)




class IndexHandler(RequestHandler):
    '''Trata renderização do cliente'''

    def get(self):
        return self.write(self.application.loader.load("index.html").generate() )






class ChatApplication(Application):
    'Minha applicação'
    def __init__(self, **kwargs):
        routes = [
            (r'/(?P<chat>[0-9]+)', MessageHandler),
            (r'/', IndexHandler),
        ]
        super().__init__(routes, **kwargs)
        self.subscriptions = defaultdict(list)
        self.loader = template.Loader(  os.getcwd() )

    def add_subscriber(self, channel, subscriber):
        self.subscriptions[channel].append(subscriber)

    def remove_subscriber(self, channel, subscriber):
        self.subscriptions[channel].remove(subscriber)

    def get_subscribers(self, channel):
        return self.subscriptions[channel]

    def broadcast(self, message, channel=None, sender=None):
        if channel is None:
            for c in self.subscriptions.keys():
                self.broadcast(message, channel=c, sender=sender)
        else:
            peers = self.get_subscribers(channel)
            for peer in peers:
                if peer != sender:
                    try:
                        peer.write_message(message)
                    except WebSocketClosedError:
                        self.remove_subscriber(channel, peer)






def shutdown(server):
    ioloop = IOLoop.instance()
    logging.info('Stopping server.')
    server.stop()

    def finalize():
        ioloop.stop()
        logging.info('Stopped.')

    ioloop.add_timeout(time.time() + 1.5, finalize)


if __name__ == "__main__":
    parse_command_line()
    application = ChatApplication()
    server = HTTPServer(application)
    server.listen(options.port)
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown(server) )
    logging.info('Starting server on localhost:{}'.format(options.port))
    IOLoop.instance().start()

