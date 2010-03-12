import itertools
import os
from glob import glob
import urllib
import cherrypy
import traceback

class Index(object):
	root = r'\\drake\videos\movies'

	def __iter__(self):
		items = (os.path.join(self.root, item) for item in os.listdir(self.root))
		files = itertools.ifilter(os.path.isfile, items)
		mfiles = itertools.ifilter(self.is_media, files)
		names = itertools.imap(self.remove_extension, mfiles)
		return names

	@staticmethod
	def is_media(path):
		media_extensions = ('.mp4', '.avi')
		name, ext = os.path.splitext(path)
		return ext in media_extensions

	@staticmethod
	def remove_extension(filename):
		filename = os.path.basename(filename)
		return os.path.splitext(filename)[0]

	def iter_links(self):
		for title in self:
			q = urllib.urlencode(dict(q=title))
			link = 'http://www.imdb.com/find?s=all&'+q
			yield link

class Site:
	@cherrypy.expose
	def index(self):
		res = self.for_iphone()
		if res: return res
		index = Index()
		items = [
			'<div><a href="{link}">{title}</a></div>'.format(**vars())
			for title, link in zip(index, index.iter_links())
			]
		return '<html><body>%s</body></html>' % ''.join(items)

	def for_iphone(self):
		"""
		iPhone user agent is
		Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_1_2 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7D11 Safari/528.16
		"""
		if 'iPhone' not in cherrypy.request.headers['User-Agent']:
			return
		item_template = """<ul class="pageitem">
	<li class="menu">
		<a href="{link}">
			<img alt="Description" src="/iweb/thumbs/basics.png" />
			<span class="name">{title}</span>
			<span class="arrow"></span>
		</a>
	</li>
</ul>"""
		index = Index()
		items = '\n'.join(
			item_template.format(**vars())
			for title, link in zip(index, index.iter_links())
			)
		title = "Movies to Watch"
		res = iweb_template.format(**vars())
		return res

	@classmethod
	def setup_application(cls, root):
		config = {
			'global': {
				'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
				'tools.decode.on': True,
				'tools.trailing_slash.on': True,
				},
		}

		static_dir = {
			'/static': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': 'static',
				'tools.staticdir.content_types': dict(svg='image/svg+xml'),
			},
			} # ignored for now

		return cherrypy.tree.mount(cls(), root, config)

	@classmethod
	def factory(cls):
		"The entry point for when the ISAPIDLL is triggered"
		try:
			import isapi_wsgi
			return isapi_wsgi.ISAPISimpleHandler(cls.setup_application('/media'))
		except:
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
	sm = [
		isapi.install.ScriptMapParams(Extension="*", Flags=0)
	]
	vd = isapi.install.VirtualDirParameters(
		Server="Default Web Site",
		Name="/media",
		Description = "Media Index",
		ScriptMaps = sm,
		ScriptMapUpdate = "end",
		)
	params.VirtualDirs = [vd]
	isapi.install.HandleCommandLine(params)

def serve():
	Site.setup_application('/')
	cherrypy.config.update({
		'server.socket_host': '::0',
		})
	cherrypy.engine.start()
	cherrypy.engine.block()

iweb_template = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
<meta content="yes" name="apple-mobile-web-app-capable" />
<meta content="text/html; charset=iso-8859-1" http-equiv="Content-Type" />
<meta content="minimum-scale=1.0, width=device-width, maximum-scale=0.6667, user-scalable=no" name="viewport" />
<link href="/iweb/css/style.css" rel="stylesheet" media="screen" type="text/css" />
<script src="/iweb/javascript/functions.js" type="text/javascript"></script>
<title>Title of your page</title>
<meta content="keyword1,keyword2,keyword3" name="keywords" />
<meta content="Description of your page" name="description" />
</head>

<body>
<div id="topbar">
	<div id="title">{title}</div>
</div>
<div id="content">

{items}

</div>
<div id="footer">
	<!-- Support iWebKit by sending us traffic; please keep this footer on your page, consider it a thank you for our work :-) -->
	<a class="noeffect" href="http://iwebkit.net">Powered by iWebKit</a></div>

</body>

</html>
"""
