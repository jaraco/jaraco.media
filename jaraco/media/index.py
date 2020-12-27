import itertools
import os
import urllib
import traceback

import path
import cherrypy
import genshi.template
import httpagentparser

from . import config


class Movie:
    def __init__(self, filename, class_):
        self.class_ = class_
        self.filename = filename

    @property
    def title(self):
        filename = os.path.basename(self.filename)
        return os.path.splitext(filename)[0]

    @property
    def link(self):
        return 'http://www.imdb.com/find?s=all&' + self.search

    @property
    def search(self):
        q = urllib.urlencode(dict(q=self.title))
        return q


class Index:
    def __init__(self, filter=None):
        self.filter = filter

    def get_named_map(self):
        result = {dir.name: dir for dir in config.movies_root.dirs()}
        result[path.Path('')] = config.movies_root
        return result

    def get_media(self, root):
        items = (os.path.join(root, item) for item in os.listdir(root))
        files = itertools.ifilter(os.path.isfile, items)
        mfiles = itertools.ifilter(self.is_media, files)
        return mfiles

    def __iter__(self):
        return itertools.ifilter(self.filter, self.get_all())

    def get_all(self):
        for class_, root in self.get_named_map().items():
            for media in self.get_media(root):
                yield Movie(media, class_)

    @staticmethod
    def is_media(path):
        media_extensions = ('.mp4', '.avi')
        name, ext = os.path.splitext(path)
        return ext in media_extensions


class Site:
    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'application/xhtml+xml'
        template = self.get_template()

        def not_watched(m):
            return m.class_ != 'watched'

        movies = Index(filter=not_watched)
        res = template.generate(movies=movies, title="Movies to Watch")
        return res.render('xml')

    def get_template(self):
        """
        iPhone user agent is
        Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_1_2 like Mac OS X; en-us) \
        AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7D11 Safari/528.16
        """
        agent = httpagentparser.detect(cherrypy.request.headers['User-Agent'])
        is_ios = agent.get('dist', {}).get('name', None) in ['iPhone', 'IPad']
        template_type = 'iweb' if is_ios else ''
        template_text = globals().get(template_type + '_template', default_template)
        template = genshi.template.MarkupTemplate(template_text)
        return template

    @classmethod
    def setup_application(cls, root):
        config = {
            'global': {
                'tools.encode.on': True,
                'tools.encode.encoding': 'utf-8',
                'tools.decode.on': True,
                'tools.trailing_slash.on': True,
            },
        }

        return cherrypy.tree.mount(cls(), root, config)

    @classmethod
    def factory(cls):
        "The entry point for when the ISAPIDLL is triggered"
        try:
            import isapi_wsgi

            return isapi_wsgi.ISAPISimpleHandler(cls.setup_application('/media'))
        except Exception:
            traceback.print_exc()


__ExtensionFactory__ = Site.factory


def handle_isapi():
    "Install or remove the extension to the virtual directory"
    import isapi.install

    params = isapi.install.ISAPIParameters()
    # Setup the virtual directories - this is a list of directories our
    # extension uses - in this case only 1.
    # Each extension has a "script map" - this is the mapping of ISAPI
    # extensions.
    sm = [isapi.install.ScriptMapParams(Extension="*", Flags=0)]
    vd = isapi.install.VirtualDirParameters(
        Server="Default Web Site",
        Name="/media",
        Description="Media Index",
        ScriptMaps=sm,
        ScriptMapUpdate="end",
    )
    params.VirtualDirs = [vd]
    isapi.install.HandleCommandLine(params)


def serve():
    Site.setup_application('/')
    cherrypy.config.update(
        {
            'server.socket_host': '::0',
        }
    )
    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


default_template = """\
<html xmlns="http://www.w3.org/1999/xhtml" \
xmlns:py="http://genshi.edgewall.org/">
    <body>
        <h1 py:content="title">Title</h1>
        <div py:for="movie in movies">
            <a href="${movie.link}" py:content="movie.title">Movie Title</a>
        </div>
    </body>
</html>
"""

iweb_template = """<!DOCTYPE html PUBLIC \
"-//W3C//DTD XHTML 1.0 Strict//EN" \
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:py="http://genshi.edgewall.org/">

<head>
<meta content="yes" name="apple-mobile-web-app-capable" />
<meta content="text/html; charset=iso-8859-1" http-equiv="Content-Type" />
<meta content="minimum-scale=1.0, width=device-width, maximum-scale=0.6667, \
user-scalable=no" name="viewport" />
<link href="/iweb/css/style.css" rel="stylesheet" media="screen" \
type="text/css" />
<script src="/iweb/javascript/functions.js" type="text/javascript"></script>
<title>Title of your page</title>
<meta content="keyword1,keyword2,keyword3" name="keywords" />
<meta content="Description of your page" name="description" />
</head>

<body>
<div id="topbar">
    <div id="title" py:content="title">Title</div>
</div>
<div id="content">

<ul py:for="movie in movies" class="pageitem">
    <li class="menu">
        <a href="imdb:///find?${movie.search}">
            <img alt="Description" src="/iweb/thumbs/video.png" />
            <span class="name">
                <span py:replace="movie.title">Movie Title</span>
                <span class="class" py:if="movie.class_">(\
<span py:replace="movie.class_" />)</span>
            </span>
            <span class="arrow"></span>
        </a>
    </li>
</ul>

</div>
<div id="footer">
    <!-- Support iWebKit by sending us traffic; please keep this footer on your \
page, consider it a thank you for our work :-) -->
    <a class="noeffect" href="http://iwebkit.net">Powered by iWebKit</a></div>

</body>

</html>
"""
