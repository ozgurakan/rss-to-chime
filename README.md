# rss-to-chime

Posts RSS Feeds to Chime Room

## Usage

Install these python packages
```
$ pip install rssfeeder
$ pip install pychime
```

Configure your lambda function and pass there environment variables. You can set these on the AWS Lambda Console.

```
web_hook // chime web hook url
feed_urls // url1, url2, url3
table // dynamodb table name, it will be created automatically
```
