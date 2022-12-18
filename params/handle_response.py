from linebot.models import (
	MessageEvent, FollowEvent, UnfollowEvent, 
	TextSendMessage, TemplateSendMessage,
	TextMessage,
	ButtonsTemplate, MessageAction,
)
from params.sensitive_settings import *
from params.template_for_bot_response import *

from app import linebot_api, app

import sqlite3

positive = ['ok', 'on', '1', 'True', 'true']
negative = ['no', 'off', '0', 'False', 'false']

def update_link(timestamp, sender_id: str, message: str):
	with sqlite3.connect(db_name) as db:
		cursor = db.cursor()
		try:
			'''TODO: defense for the injection'''
			cursor.execute(f'''INSERT INTO quests (timestamp, sender_id, message, type) VALUES (\'{timestamp}\',\'{sender_id}\',\'{message}\', \'link\')''')
			return_value = 'I got it'
		except:
			app.logger.exception('Exception when inserting quests.')
			return_value = 'Error: could not update quest.'
		finally:
			db.commit()
	return return_value

def update_quest(timestamp, sender_id: str, message: str):
	with sqlite3.connect(db_name) as db:
		cursor = db.cursor()
		try:
			'''TODO: defense for the injection'''
			cursor.execute(f'''INSERT INTO quests (timestamp, sender_id, message, type) VALUES ('{timestamp}','{sender_id}','{message}', \'quest\')''')
			return_value = 'I got it.'
		except:
			app.logger.exception('Exception when inserting quests.')
			return_value = 'Error: could not update quest.'
		finally:
			db.commit()
	return return_value

def response_for_command(event: MessageEvent):

	user_input = event.message.text.strip().split()
	user_command = user_input[0]
	user_params = ' '.join(user_input[1:])

	if user_command == '/new':
		if user_params:
			reply = update_quest(event.timestamp, event.source.sender_id, user_params)
			linebot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
		else:
			linebot_api.reply_message(event.reply_token, TextSendMessage(text='Just type your quest in the chat, I will record it.'))


	elif user_command == '/help':
		linebot_api.reply_message(event.reply_token, TemplateSendMessage(alt_text=template_for_help.alt_text, template=template_for_help.template))
	
	elif user_command == '/list':
		template_for_list = return_template_for_list(event)
		linebot_api.reply_message(event.reply_token, TemplateSendMessage(alt_text=template_for_list.alt_text, template=template_for_list.template))
	
	elif user_command == '/link':
		template_for_link = return_template_for_link(event)
		linebot_api.reply_message(event.reply_token, TemplateSendMessage(alt_text=template_for_link.alt_text, template=template_for_link.template))
	
	elif user_command == '/clear':
		remove_from_database(event)
		linebot_api.reply_message(event.reply_token, TextSendMessage(text='List cleared.'))

	elif user_command in ['/notify']:
		linebot_api.reply_message(event.reply_token, TextSendMessage(text='Not implemented yet.'))

	elif user_command == '/finish':
		pass
	else:
		pass
	return

def response_for_quest(event: MessageEvent):
	if event.message.text.startswith('http://'):
		reply = update_link(event.timestamp, event.source.sender_id, event.message.text.strip())
	elif event.message.text.startswith('https://'):
		reply = update_link(event.timestamp, event.source.sender_id, event.message.text.strip())
	else:
		reply = update_quest(event.timestamp, event.source.sender_id, event.message.text.strip())
	
	linebot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
