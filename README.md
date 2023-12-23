# Fantasy Football
This was my draft board that I used data scraping for. It is currently unoperational due to websites changing their format as it was for the draft not for the in season.

This will be back up and running to be improved in the Summer of 2024!

Here is a video that was sent in for a job interview dealing with fantasy football to give a quick visualization
https://www.loom.com/share/3506544998e04f54b67b45a67ba075bc

# Purpose
I have always made a draft board by printing out and highlighting. I ran into the problem of on draft day the board looked different from when I printed it out

This is because the ADP (average draft position) changes daily on these sites that run fantasy football

I made this application that on every run fetches the most recent positions experts and websites have players ranked at to see where the value is of picking a player

# Information about main
In here I was able to start the streamlit application and apply highlights to columns based on if an expert had a player ranked above or below the application being used such as ESPN

I make requests from every different website and combined them to make a pandas dataframe column which I then displayed

Technology used: Requests, Pandas, Streamlit

# Information about Variables.py
This was the variables that were stored in order to make requests to these websites

These were accessed by main.py

# Thank you for viewing!
Any questions email micheal.callahan@icloud.com or message me at my LinkedIn of https://www.linkedin.com/in/micheal-callahan-668b3224a/
