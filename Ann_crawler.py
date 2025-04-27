import praw

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
#print(subreddit)  # Print the name of the subreddit
top_posts = subreddit.top(limit=10)  # Get the top 10 posts from the subreddit
for post in top_posts:
    print(f"Title: {post.title}")  # Print the title of each post
    #print(f"Author: {post.author}")  # Print the author of each post
    #print(f"Score: {post.score}")  # Print the score of each post
    #print(f"URL: {post.url}")  # Print the URL of each post
    #print(f"Created: {post.created_utc}")  # Print the creation time of each post
    #print(f"Comments: {post.num_comments}")  # Print the number of comments on each post
    print("-" * 80)  # Separator for readability