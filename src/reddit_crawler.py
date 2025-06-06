import praw
import json
import os
import time
import random
from dotenv import load_dotenv
from datetime import datetime
from prawcore.exceptions import TooManyRequests, ServerError, ResponseException

# -------Config-----

with open("subreddits.txt", 'r') as f:  # Corrected file path
    SUBREDDITS = [line.strip() for line in f if line.strip()] 

POSTS_PER_SUBREDDIT = 1000  # Max posts per subreddit
MAX_COMMENTS_PER_POST = 50  # Max comments per post
BATCH_SIZE = 10  # Posts per API call
REQUEST_DELAY = 3.0  # Base delay between requests (seconds)
DATA_DIR = "collections"
CHECKPOINT_FILE = os.path.join(DATA_DIR, "crawler_checkpoint.json")

# ===== RATE-LIMITED PRAW SETUP =====
class RateLimitedSession(praw.reddit.Requestor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_request = 0
        self.rate_limit = 28  # Conservative limit (30/min)

    def request(self, *args, **kwargs):
        elapsed = time.time() - self.last_request
        required_delay = 60 / self.rate_limit
        if elapsed < required_delay:
            sleep_time = required_delay - elapsed + random.uniform(0, 0.3)
            time.sleep(sleep_time)
        
        self.last_request = time.time()
        return super().request(*args, **kwargs)


# ----- load api keys----
load_dotenv()
reddit_instance = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
    # username and password optional, only needed for private comments
)


#  ------ data processing

def process_comment(comment):
    """Convert comment to serializable format with nested structure"""
    return {
        "id": comment.id,
        "author": str(comment.author) if comment.author else "[deleted]",
        "body": comment.body,
        "score": comment.score,
        "created_utc": comment.created_utc,
        "depth": comment.depth,
        "replies": [process_comment(reply) for reply in comment.replies][:5]  # Max 5 replies per comment
    }

def get_post_comments(post):
    """Fetch comments with nested structure and error handling"""
    try:
        post.comment_limit = MAX_COMMENTS_PER_POST
        post.comments.replace_more(limit=1)  # Expand 1 level of "more comments"
        return [process_comment(comment) for comment in post.comments][:MAX_COMMENTS_PER_POST]
    except Exception as e:
        print(f"Error fetching comments for {post.id}: {str(e)}")
        return []

def load_checkpoint():
    """Load crawling progress"""
    try:
        with open(CHECKPOINT_FILE, "r") as f:
            data = json.load(f)
            return {
                "current_subreddit": data.get("current_subreddit", 0),
                "processed_posts": data.get("processed_posts", 0),
                "last_post_id": data.get("last_post_id", None)
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current_subreddit": 0, "processed_posts": 0, "last_post_id": None}

def save_checkpoint(state):
    """Save crawling progress"""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)




# ===== CORE CRAWLING FUNCTION =====
def crawl_subreddit(subreddit_name, start_after=None, processed_count=0):
    """Main crawling function with comments and error handling"""
    count = 1 # file number
    filename = os.path.join(DATA_DIR, f"{subreddit_name}_{count}.json")
    os.makedirs(DATA_DIR, exist_ok=True)

    # Load existing data
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    subreddit = reddit_instance.subreddit(subreddit_name)
    posts_collected = 0
    after = start_after

    # create set to hold unique ids
    processed_post_ids = set()
    mb = 0 # initialize mb to 0

    while posts_collected < (POSTS_PER_SUBREDDIT - processed_count):
        try:
            # Fetch posts batch
            params = {"after": after} if after else None
            posts = list(subreddit.new(limit=BATCH_SIZE, params=params))
            if not posts:
                break

            batch = []
            for post in posts:
                # check for duplicates
                if post.id in processed_post_ids:
                    print(f"Duplicate post found: {post.id}. Skipping.")
                    continue   # if duplicate, do not crawl skip loop

                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author),
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "url": post.url,
                    "num_comments": post.num_comments,
                    "text": post.selftext,
                    "comments": get_post_comments(post)
                }
                batch.append(post_data)

                # add id to set
                processed_post_ids.add(post.id)
            
            if mb > 10:
                base_name, ext = os.path.splitext(filename)
                count += 1
                filename = os.path.join(DATA_DIR,f"{subreddit_name}_{count}.json")
                print(f"Current file size exceeded 10 MB. Writing to new file: {filename}")

               
                with open(filename, "w") as f:
                    json.dump(batch, f, indent=2)  
                    
                existing_data = []
            else:
                # Save batch to the existing file
                existing_data.extend(batch)
                with open(filename, "w") as f:
                    json.dump(existing_data, f, indent=2)

            file_size = os.path.getsize(filename)
            mb = file_size / 1000000 # file size in megabytes

            # Update checkpoint
            save_checkpoint({
                "current_subreddit": SUBREDDITS.index(subreddit_name),
                "processed_posts": processed_count + len(batch),
                "last_post_id": batch[-1]["id"]
            })

            print(f"Saved {len(batch)} posts (+comments) from r/{subreddit_name}")
            print(f"Remaining API requests: {reddit_instance.auth.limits['remaining']}")
            print(f"File size: {mb} MB")

            # Prepare next batch
            after = "t3_" + batch[-1]["id"]
            posts_collected += len(batch)
            time.sleep(REQUEST_DELAY + random.uniform(0, 1))

        except TooManyRequests as e:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
        except (ServerError, ResponseException) as e:
            print(f"API error: {str(e)}. Waiting 30s...")
            time.sleep(30)
        except Exception as e:
            print(f"Unexpected error: {str(e)}. Waiting 60s...")
            time.sleep(60)

    return True

# ===== MAIN EXECUTION =====
def main():
    checkpoint = load_checkpoint()
    start_idx = checkpoint["current_subreddit"]
    processed = checkpoint["processed_posts"]
    last_id = checkpoint["last_post_id"]

    for i in range(start_idx, len(SUBREDDITS)):
        subreddit = SUBREDDITS[i]
        print(f"\n=== Crawling r/{subreddit} ===")

        success = crawl_subreddit(
            subreddit,
            start_after=last_id if i == start_idx else None,
            processed_count=processed if i == start_idx else 0
        )

        if success:
            # Reset checkpoint for next subreddit
            save_checkpoint({
                "current_subreddit": i + 1,
                "processed_posts": 0,
                "last_post_id": None
            })
            processed = 0
            last_id = None

if __name__ == "__main__":
    main()
