from turtle import pos
from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask import Markup
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'reds209ndsldssdsljdsldsdsljdsldksdksdsdfsfsfsfis'
#session.init_app(app)

positive = 0
negative = 0
neutral = 0


@app.route('/')
def home():
    if not session.get('searched'):
        return render_template('search.html')
    else:
        labels = ["Positive", "Negative", "Neutral"]
        global positive
        global negative
        global neutral
        values = [positive, negative, neutral]
        colors = ["#8bc34a", "#ff5252", "#9e9e9e"]
        session['searched'] = False
        return render_template('chart.html', set=values)


@app.route('/search', methods=['POST'])
def do_search():
    if request.form['search_query'] == '':
        flash('Search Queary cannot be empty!')
        session['searched'] = False
    import tweepy
    auth = tweepy.OAuthHandler("3l3wecTeXmebsRlxhGDPuqZad", "fXgsM1M0MLf3SNL1KyzXNFpzvyY3ALHl8vdh1Rci12vXFNbfqa")
    auth.set_access_token("1256196895-SsCsAisekhWZzSKuJ0XPky0NI3GcXPH8o5mjAeI", "ULFbfZGV7gClesQNZrOQxOFV6xfupcJpdcBDdtJC7Njxr")
    api = tweepy.API(auth)
    # Error handling
    if (not api):
        print("Problem Connecting to API")

    # inputs for counts taken
    #hash_tag = request.form['search_query']
    hash_tag=request.form['search_query']
    number = 100

    tweetsPerQry = 100  # this is the max the API permits
    sinceId = None

    max_id = -1
    data = None

    dataset = []
    tweetCount = 0
    print("Downloading max {0} tweets".format(number))
    while tweetCount < number:
        try:
            if (max_id <= 0):
                if (not sinceId):
                    new_tweets = api.search_tweets(q=hash_tag, count=tweetsPerQry, tweet_mode='extended', lang='en')
                    tweetCount += len(new_tweets)
                    print("Downloaded {0} tweets".format(tweetCount))
                else:
                    new_tweets = api.search(q=hash_tag, count=tweetsPerQry,
                                            since_id=sinceId, tweet_mode='extended', lang='en')
                    print("here 2")
            else:
                if (not sinceId):
                    new_tweets = api.search(q=hash_tag, count=tweetsPerQry,
                                            max_id=str(max_id - 1), tweet_mode='extended', lang='en')
                    print("here 3")
                else:
                    new_tweets = api.search(q=hash_tag, count=tweetsPerQry,
                                            max_id=str(max_id - 1),
                                            since_id=sinceId, tweet_mode='extended', lang='en')
                    print("here 4")
                if not new_tweets:
                    print("No more tweets found")
                    break

            # print(new_tweets)

            tweets = new_tweets
            for tweet in tweets:
                dataset.append(tweet.full_text)
            #data += pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['Tweets'])
            tweetCount += len(new_tweets)
            print("Downloaded {0} tweets".format(tweetCount))
            max_id = new_tweets[-1].id
        except Exception as e:
            print(str(e))
            break
    print(len(dataset))
    tweets = dataset
    import re
    remove_mentions = r"@\S+"
    remove_links = r"https?:\S+"
    remove_non_word_char = r"[^A-Za-z0-9 ]+"
    remove_html_entities = r"\&\w+;"

    def clean_tweets(tweets):
        cleaned_tweets = []
        for tweet in tweets:
            tweet = re.sub(remove_mentions, '', str(tweet).lower()).strip()
            tweet = re.sub(remove_links, '', str(tweet).lower()).strip()
            tweet = re.sub(remove_non_word_char, '', str(tweet).lower()).strip()
            tweet = re.sub(remove_html_entities, '', str(tweet).lower()).strip()
            
            cleaned_tweets.append(tweet)
        
        return cleaned_tweets

    import pickle
    with open('./tokenizer-clean.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)

    from keras.preprocessing.sequence import pad_sequences
    from keras.preprocessing.text import Tokenizer
    import tensorflow as tf

    model = tf.keras.models.load_model('./senan-7_no_extra.h5')

    tweets = clean_tweets(tweets)
    tweets = pad_sequences(tokenizer.texts_to_sequences(tweets),maxlen = 30)

    predictions = model.predict(tweets)
    global positive
    positive = 0
    global negative
    negative = 0
    global neutral
    neutral = 0

    for prediction in predictions:
        if prediction <= 0.4:
            negative += 1
        elif prediction >= 0.6:
            positive += 1
        else:
            neutral += 1
    session['searched'] = True
    print(positive)
    return home()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)
