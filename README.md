# slack-message-pipe

This project began as a clone of [ErikKalkoken / slackchannel2pdf](https://github.com/ErikKalkoken/slackchannel2pdf). Our initial goal is to format a Slack channel's message history nicely as JSON for consumption by an LLM. We have to do quite a bit of cleanup of the JSON that comes back from Slack's API to make it simple, self contained, and easy to interpret. 

Our approach is to insert an intermediate language of simple python data structures in between the Slack history processing and the PDF generation. Then we will add an adapter to go from that intermediate language to JSON when desired.