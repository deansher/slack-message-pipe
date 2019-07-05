import os
from channel_exporter import ChannelExporter

def main():
    exporter = ChannelExporter(os.environ['SLACK_TOKEN'])
    exporter.run("G7LULJD46")    

if __name__ == '__main__':
    main()
