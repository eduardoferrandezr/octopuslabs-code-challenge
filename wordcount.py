from __future__ import division
import os.path
import tornado.escape
import tornado.web
import tornado.wsgi
from bs4 import BeautifulSoup
import hashlib
import urllib
import re
import operator
import math
from stopwords import stopwords
from google.appengine.ext import db


class WordCount(db.Model):
    id = db.StringProperty(required=True)
    word = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True)


def remove_html_tags(text):
    """
        Removes all the html tags, scripts and styles
    """
    # remove not visible content
    soup = BeautifulSoup(text, 'html.parser')
    texts = soup.findAll(text=True)

    def visible(element):
        if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
            return False
        elif re.match('<!--.*-->', unicode(element)):
            return False
        return True
    visible_texts = filter(visible, texts)

    # remove html tags
    text = " ".join(visible_texts)
    return re.sub(r'<[^>]+>',' ',text)


def extract_words(text):
    """
        Returns a list with the words of the text
    """
    return re.compile('\w+').findall(text)


def count_words(words):
    """
        Receives a list of words and returns a dictionary with the word and its ocurrences in the list
    """

    worddict = dict()
    for word in words:
        word = word.lower()
        if word not in stopwords:
            count = worddict.get(word, 0)
            worddict[word] = count + 1
    return worddict


def top100words(worddict):
    """
        Returns a list of tuples with the 100 most frequent words
    """
    sortedentries = sorted(worddict.items(), key=operator.itemgetter(1))
    # we take the last 100 entries
    return sortedentries[-100:]


def url_wordcount(url):
    """
        Receives an url and returns a tuple with the 100 most frequent words
    """

    f = urllib.urlopen(url)
    text = f.read()
    text = remove_html_tags(text)
    words = extract_words(text)
    worddict = count_words(words)
    wordcount100 = top100words(worddict)
    return wordcount100


def build_wordcloud(wordcount):
    """
        Receives a list of tuples (word, count) and returns a dictionary of word and category
        where category is a value from 1 to 10 where 1 means the least frequent and 10 means the most frequent
    """

    wordcloud = dict()
    max_count = wordcount[-1][1]
    for word, count in wordcount:
        # size goes from 1 to 10 and divides the frequencies in categories
        size = int(math.ceil(10 * count/max_count))
        wordcloud[word] = size
    return wordcloud


def hash_word(word):
    """
        Computes the salted hash for the word
    """

    m = hashlib.sha1()
    m.update(settings.get("salt"))
    m.update(word)
    return m.hexdigest()


def add_to_database(wordcount):
    """
        Adds all the words to the database, with its frequency. If the word doesn't exists, it is inserted
        with its frequency. If the word already exists (its hash matches with a stored one) then the count
        is added to the stored frequency and the row is updated.
    """
    for word, count in wordcount:
        id = hash_word(word)
        obj = db.Query(WordCount).filter("id =", id).get()
        if obj is None:
            obj = WordCount(
                id=id,
                word=word,  # TODO: encrypt with public key
                count=count
            )
        else:
            obj.count += count
        obj.put()


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        wordcloud = {}
        error = None
        url = self.get_argument("url", None)
        if url is not None:
            try:
                wordcount = url_wordcount(url)
                add_to_database(wordcount)
                wordcloud = build_wordcloud(wordcount)
            except IOError:
                error = "The url seems to be wrong!"

        self.render("main.html", url=url, wordcloud=wordcloud, error=error)


class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        counts = db.Query(WordCount).order('-count')
        self.render("admin.html", counts=counts)


settings = {
    "page_title": u"Word Count",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
    "salt": 'this is the salt',
    "rsakeyfile": 'rsakey'
}
application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/admin", AdminHandler)
], **settings)

application = tornado.wsgi.WSGIAdapter(application)

