import tornado.options
import tornado.httpserver
import tornado.ioloop

import logging
import os

import app.main
import app.courses
import app.affairs
import app.dining
import app.athletics
import app.housing
import app.uem
import app.docs
import app.auth


class Application(tornado.web.Application):
    def __init__(self):
        logging.getLogger().setLevel(logging.DEBUG)

        app_settings = {
            'debug': "dev",
            "xsrf_cookies" : False,
            "cookie_secret" : "32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
            "static_path" : os.path.join(os.path.dirname(__file__), "static"),
            "autoescape" : None,
            "login_url" : "http://data.adicu.com/login",
        }

        handlers = [
            (r"/$", app.main.MainHandler),
            (r"/ping$", PingHandler),
            (r"/courses$", app.courses.CoursesHandler),
            (r"/dining$", app.dining.DiningHandler),
            (r"/uem$", app.uem.UemHandler),
            (r"/affairs$", app.affairs.AffairsHandler),
            (r"/affairs/([^/]+)", app.affairs.AffairsHandler),
            (r"/athletics$", app.athletics.athleticsHandler),
            (r"/housing/rooms$", app.housing.RoomHandler),
            (r"/housing/buildings$", app.housing.BuildingHandler),
            (r"/docs$", app.main.MainHandler),
            (r"/docs/([^/]+)", app.docs.DocsHandler),
            (r"/login$", app.auth.LoginHandler),
            (r"/logout$", app.auth.LogoutHandler),
            (r"/profile$", app.main.ProfileHandler),

        ]
        debug = True
        tornado.web.Application.__init__(self, handlers, **app_settings)

class PingHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish('OK')
    def head(self):
        self.finish('OK')


if __name__ == "__main__":
    # this port should be unique system wide; all ports used should be listed in ~/services.py
    tornado.options.define("port", default=int(os.environ["PORT"]), help="Listen on port", type=int)
    tornado.options.parse_command_line()
    logging.info("starting app on 0.0.0.0:%d" % tornado.options.options.port)
    http_server = tornado.httpserver.HTTPServer(request_callback=Application())
    http_server.listen(tornado.options.options.port, address="0.0.0.0")
    tornado.ioloop.IOLoop.instance().start()
