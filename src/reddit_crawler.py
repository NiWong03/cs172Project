import praw
import time, datetime # pytz just for clarity
import json
import os
from dotenv import load_dotenv


# Initialize the Reddit client
load_dotenv()


reddit_instance = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)

# Read subreddits from the file
with open("subreddits.txt", "r") as file:
    TARGET_SUBS = [line.strip() for line in file if line.strip()]

print("Querying subreddits:", TARGET_SUBS)

def respectful_stream(subs, limit=1):
    for sub in subs:
        print(f"Querying subreddit: {sub}")
        for post in reddit_instance.subreddit(sub).top(time_filter="month", limit=50):
            # Safe lookup: if the attribute is absent, default to None
            hint = getattr(post, "post_hint", None)

            # keep only text posts that actually have content
            if post.is_self and hint is None and post.selftext.strip():
                print(f"Crawling post from subreddit: {post.subreddit.display_name}")
                yield {
                    "id":          post.id,
                    "title":       post.title,
                    "body":        post.selftext,
                    "created_utc": post.created_utc,
                    "author":      str(post.author),
                    "subreddit":   post.subreddit.display_name,
                    "score":       post.score,
                    "num_comments": post.num_comments,
                }

            time.sleep(0.5)  # polite crawl
            rl = reddit_instance.auth.limits
            if rl["remaining"] is not None and rl["remaining"] < 2:
                wait = rl["reset_timestamp"] - datetime.datetime.now(
                    datetime.timezone.utc).timestamp()
                if wait > 0:
                    print(f"Rate limit hit – sleeping {int(wait)+2}s")
                    time.sleep(wait + 2)


with open("collections/clean_posts.jsonl", "w", encoding="utf-8") as f:
    for item in respectful_stream(TARGET_SUBS, limit=1000):
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
