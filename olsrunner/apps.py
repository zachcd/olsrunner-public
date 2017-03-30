from django.apps import AppConfig
from cassiopeia import riotapi

class OlsrunnerConfig(AppConfig):
	name = 'olsrunner'
	def ready(self):
		riotapi.set_region("NA")
		riotapi.set_api_key("APIKEY")
		riotapi.get_champions()
		print("got champs")
