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

print(reddit_instance.user.me())  # Print the username of the authenticated user