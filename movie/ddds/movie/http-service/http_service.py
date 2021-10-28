# -*- coding: utf-8 -*-

import json
import os
from os import getenv
import sys
from flask import Flask, request
from jinja2 import Environment
import structlog

from logger import configure_stdout_logging

from urllib.request import Request, urlopen
import requests
import http.client
import mimetypes
import string
import csv as c

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

key = "k_rzd6lii8" #k_rzd6lii8, k_p6wl5oj9

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
    print("data::: ", data)

    # ALT 2
    # url = f"https://imdb-api.com/API/Keyword/{key}/{keyword}"
    # payload = {}
    # headers= {}
    # response = requests.request("GET", url, headers=headers, data = payload, verify=False)
    # data = response.text.encode('utf8')

    # # ALT 3 (Throws INTERNAL SERVER ERROR 500)
    # url = f"https://imdb-api.com/API/Keyword/{key}/{keyword}"
    # request = Request(url)
    # response = urlopen(request)
    # data = response.read()

    return json.loads(data)

def prepare_string_for_url(title):
  title = title.lower()
  title = title.translate(str.maketrans('', '', string.punctuation))
  title = title.replace(' ','%20') # handle whitespaces in URL
  return title

def get_id(title):
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/SearchTitle/{key}/{title}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  movie_id = json_data['results'][0]['id']
  movie_id = str(movie_id)
  return movie_id

def get_plot(title):
  title_edited = prepare_string_for_url(title)
  ## Get ID given Title
  movie_id = get_id(title_edited)
  ## Get Plot given ID
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/Trailer/{key}/{movie_id}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  movie_plot = json_data['videoDescription']
  plot_string = title + " talks about " + str(movie_plot)
  return plot_string

def get_genre(title):
  title_edited = prepare_string_for_url(title)
  ## Get ID given Title
  movie_id = get_id(title_edited)
  ## Get Genre given ID
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/Title/{key}/{movie_id}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  movie_genre = json_data['genres']
  genre_string = title + " is classified as " + str(movie_genre)
  return genre_string

def get_fullcast(title):
  title_edited = prepare_string_for_url(title)
  ## Get ID given Title
  movie_id = get_id(title_edited)
  ## Get Genre given ID
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/Title/{key}/{movie_id}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  movie_cast = json_data['stars']
  fullcast_string = "The stars of "+ title +" are: " + str(movie_cast)
  return fullcast_string

def get_rating(title):
  title_edited = prepare_string_for_url(title)
  ## Get ID given Title
  movie_id = get_id(title_edited)
  ## Get Rating given ID
  conn = http.client.HTTPSConnection("imdb-api.com", 443)
  url = f"/en/API/Title/{key}/{movie_id}"
  payload = ''
  headers = {}
  conn.request("GET", url, payload, headers)
  res = conn.getresponse()
  data = res.read()
  json_data = json.loads(data)
  print("json_data: ", json_data)
  imdb_rating = json_data['imDbRating']
  metacritic_rating = json_data['metacriticRating']
  rating_votes = json_data['imDbRatingVotes']
  rating_string = "For a total of " + str(rating_votes) + " votes, the IMDB rating is " + str(imdb_rating) + " and the metacritic rating is " + str(metacritic_rating)
  return rating_string


def get_similar(title):
  title_edited = prepare_string_for_url(title)
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

@app.route("/info", methods=['POST'])
def info():
  payload = request.get_json()
  title = payload["context"]["facts"]["title_to_search"]["grammar_entry"]
  info_type = payload["context"]["facts"]["info_type"]["grammar_entry"]
  info_type = info_type.lower()
  info_type = info_type.replace(' ','')
  info_type = info_type.translate(str.maketrans('', '', string.punctuation))
  if info_type == "rating":
    temp = get_rating(title)
  elif info_type == "fullcast":
    temp = get_fullcast(title)
  elif info_type == "genre":
    temp = get_genre(title)
  else:
    temp = get_plot(title)
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
  poster = data['similars'][0]['image']
  # Edit visual output
  path_to_json = "visual_output/visual_output.json"
  fileObject = open(path_to_json, "r")
  jsonContent = fileObject.read()
  try:
    jsondata = json.loads(jsonContent)
  except ValueError:  # includes simplejson.decoder.JSONDecodeError
    print('Decoding JSON has failed')
  # Update visual_output files
  with open(path_to_json, 'w') as visual_output_file:
    print("visual_output_file", str(jsondata))
    jsondata[1]["semantic_expression"] = "answer(similar_movie(\"" + tempstr + "\"))"
    jsondata[1]["visual_information"][0]["value"] = poster
    print("dumping ...")
    json.dump(jsondata, visual_output_file)
  # #Sync with couchdb (Throws error)
  # import visual_output.update_visual_output_db as uvo
  # uvo.main()
  print("done. sending query ... ")
  return query_response(value=tempstr, grammar_entry=None)

@app.route("/mlist_given_feeling", methods=['POST'])
def mlist_given_feeling():
  payload = request.get_json()
  feeling = payload["context"]["facts"]["feeling_to_search"]["grammar_entry"]

  feeling_folder = "data/"
  feeling = feeling.lower()
  feeling = feeling.translate(str.maketrans('', '', string.punctuation))
  print("feeling: ", feeling)
  mad_list = ["mad", "angry", "furious", "annoyed"]
  happy_list = ["good", "glad", "happy", "excited"]
  sad_list = ["bad", "sad", "depressed", "upset"]
  if feeling in sad_list:
    feeling_path = feeling_folder + "sad.csv"
  elif feeling in mad_list:
    feeling_path = feeling_folder + "mad.csv"
  else:
    feeling_path = feeling_folder + "happy.csv"

  with open(feeling_path, "r") as ffile:
    csv = c.reader(ffile, delimiter = "\t")
    list_str = ""
    for row in csv:
      list_str = list_str + ", " + str(row[0])
  return query_response(value=list_str, grammar_entry=None)