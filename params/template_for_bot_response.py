from linebot.models import ButtonsTemplate, MessageAction

import sqlite3
from params.sensitive_settings import db_name
from app import app, get_sender_id

class template_for_bot_response:
	'''alt_text + template'''
	def __init__(self, _alt_text: str = '', _template: ButtonsTemplate=ButtonsTemplate()) -> None:
		self.alt_text = _alt_text
		self.template = _template

actions_for_commands = [
	MessageAction(label='New quest', text='/new'),
	MessageAction(label='Quest list', text='/list'), 
	MessageAction(label='Link list', text='/link'), 
	MessageAction(label='Clear list', text='/clear'), 
]

template_for_help = template_for_bot_response(
	_alt_text='''<code>
I have the following commands:
/new: add a new quest.
/list: fetch the quest list.
/link: fetch the link list.
/clear: clear the quest list.
</code>''', 
	_template=ButtonsTemplate(
		text='I have the following commands:', 
		title='HELP', 
		actions=actions_for_commands
	)
)

template_for_follow = template_for_bot_response(
	_alt_text='Welcome! I am GTD bot.',
	_template=ButtonsTemplate(
		text='I am GTD bot.', 
		title='WELCOME', 
		actions=actions_for_commands, 
	)
)

def get_link(sender_id: str) -> list:

	with sqlite3.connect(db_name) as db:

		try:
			cursor = db.cursor()
			quest_list = list(cursor.execute(f"""SELECT message FROM quests WHERE type == \'link\' AND sender_id = \'{sender_id}\'"""))
			db.commit()

		except:
			quest_list = list()
			app.logger.warning('Exception when listing the quest.')
	
	return quest_list


def get_quest(sender_id: str) -> list:

	with sqlite3.connect(db_name) as db:

		try:
			cursor = db.cursor()
			quest_list = list(cursor.execute(f"""SELECT message FROM quests WHERE sender_id == \'{sender_id}\'"""))
			db.commit()

		except:
			quest_list = list()
			app.logger.warning('Exception when listing the quest.')

	return quest_list

def remove_from_database(_event):

	with sqlite3.connect(db_name) as db:

		try:
			sender_id = get_sender_id(_event)
			cursor = db.cursor()
			cursor.execute(f"""DELETE FROM quests WHERE sender_id = \'{sender_id}\'""")
			db.commit()

		except AttributeError:
			app.logger.exception(f"Got an exception while fetching the sender id.")
		except:
			app.logger.exception(f"Got an unexpected exception when deleting from the database.")

	return

def return_template_for_link(_event):
	link_list = get_link(get_sender_id(_event))
	if link_list:
		link_mes = '\n'.join([f'[{link[0]:02d}] {link[1][0]}' for link in enumerate(link_list)])
		'''TODO: if text_length > 160 then compress the quest list.'''
		return template_for_bot_response(
			_alt_text=f'Quest list:\n{link_mes}', 
			_template=ButtonsTemplate(
				text=link_mes, 
				actions=actions_for_commands, 
			)
		)
	else:
		link_mes = f'Link is clear. Try to add one!'
		return template_for_bot_response(_alt_text=link_mes, _template=ButtonsTemplate(text=link_mes, actions=actions_for_commands))


def return_template_for_list(_event):
	quest_list = get_quest(get_sender_id(_event))
	if quest_list:
		quest_mes = '\n'.join([f'[{quest[0]:02d}] {quest[1][0]}' for quest in enumerate(quest_list)])
		'''TODO: if text_length > 160 then compress the quest list.'''
		return template_for_bot_response(
			_alt_text=f'Quest list:\n{quest_mes}', 
			_template=ButtonsTemplate(
				text=quest_mes, 
				# title='QUEST LIST', 
				actions=actions_for_commands, 
			)
		)
	else:
		quest_mes = f'Quest is clear. Try to add one!'
		return template_for_bot_response(_alt_text=quest_mes, _template=ButtonsTemplate(text=quest_mes, actions=actions_for_commands))
