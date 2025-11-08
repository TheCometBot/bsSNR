import requests

url = "https://creeper-7rup.onrender.com/websub/callback"
xml = """
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>yt:video:TEST123</id>
    <yt:videoId>TEST123</yt:videoId>
    <yt:channelId>UC_TESTCHANNEL</yt:channelId>
    <title>Testvideo 🎬</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=TEST123"/>
    <author>
      <name>Test Channel</name>
      <uri>https://www.youtube.com/channel/UC_TESTCHANNEL</uri>
    </author>
  </entry>
</feed>
"""

r = requests.post(url, data=xml, headers={"Content-Type": "application/xml"})
print(r.status_code, r.text)
