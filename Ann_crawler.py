import praw
import time, datetime # pytz just for clarity
import json

username_of_me = "PresentTangelo7958"
password_of_me = "Valar Morghulis"
client_id = "wJH5oSZpN6eCUaygK5cH2w"
client_secret = "NxoJVNdg6q3wrtk2QWUlaBvH4_zhQA"
#user_agent = "your_user_agent"
#subreddit_name = "your_subreddit_name"

# Initialize the Reddit client
reddit_instance = praw.Reddit(
    username=username_of_me,
    password=password_of_me,
    client_id=client_id,
    client_secret=client_secret,
    user_agent="clean_crawler by /u/PresentTangelo7958",
)

#print(reddit_instance.user.me())  # Print the username of the authenticated user
subreddit = reddit_instance.subreddit("literature")
TARGET_SUBS = ["literature"]
#print(subreddit)  # Print the name of the subreddit
#top_posts = subreddit.top(limit=10)  
# Get the top 10 posts from the subreddit, time rage = all time
#for post in top_posts:
    #print(f"Title: {post.title}")  # Print the title of each post
    #print(f"Author: {post.author}")  # Print the author of each post
    #print(f"Score: {post.score}")  # Print the score of each post
    #print(f"URL: {post.url}")  # Print the URL of each post
    #print(f"Created: {post.created_utc}")  # Print the creation time of each post
    #print(f"Comments: {post.num_comments}")  # Print the number of comments on each post
    #print("-" * 80)  # Separator for readability


def respectful_stream(subs, limit=1):
    for post in reddit_instance.subreddit("+".join(subs)).top(time_filter="month", limit=50):
        # Safe lookup: if the attribute is absent, default to None
        hint = getattr(post, "post_hint", None)

        # keep only text posts that actually have content
        if post.is_self and hint is None and post.selftext.strip():
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

        time.sleep(0.5)                         # polite crawl
        rl = reddit_instance.auth.limits
        if rl["remaining"] is not None and rl["remaining"] < 2:
            wait = rl["reset_timestamp"] - datetime.datetime.now(
                datetime.timezone.utc).timestamp()
            if wait > 0:
                print(f"Rate limit hit – sleeping {int(wait)+2}s")
                time.sleep(wait + 2)


with open("clean_posts.jsonl", "w", encoding="utf-8") as f:
    for item in respectful_stream(TARGET_SUBS, limit=2000):
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
