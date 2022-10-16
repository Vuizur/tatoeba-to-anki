import sqlite3
# Testing code, ignore

SQL = """
CREATE TABLE sentences_detailed (
	sentence_id INTEGER NOT NULL, 
	lang VARCHAR(4), 
	text VARCHAR(1500), 
	username VARCHAR(20), 
	date_added DATETIME, 
	date_last_modified DATETIME, 
	PRIMARY KEY (sentence_id)
);
CREATE TABLE user_languages (
	lang VARCHAR(4), 
	skill_level INTEGER, 
	username VARCHAR(20), 
	details TEXT, 
	PRIMARY KEY (lang, username)
);
CREATE TABLE sentences_with_audio (
	id INTEGER NOT NULL, 
	sentence_id INTEGER, 
	audio_id INTEGER, 
	username VARCHAR(20), 
	license VARCHAR(50), 
	attribution_url VARCHAR(255), 
	PRIMARY KEY (id)
);
CREATE TABLE tags (
	sentence_id INTEGER NOT NULL, 
	tag_name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (sentence_id, tag_name)
);
CREATE TABLE links (
	sentence_id BIGINT, 
	translation_id BIGINT
);
CREATE INDEX ix_sentence_detailed_sentence_id ON sentences_detailed (sentence_id);
CREATE INDEX ix_sentence_detailed_username ON sentences_detailed (username);
CREATE INDEX ix_sentences_detailed_lang ON sentences_detailed (lang);
CREATE INDEX ix_links_translation_id ON links (translation_id);
CREATE INDEX ix_links_sentence_id ON links (sentence_id);
CREATE INDEX ix_sentences_with_audio_sentence_id ON sentences_with_audio (sentence_id);
CREATE INDEX ix_user_languages_username ON user_languages (username);
CREATE INDEX ix_user_languages_lang ON user_languages (lang);
CREATE INDEX ix_user_languages_skill_level ON user_languages (skill_level);
CREATE INDEX ix_tags_sentence_id ON tags (sentence_id);
CREATE INDEX ix_tags_tag_name ON tags (tag_name);
"""

def query():
	lang_1 = "eng"
	lang_2 = "deu"
	unwanted_tags = ["outdated", "old-fashioned"]
	# Select the sentences that don't have an unwanted tag

	query = """
	SELECT
		sentences_detailed.sentence_id,
		sentences_detailed.text,
		sentences_detailed.username,
		sentences_detailed.date_added,
		sentences_detailed.date_last_modified,
		sentences_with_audio.audio_id,
		sentences_with_audio.license,
		sentences_with_audio.attribution_url,
		tags.tag_name
	FROM sentences_detailed
	LEFT JOIN sentences_with_audio
	ON sentences_detailed.sentence_id = sentences_with_audio.sentence_id
	LEFT JOIN tags
	ON sentences_detailed.sentence_id = tags.sentence_id
	WHERE sentences_detailed.lang = ?
	AND sentences_detailed.sentence_id NOT IN (
		SELECT sentence_id
		FROM tags
		WHERE tag_name IN ({})
	)
	AND sentences_detailed.sentence_id IN (
		SELECT sentence_id
		FROM links
		WHERE translation_id IN (
			SELECT sentence_id
			FROM sentences_detailed
			WHERE lang = ?
		)
	)
	""".format(", ".join("?" * len(unwanted_tags)))

	conn = sqlite3.connect("sentences.db")
	c = conn.cursor()
	c.execute(query, [lang_1] + unwanted_tags + [lang_2])
	return c.fetchall()
	conn = sqlite3.connect("sentences.db")
	c = conn.cursor()
	c.execute(query, (lang_1, lang_2))
	return c.fetchall()
if __name__ == "__main__":
	query()


