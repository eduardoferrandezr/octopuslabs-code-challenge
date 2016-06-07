from __future__ import division
import os.path
import tornado.escape
import tornado.web
import tornado.wsgi
from bs4 import BeautifulSoup
import urllib
import re
import operator
import math
from stopwords import stopwords

from google.appengine.ext import db


class Entry(db.Model):
    """A single blog entry."""
    author = db.UserProperty()
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    body_source = db.TextProperty(required=True)
    html = db.TextProperty(required=True)
    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)


def remove_html_tags(text):
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
    return re.compile('\w+').findall(text)


def count_words(words):
    worddict = dict()
    for word in words:
        word = word.lower()
        if word not in stopwords:
            count = worddict.get(word, 0)
            worddict[word] = count + 1
    return worddict


def top100words(worddict):
    sortedentries = sorted(worddict.items(), key=operator.itemgetter(1))
    # we take the last 100 entries
    return sortedentries[-100:]


def url_wordcount(url):
    f = urllib.urlopen(url)
    text = f.read()
    text = remove_html_tags(text)
    words = extract_words(text)
    worddict = count_words(words)
    wordcount100 = top100words(worddict)
    return wordcount100

def build_wordcloud(wordcount):
    wordcloud = dict()
    max_count = wordcount[-1][1]
    for word, count in wordcount:
        size = int(math.ceil(10 * count/max_count))
        wordcloud[word] = size
    return wordcloud



class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        url = self.get_argument("url", None)
        if url is not None:
            wordcount = url_wordcount(url)
            wordcloud = build_wordcloud(wordcount)
        else:
            wordcloud = {}
        self.render("main.html", url=url, wordcloud=wordcloud)


settings = {
    "page_title": u"Word Count",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.web.Application([
    (r"/", HomeHandler),
], **settings)

application = tornado.wsgi.WSGIAdapter(application)
