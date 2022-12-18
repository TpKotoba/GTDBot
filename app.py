#!/home/tpkotoba/.local/share/virtualenvs/flask-server-cIrZG_DZ/bin/python

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
	Event, MessageEvent, FollowEvent, UnfollowEvent, 
	TextSendMessage, TemplateSendMessage,
	SourceUser, SourceGroup, SourceRoom,
	Error, 
)

import sys, os
import flask, sqlite3							# HTTP server & database
from params.handle_response import *			# process with the text message
from params.sensitive_settings import *			# sensitive data stored separately
from params.template_for_bot_response import *	# template for the bot response

app = flask.Flask(__name__)
webhook_handler = WebhookHandler(channel_secret)
linebot_api = LineBotApi(channel_access_token)

@app.route('/', methods=['POST'])
def callback():
	'''HTTP server using Flask micro web framework'''

	try:
		x_line_signature = flask.request.headers['X-Line-Signature']
		request_body = flask.request.get_data(as_text=True)
		app.logger.info(f"Request body: {request_body}")
		webhook_handler.handle(request_body, x_line_signature)

	except InvalidSignatureError:
		app.logger.warning(f'Got an unauthorized request.')
		flask.abort(403) # Forbidden
	except LineBotApiError as err:
		if isinstance(err.error, Error): # dump the exception detail
			app.logger.exception(f'Got exception from LINE bot API: {err.message}')
			for error_message in err.error.details:
				app.logger.exception(f'> {error_message.property}: {error_message.message}')
		flask.abort(500) # Internal Server Error
	except:
		app.logger.exception(f'Got an unexpected exception.')
		flask.abort(500)

	return 'OK'

@webhook_handler.add(FollowEvent)
def handle_follow(event: FollowEvent):

	linebot_api.reply_message(event.reply_token, TemplateSendMessage(alt_text=template_for_follow.alt_text, template=template_for_follow.template))

	if isinstance(event.source, SourceUser):
		app.logger.info(f"Followed by {event.source.user_id}.")
	elif isinstance(event.source, SourceRoom):
		app.logger.info(f"Entered the room {event.source.room_id}.")
	elif isinstance(event.source, SourceGroup):
		app.logger.info(f"Entered the group {event.source.group_id}.")

	return

def get_sender_id(event: Event) -> str:
	'''get the sender_id from the event'''

	if isinstance(event.source, SourceUser):
		sender_id = str(event.source.user_id)
	elif isinstance(event.source, SourceGroup):
		sender_id = str(event.source.group_id)
	elif isinstance(event.source, SourceRoom):
		sender_id = str(event.source.room_id)
	else:
		sender_id = ''
		app.logger.exception(f'The source of the event is not in [SourceUser, SourceGroup, SourceRoom].')
		raise AttributeError()
	
	return sender_id


@webhook_handler.add(UnfollowEvent)
def handle_unfollow(event: UnfollowEvent):
	'''remove from db'''

	with sqlite3.connect(db_name) as db:

		try:
			sender_id = get_sender_id(event)
			app.logger.info(f"{sender_id} unfollowed.")
			cursor = db.cursor()
			cursor.execute(f"""DELETE FROM quests WHERE sender_id = \'{sender_id}\'""")
			db.commit()

		except AttributeError:
			app.logger.exception(f"Got an exception while fetching the sender id.")
		except:
			app.logger.exception(f"Got an unexpected exception when deleting from the database.")

	return

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
	'''main function for processing the user input'''

	if event.message.text.strip()[0] == '/':
		'''A command-type input.'''
		response_for_command(event)
	else:
		'''A message-type inpput.'''
		response_for_quest(event)

	return

if __name__ == '__main__':

	if sys.argv[1:]:
		if sys.argv[1] == '--rm':
			os.system(f'rm -rf {db_name}')
			print('db removed')

	'''database initialize'''
	with sqlite3.connect(db_name) as db:

		try:
			cursor = db.cursor()
			cursor.execute(f'''CREATE TABLE quests(timestamp TEXT PRIMARY KEY NOT NULL, sender_id TEXT NOT NULL, message TEXT, type TEXT);''')
			app.logger.info('Create a new database.')
			db.commit()

		except sqlite3.OperationalError:
			app.logger.info('Use an existing database.')
		except:
			app.logger.exception('Exception when creating database.')
	
	linebot_api.push_message(admin_id, TextSendMessage(text='server fired.'))	# check we are puppeting the right bot
	app.run(debug=False, port=5000)