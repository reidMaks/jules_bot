from flask import Flask
from quiz import get_random_question
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
cors = CORS(app)


@app.route("/question")
@cross_origin()
def question():
    return get_random_question().toJSON()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 80))
