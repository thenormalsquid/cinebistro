import os.path
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornadoredis
import logging

import random

from tornado.options import define, options, parse_command_line

define("port", default=1492, help="run on the given port", type=int)


#should get object from mainhandler and store to redis, but for test purposes, we'll just use minehandler for that now

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MenuHandler),
	        (r"/edit", EditHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/test", TestHandler)
        ]
        settings = dict(
            cookie_secret="nowayjose",
            login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            autoescape=None,
            ui_modules={"Entrees": EntreeModule, "Desserts": DessertModule, "Beverages": BeverageModule, "Menu": MenuModule},
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class TestHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        c = tornadoredis.Client()
        c.connect()
        pipe = c.pipeline()
        for i in xrange(1,5):
            keye = "entree" + str(i)
            keyd = "dessert" + str(i)
            keyb = "beverage" + str(i)
            keydtit = "dessert_title"+str(i)
            keyddesc = "dessert_desc" + str(i)
            keyetit = "entree_title" + str(i)
            keyedesc = "entree_desc" + str(i)
            keybtit = "beverage_title" + str(i)
            keybdesc = "beverage_desc" + str(i)
            entrees = {}
            desserts = {}
            beverages = {}
            dtitle = ""
            ddesc = ""
            etitle = ""
            edesc = ""
            btitle = ""
            bdesc = ""
            entrees[keyetit] = etitle
            entrees[keyedesc] = edesc
            desserts[keydtit] = dtitle
            desserts[keyddesc] = ddesc
            beverages[keybtit] = btitle
            beverages[keybdesc] = bdesc
            pipe.hmset(keye, entrees)
            pipe.hmset(keyd, desserts)
            pipe.hmset(keyb, beverages)
        yield tornado.gen.Task(pipe.execute)
        self.render("menu.html")


class IndexHandler(BaseHandler):
    def get(self):
        self.render("index.html")

class AuthLoginHandler(BaseHandler):
    def get(self):
        error = None
        self.render("login.html", next=self.get_argument("next","/"), errors=error)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        c = tornadoredis.Client()
        c.connect()
        user = self.get_argument("username")
        if user == u'': print "truedatyo"
        pw = self.get_argument("password")
        user2 = yield tornado.gen.Task(c.hget, "user", "username")
        pw2 = yield tornado.gen.Task(c.hget, "user","password")
        if user == user2 and pw == pw2:
            print 'true yeah'
            self.set_secure_cookie("user", user)
            self.redirect(self.get_argument("next", u"/"))
        else:
            print 'dsfl'
            errors = "Uh, uh, uh, you didn't say the magic word!"
            self.render("login.html" , errors=errors)


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class EditHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self):
        c = tornadoredis.Client()
        c.connect()
        pipe = c.pipeline()
        e = []
        d = []
        b = []
        for i in xrange(1,5):
            pipe.hgetall("entree"+str(i))
            pipe.hgetall("dessert"+str(i))
            pipe.hgetall("beverage"+str(i))
            entree, dessert, beverage = yield tornado.gen.Task(pipe.execute)
            e.append(entree)
            d.append(dessert)
            b.append(beverage)
        show = yield tornado.gen.Task(c.hget,"showing", "movies")
        self.render("edit.html", entrees=e, desserts=d, beverages=b, show=show)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        c = tornadoredis.Client()
        c.connect()
        pipe = c.pipeline()
        for i in xrange(1,5):
            keye = "entree" + str(i)
            keyd = "dessert" + str(i)
            keyb = "beverage" + str(i)
            keydtit = "dessert_title"+str(i)
            keyddesc = "dessert_desc" + str(i)
            keyetit = "entree_title" + str(i)
            keyedesc = "entree_desc" + str(i)
            keybtit = "beverage_title" + str(i)
            keybdesc = "beverage_desc" + str(i)
            entrees = {}
            desserts = {}
            beverages = {}
            dtitle = self.get_argument(keydtit)
            ddesc = self.get_argument(keyddesc)
            etitle = self.get_argument(keyetit)
            edesc = self.get_argument(keyedesc)
            btitle = self.get_argument(keybtit)
            bdesc = self.get_argument(keybdesc)
            entrees[keyetit] = etitle
            entrees[keyedesc] = edesc
            desserts[keydtit] = dtitle
            desserts[keyddesc] = ddesc
            beverages[keybtit] = btitle
            beverages[keybdesc] = bdesc
            pipe.hmset(keye, entrees)
            pipe.hmset(keyd, desserts)
            pipe.hmset(keyb, beverages)
        now_playing = self.get_argument("showing")
        pipe.hset("showing", "movies", now_playing)
        yield tornado.gen.Task(pipe.execute)
        self.redirect("/")


class MenuHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        c = tornadoredis.Client()
        c.connect()
        pipe = c.pipeline()
        e = []
        d = []
        b = []
        for i in xrange(1,5):
            pipe.hgetall("entree"+str(i))
            pipe.hgetall("dessert"+str(i))
            pipe.hgetall("beverage"+str(i))
            entree, dessert, beverage = yield tornado.gen.Task(pipe.execute)
            e.append(entree)
            d.append(dessert)
            b.append(beverage)
        show = yield tornado.gen.Task(c.hget,"showing", "movies")
        print e
        self.render("menu.html", entrees=e, desserts=d, beverages=b, show=show)

class EntreeModule(tornado.web.UIModule):
    def render(self, entree, entree_tit, entree_desc):
        return self.render_string("modules/entrees.html", entree=entree, entree_title=entree_tit, entree_desc=entree_desc)

class DessertModule(tornado.web.UIModule):
    def render(self, dessert, dessert_tit, dessert_desc):
        return self.render_string("modules/desserts.html", dessert=dessert, dessert_title=dessert_tit, dessert_desc=dessert_desc)

class BeverageModule(tornado.web.UIModule):
    def render(self, beverage, beverage_tit, beverage_desc):
        return self.render_string("modules/beverages.html", beverage=beverage, beverage_title=beverage_tit, beverage_desc=beverage_desc)

#d is a dictionary
class MenuModule(tornado.web.UIModule):
    def render(self, k1, k2, d):
        return self.render_string("modules/menu_mod.html", title=k1, desc=k2, d=d)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info("listening on :%s" % options.port)
    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()
 