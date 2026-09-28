import os
from pyngrok import ngrok, conf
from sentiment_text import app

conf.get_default().auth_token = os.getenv("NGROK_AUTHTOKEN")
#conf.get_default().auth_token = "2y7mXCOBPrbMNYDxweVvzk6Dnou_3vc3rAyhNd2BGTHhz4dTR"

public_url = ngrok.connect(8000)
print(" * ngrok tunnel:", public_url)

# เรียกใช้งาน Flask app
app.run(port=8000)