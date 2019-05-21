""" AWS News RSS to Chime Chat Room Webhook"""
import os
import time
import ssl
from html.parser import HTMLParser


from pychime import Chime, ChimeException
from rssfeeder import Feeder, Poster

ssl._create_default_https_context = ssl._create_unverified_context

TABLE = 'rssfeedtest2'

class MyHTMLParser(HTMLParser):
    """ Cleans up HTML tags """
    def __init__(self):
        super(MyHTMLParser, self).__init__()
        self._text = []

    def error(self, message):
        return message

    def handle_data(self, data):
        self._text.append(data)

    def get_text(self):
        """ Returns text """
        return ''.join(self._text)

class Post2Chime(Poster):
    """
    Posts the feed to the Chime Chat Room
    """
    def __init__(self, webhook):
        self._webhook = webhook
        super().__init__()

    def post(self, feed):
        """ Post the feed to Chime Chat Room """
        print('Posting {} to chime'.format(feed.id))
        parser = MyHTMLParser()
        chime = Chime(self._webhook)

        parser.feed(feed.summary)
        summary = parser.get_text()
        
        content = '/md '
        content += '**[' + feed.title + '](' + feed.link + ')**\n'
        content += '*' + feed.published + '*\n\000\n'
        content += summary + '\n\000\n'
        
        if len(feed.tags) > 0:
            content += '*category: ' + feed.tags[0]['term'] + '* \n'

        try:
            chime.post(content)
        except ChimeException as err:
            print('Error Code: {}, Error Message: {}'.format(err.code, err.message))
            return False
        return True


def lambda_handler(event, context):
    """
    *Lambda function requires these variables*

    web_hook: required, this is the Chime Chat Room Webhook URL

    feed_urls: required, this is the comma seperated list of
    RSS feed URLs

    table: optional, this is the name of the dynamodb required
    to record already seen news. If not provided a default
    name is used. Check TABLE at the top of this file.

    os.environ['web_hook'] = 'https://....'
    os.environ['feed_urls'] = ['https://....', 'https://...']
    os.environ['table'] = 'rssfeedslog'
    """
    if 'web_hook' in event and 'feed_urls' in event:
        tochime = Post2Chime(event['web_hook'])
        print('Using event data')
        for feed_url in event['feed_urls']:
            table = event['table'] if 'table' in event else TABLE
            r2c = Feeder(feed_url, table, tochime)
            r2c.process_feeds()
    elif 'web_hook' in os.environ and 'feed_urls' in os.environ:
        tochime = Post2Chime(os.environ['web_hook'])
        print('Using environment variables')
        for feed_url in os.environ['feed_urls'].rstrip(',').split(','):
            print('Feed URL: {}'.format(feed_url.strip()))
            table = os.environ['table'] if 'table' in os.environ else TABLE
            r2c = Feeder(feed_url.strip(), table, tochime)
            r2c.process_feeds()
    else:
        print('Provide "web_hook" and "feed_urls" as environment variables or in the event')

#----v---------------------
# Code for local testing
#---------------------v----

class ContextEmulator():
    "Emulates lambda context"
    def __init__(self, lambda_timeout=30):
        self.time = time.time()
        self.lambda_timeout = lambda_timeout * 1000

    def get_remaining_time_in_millis(self):
        "returns remaining time"
        return self.lambda_timeout - (time.time() - self.time) * 1000

if __name__ == "__main__":
    # testing with an event
    EVENT_ = {
        "web_hook" : "https://hooks.chime.aws/incomingwebhooks/" \
        + "09ee788d-db41-4d9a-88c3-ff41315a436b" \
        + "?token=djZneFdFWUF8MXxKSnhVYVFCZFFlUW9IcXRDSVRFQm9oQ2xXS051TzVNTGJ5blUyakNROEZj",
        "feed_urls" : [
            "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
            "https://aws.amazon.com/blogs/mt/feed/"
            ],
        "table" : "rssfeeddev"
    }

    # testing with the environment variables
    EVENT = {}
    os.environ['web_hook'] = "https://hooks.chime.aws/incomingwebhooks/" \
        + "09ee788d-db41-4d9a-88c3-ff41315a436b" \
        + "?token=djZneFdFWUF8MXxKSnhVYVFCZFFlUW9IcXRDSVRFQm9oQ2xXS051TzVNTGJ5blUyakNROEZj"
    os.environ['feed_urls'] = "https://aws.amazon.com/about-aws/whats-new/recent/feed/," \
                            + "https://aws.amazon.com/blogs/mt/feed/"
    #os.environ['table'] = "rssfeeddev"

    CONTEXT = ContextEmulator(lambda_timeout=30)
    lambda_handler(EVENT_, CONTEXT)
