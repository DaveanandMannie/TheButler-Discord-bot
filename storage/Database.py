import sqlite3
import logging

#TODO: figure out to search based on user name and nick name
class StackNotFoundError(Exception):
	"""Custom Exception for no stack found"""
	pass


class Manager:
	def __init__(self, *, database_name: str) -> None:
		"""Initializes connection with database and creators a cursor"""
		self.database_name: str = database_name
		self.connection: sqlite3.Connection = sqlite3.connect(database_name)
		self.cursor: sqlite3.Cursor = self.connection.cursor()
		self.logger: logging.Logger = logging.getLogger(__name__)
		logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

	def build_from_schema(self) -> None:
		"""Builds required tables for the Butlers"""
		try:
			self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS Users (
					id INTEGER PRIMARY KEY UNIQUE ,
					username TEXT NOT NULL,
					nickname TEXT,
					discord_id INTEGER NOT NULL UNIQUE 
					)
				''')
			self.logger.info('User table created successfully')
			self.connection.commit()
		except sqlite3.Error as error:
			self.logger.error(f'Error creating User table: {error}')
			self.connection.rollback()
			raise

		try:
			self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS MentionGroups (
					id INTEGER PRIMARY KEY, 
					name TEXT UNIQUE
					)
				''')
			self.logger.info('MentionGroups table created successfully')
			self.connection.commit()
		except sqlite3.Error as error:
			self.logger.error(f'Error creating MentionGroups table: {error}')
			self.connection.rollback()
			raise

		try:
			self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS UserMentionGroups (
					user_id INTEGER,
					group_id INTEGER,
					FOREIGN KEY(user_id) REFERENCES Users(id),
					FOREIGN KEY(group_id) REFERENCES MentionGroups(id), 
					PRIMARY KEY(user_id, group_id)
					)
				''')
			self.connection.commit()
			self.logger.info('UserMentionGroups table created successfully')
		except sqlite3.Error as error:
			self.logger.error(f'Error creating UserMentionGroups: {error}')
			raise

	def add_user(self, *, username: str, nickname: str, discord_id: int) -> None:
		""" Adds user to the database with their discord id, nickname, and username """
		try:
			self.cursor.execute(
				'INSERT INTO users (username, nickname, discord_id) VALUES (?, ?, ?)',
				(username, nickname, discord_id)
			)
			self.connection.commit()
			self.logger.info('Success user: {username} added')
		except sqlite3.Error as error:
			self.logger.error(f'Failed to add user: {error}')
			self.connection.rollback()
			raise

	def create_mention_group(self, *, mention_group_name: str) -> None:
		"""Creates a new mention group """
		try:
			self.cursor.execute('INSERT INTO MentionGroups(name) VALUES (?)', (mention_group_name,))
			self.connection.commit()
			self.logger.info(f'Success group: {mention_group_name} created')
		except sqlite3.Error as error:
			self.logger.error(f'Failed to create group: {error}')
			raise

	def get_mention_names(self) -> list[str]:
		"""Returns a list of Mention Group tuples [(name,)]"""
		try:
			self.cursor.execute('SELECT name FROM MentionGroups')
			mention_groups_temp: list = self.cursor.fetchall()
			mention_groups: list[str] = [i[0] for i in mention_groups_temp]
			return mention_groups
		except sqlite3.Error as error:
			self.logger.error(f'An error occurred: {error}')
			raise

	def get_all_users(self) -> list[tuple[int, str, str, int]]:
		"""Returns a list of user tuples [(id, username, nickname, discord ID )]"""
		try:
			self.cursor.execute('SELECT * FROM Users')
			users: list[tuple[int, str, str, int]] = self.cursor.fetchall()
			return users
		except sqlite3.Error as error:
			self.logger.error(f'An error occurred: {error}')
			raise

	def add_to_mention_group(self, user_id: int, group_id: int):
		"""Adds a user to a mention group"""
		try:
			self.cursor.execute(
				'''insert into UserMentionGroups (user_id, group_id) VALUES (?,?)''',
				(user_id, group_id)
			)
			self.connection.commit()
		except sqlite3.Error as error:
			self.logger.error(f'An error occurred: {error}')
			raise

	def get_mention_group_data(self, *, name: str) -> tuple[int, str] | None:
		"""Returns mention group tuple(id, name)"""
		self.cursor.execute('''SELECT * FROM MentionGroups WHERE name = ?''', (name,))
		return self.cursor.fetchone()

	def get_member_data(self, *, name: str) -> tuple[int, str, str, int] | None:
		"""Returns User data tuple(id, username, nickname, discord id)"""
		self.cursor.execute(
			'''SELECT * FROM Users WHERE username = ? OR nickname = ?''',
			(name, name)
		)
		return self.cursor.fetchone()

	def get_stack_members_ids(self, *, stack_name: str) -> list[int]:
		try:
			self.cursor.execute(
				'''
				SELECT discord_id FROM Users
				JOIN UserMentionGroups on Users.id = UserMentionGroups.user_id
				JOIN MentionGroups on UserMentionGroups.group_id = MentionGroups.id
				WHERE MentionGroups.name = ?
				''',
				(stack_name,)
			)
			rows = self.cursor.fetchall()
			if not rows:
				raise StackNotFoundError
			discord_ids = [row[0] for row in rows]
			return discord_ids
		except sqlite3.Error as error:
			print(error)
			raise

	def get_stack_members(self, *, stack_name: str) -> list[str]:
		"""returns a list of users who belong to the specified mention group."""
		try:
			self.cursor.execute(
				'''
				SELECT username FROM Users
				JOIN UserMentionGroups ON Users.id = UserMentionGroups.user_id 
				JOIN MentionGroups ON UserMentionGroups.group_id = MentionGroups.id 
				WHERE MentionGroups.name = ?
				''',
				(stack_name,))
			rows = self.cursor.fetchall()
			if not rows:
				raise StackNotFoundError
			users = [row[0] for row in rows]
			return users
		except sqlite3.Error as error:
			self.logger.error(f'an error occurred: {error}')
			raise
