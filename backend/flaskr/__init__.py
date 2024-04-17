import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from starter.backend.models import setup_db, Question, Category

db = SQLAlchemy()
QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resources={r"/app/*":{"origins":"*"}})

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_categories():
    categories = Category.query.all()
    formatted_categories = {}
    for row in categories:
      formatted_categories[row.id] = row.type

    return jsonify({
      'success': True,
      'categories': formatted_categories,
      'total_categories': len(formatted_categories)
    })
  



  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  def convert_questions_to_dict(query):
    questions_list = []

    for row in query:
      current_question = {
        'id': row.id,
        'question': row.question,
        'answer': row.answer,
        'category': row.category,
        'difficulty': row.difficulty
      }
      questions_list.append(current_question)
    return questions_list
  
  @app.route('/questions', methods=['GET'])
  def get_questions():
    #not right method
    if not request.method == 'GET':
      abort(405)
    #get pagination
    try:
      page = request.args.get('page', 1, type=int) 
    except:
      abort(400)
    #query all the questions
    questions = Question.query.all()
    if questions is None:
      abort(404)
    #query all the categories
    categories = Category.query.all()
    if len(categories) == 0:
      abort(404)
    
    try:
      start = (page - 1) * QUESTIONS_PER_PAGE
      end = start + QUESTIONS_PER_PAGE

      formatted_questions = convert_questions_to_dict(questions)

      return jsonify({
        'success': True,
        'questions': formatted_questions[start:end],
        'total_questions':len(formatted_questions),
        'total_categories':len(categories)
      })
    except:
      db.session.rollback()
      abort(422)
    finally:
      db.session.close

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questionsDelete/<int:delete_id>', methods=['DELETE'])
  def del_question(delete_id):
    if not request.method =='DELETE':
      abort(405)
    #parse and return data 
    
    body = request.get_json()
    currentCategory = body['currentCategory']
    question_to_delete = Question.query.get(delete_id)

    if question_to_delete is None:
      abort(404)
    try:
      #delete and refresh
      question_to_delete.deletes()
      questions = convert_questions_to_dict(Question.query.filter_by(category=currentCategory))
      db.session.commit()
      return jsonify({
        'success': True,
        'questions': questions,
        'deleted':question_to_delete,
        'total_questions':len(questions),
      })
    except:
      db.session.rollback()
      abort(422)
    finally:
      db.session.close()

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questionsPost', method=['POST'])
  def post_question():
    if not request.method == 'POST':
      abort(405)
    
    try:
      body = request.get_json()
      data = {
        'question': body['question'],
        'answer': body['answer'],
        'category': body['category'],
        'difficulty':body['difficulty']
      }
    except:
      abort(422)
    
    try:
      question = Question(data)
      question.insert()
      return jsonify({
        'success': True,
        'question': question,
        
      })
    except:
      db.session.rollback()
      abort(422)
    finally:
      db.session.close()





  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    if not request.method == 'POST':
      abort(405)
    
    try:
      body = request.get_json()
      search_term = body['searchTerm']
    
    except:
      abort(422)
      db.session.rollback()
    
    search_query = Question.query.filter(Question.question.ilike('%' + search_term +'%')).all()

    if search_query == []:
      abort(404)
    
    try:
      questions = convert_questions_to_dict(search_query)
      return jsonify({
        'success': True,
        'questions': questions,
        'total_questions': len(questions)
      })
    except:
      abort(422)
      db.session.rollback()

    finally:
      db.session.close()

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_categories(category_id):
    if not request.method == 'GET':
      abort(405)

    filtered_by_category_questions = Question.query.filter(Question.category == category_id).all()
    if len(filtered_by_category_questions) == 0:
      abort(404)
    
    try:
      questions = convert_questions_to_dict(filtered_by_category_questions)
      db.sessions.commit()
      
      return jsonify({
        'success': True,
        'total_questions': len(questions),
        'current_category': questions[0]['category']
      })
    except:
      db.session.rollback()
      abort(422)
    finally:
      db.session.close()

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def quizzes_search():
    
    if not request.method == 'POST':
      abort(405)

    body = request.get_json()
    previous_questions = body['previous_questions']
    quiz_category = body['quiz_category']
    quiz_category_id = quiz_category['id']

    if quiz_category['id'] == 0:
      #not appeared in the previous questions
      filtered_question = Question.query.filter(~Question.id.in_(previous_questions)).first()
    else:
      filtered_question = Question.query.filter(Question.category == quiz_category_id).filter(~Question.id.in_(previous_questions)).first()
    
    try:
      filtered_dict = filtered_question.__dict__
      print(filtered_question)
      current_question = {}
      current_question['question'] = filtered_question['question']
      current_question['answer'] = filtered_question['answer']
      current_question['id'] = filtered_question['id']

      return jsonify({
        'question': current_question
      })

    except:
      db.session.rollback()
      abort(422)
    
    finally:
      db.session.close()

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success':False,
      'error':404,
      'message': 'Resource Not Found'
    }), 404
  
  @app.errorhandler(405)
  def not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'Not Allowed'
    }), 405
  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      "message": "Unprocessable"
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      "message": "Bad Request"
    }), 400



  return app

    