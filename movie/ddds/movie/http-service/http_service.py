# -*- coding: utf-8 -*-

import json
from os import getenv

from flask import Flask, request
from jinja2 import Environment
import structlog

from logger import configure_stdout_logging

from urllib.request import Request, urlopen
import requests
import http.client
import mimetypes
import string
import webbrowser
from imdb import IMDb

def setup_logger():
    logger = structlog.get_logger(__name__)
    try:
        log_level = getenv("LOG_LEVEL", default="INFO")
        configure_stdout_logging(log_level)
        return logger
    except BaseException:
        logger.exception("exception during logger setup")
        raise


logger = setup_logger()
app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending error response to TDM", response=response)
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending query response to TDM", response=response)
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
     """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending multiple query response to TDM", response=response)
    return response


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending validator response to TDM", response=response)
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
     """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending dummy query response to TDM", response=response)
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
     }
   }
   """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    logger.info("Sending successful action response to TDM", response=response)
    return response

key = "k_z0tnk13w"

def get_data(keyword):
    keyword = keyword.strip().lower()
    keyword = keyword.translate(str.maketrans('', '', string.punctuation))
    keyword = keyword.replace(' ','-')
    ## ALT 1
    conn = http.client.HTTPSConnection("imdb-api.com", 443)
    url = f"/API/Keyword/{key}/{keyword}"
    print("url::: ", url)
    payload = ''
    headers = {}
    conn.request("GET", url, payload, headers)
    res = conn.getresponse()
    data = res.read()

    # ALT 2
    # url = f"https://imdb-api.com/API/Keyword/k_rzd6lii8/{keyword}"
    # payload = {}
    # headers= {}
    # response = requests.request("GET", url, headers=headers, data = payload, verify=False)
    # data = response.text.encode('utf8')

    # # ALT 3 (Throws INTERNAL SERVER ERROR 500)
    # url = f"https://imdb-api.com/API/Keyword/k_rzd6lii8/{keyword}"
    # request = Request(url)
    # response = urlopen(request)
    # data = response.read()

    return json.loads(data)

def get_plot(title):
    title = title.lower()
    title = title.translate(str.maketrans('', '', string.punctuation))
    title_edited = title.replace(' ','%20')
    ## ALT 1
    conn = http.client.HTTPSConnection("imdb-api.com", 443)
    url = f"/en/API/SearchTitle/{key}/{title_edited}"
    payload = ''
    headers = {}
    conn.request("GET", url, payload, headers)
    res = conn.getresponse()
    data = res.read()
    json_data = json.loads(data)
    print("reading json_data: ", json_data)
    movie_id = json_data['results'][0]['id']
    movie_id = str(movie_id)
    conn = http.client.HTTPSConnection("imdb-api.com", 443)
    url = f"/en/API/Trailer/{key}/{movie_id}"
    payload = ''
    headers = {}
    conn.request("GET", url, payload, headers)
    res = conn.getresponse()
    data = res.read()

    return json.loads(data)

def get_similar(title):
  # https://imdb-api.com/API/title/tt1323594/k_rzd6lii8/keywords/
  title = title.lower()
  title = title.translate(str.maketrans('', '', string.punctuation))
  title_edited = title.replace(' ','%20')
  ## ALT 1
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/SearchTitle/{key}/{title_edited}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  print("reading json_data: ", json_data)
  movie_id = json_data['results'][0]['id']
  movie_id = str(movie_id)
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/API/title/{movie_id}/{key}/keywords"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  return json.loads(data)


@app.route("/movie", methods=['POST'])
def movie():
  payload = request.get_json()
  keyword = payload["context"]["facts"]["keyword_to_search"]["grammar_entry"]
  data = get_data(keyword)
  temp = data['items'][0]['title']
  tempstr = str(temp)
  return query_response(value=tempstr, grammar_entry=None)

@app.route("/plot", methods=['POST'])
def plot():
  payload = request.get_json()
  title = payload["context"]["facts"]["title_to_search"]["grammar_entry"]
  data = get_plot(title)
  temp = data['videoDescription']
  tempstr = str(temp)
  return query_response(value=tempstr, grammar_entry=None)


@app.route("/similar_movie", methods=['POST'])
def similar_movie():
  payload = request.get_json()
  title = payload["context"]["facts"]["title_to_search"]["grammar_entry"]
  data = get_similar(title)
  temp = data['similars'][0]['title']
  tempstr = str(temp)
  print(f"similar movie: {tempstr}.")
  return query_response(value=tempstr, grammar_entry=None)

