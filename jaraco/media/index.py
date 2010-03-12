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

	def __iter__(self):
		return iter(['A', 'B', 'C'])

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
		index = Index()
		items = [
			'<div><a href="{link}">{title}</a></div>'.format(**vars())
			for title, link in zip(index, index.iter_links())
			]
		return '<html><body>%s</body></html>' % ''.join(items)

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
			return isapi_wsgi.ISAPISimpleHandler(cls.setup_application('/'))
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

