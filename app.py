from flask import Flask, request, jsonify, Response
# Import both classes from book.py
from book import Book, Books

import time
import logging
from logger_config import setup_loggers


app = Flask(__name__)

library = Books()

# Initialize the request counter as a global variable
request_counter = 0

# Set up loggers using the function from logger_config.py
request_logger, books_logger = setup_loggers()

# HELPER FUNCTION
def make_response(result=None, error_message=None, status_code=200):
    if error_message is not None:
        return jsonify({"errorMessage": error_message}), status_code
    return jsonify({"result": result}), status_code

@app.before_request
def start_request_logging():
    global request_counter
    request_counter += 1
    
    # Capture the start time in seconds (with floating-point precision for ms)
    request.start_time = time.time()
    
    # Extract the resource path and uppercase HTTP verb
    resource_name = request.path
    http_verb = request.method.upper()
    
    

    # 1. INFO: Happens before the request is processed
    request_logger.info(f"Incoming request | #{request_counter} | resource: {resource_name} | HTTP Verb {http_verb}", extra={'req_num': request_counter})


@app.after_request
def end_request_logging(response):
    # 2. DEBUG: Happens after the request ends (measures duration)
    if hasattr(request, 'start_time'):
        # Calculate duration: (Current Time - Start Time) * 1000 to get milliseconds
        duration_ms = int((time.time() - request.start_time) * 1000)
        request_logger.debug(f"request #{request_counter} duration: {duration_ms}ms", extra={'req_num': request_counter})
    
    return response

# 1. Health Endpoint (Plain Text OK)
@app.route('/books/health', methods=['GET'])
def health_check():
    return "OK", 200


# 2. Create Book Endpoint
@app.route('/book', methods=['POST'])
def create_book():
    data = request.get_json()
    
  
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    price = data.get('price')
    genres = data.get('genres', [])

   
    response_from_manager = library.add_book(title, author, year, price, genres)
   
    if "error" in response_from_manager:
        books_logger.error(response_from_manager["error"], extra={'req_num': request_counter})  

        return make_response(
            error_message=response_from_manager["error"], 
            status_code=response_from_manager["status"]
        )

    books_logger.info(f"Creating new Book with Title [{title}]", extra={'req_num': request_counter})
    books_logger.debug(f"Currently there are {len(library.books_db) - 1} Books in the system. New Book will be assigned with id {response_from_manager['id']}", extra={'req_num': request_counter})
  
    return make_response(
        result=response_from_manager["id"], 
        status_code=200
    )


@app.route('/books/total', methods=['GET'])
def total_books():
    author_filter = request.args.get('author')
    price_bigger_than = request.args.get('price-bigger-than')
    price_less_than = request.args.get('price-less-than')
    year_bigger_than = request.args.get('year-bigger-than')
    year_less_than = request.args.get('year-less-than')
    genres_filter = request.args.get('genres')

    manager_response = library.get_filtered_books(author_filter, price_bigger_than, price_less_than, year_bigger_than, year_less_than, genres_filter)

    if "error" in manager_response:
        books_logger.error(manager_response["error"], extra={'req_num': request_counter})

        return make_response(
            error_message=manager_response["error"], 
            status_code=manager_response["status"]
        )
    
    matching_books = manager_response["books"]
    total_count = len(matching_books)
    books_logger.info(f"Total Books found for requested filters is {total_count}", extra={'req_num': request_counter})

    return make_response(result=total_count, status_code=200)


@app.route('/books', methods=['GET'])
def books_data():
    author_filter = request.args.get('author')
    price_bigger_than = request.args.get('price-bigger-than')
    price_less_than = request.args.get('price-less-than')
    year_bigger_than = request.args.get('year-bigger-than')
    year_less_than = request.args.get('year-less-than')
    genres_filter = request.args.get('genres')

    manager_response = library.get_filtered_books(author_filter, price_bigger_than, price_less_than, year_bigger_than, year_less_than, genres_filter)

    if "error" in manager_response:
        books_logger.error(manager_response["error"], extra={'req_num': request_counter})

        return make_response(
            error_message=manager_response["error"], 
            status_code=manager_response["status"]
        )
    
    matching_books = manager_response["books"]

    # convert it to json format
    books_as_dicts = [b.to_dict() for b in matching_books]

    # sort by book title
    books_as_dicts.sort(key=lambda book: book['title'].lower())

    books_logger.info(f"Total Books found for requested filters is {len(books_as_dicts)}", extra={'req_num': request_counter})

    return make_response(result=books_as_dicts, status_code=200)

# 5
@app.route('/book', methods=['GET'])
def get_book_by_id():
    book_id = int(request.args.get('id'))
    returned_book = library.get_book_by_id(book_id)

    if returned_book is  None:
        books_logger.error(f"Error: no such Book with id {book_id}", extra={'req_num': request_counter})
        return make_response(error_message= f"Error: no such Book with id {book_id}", status_code= 404)
    
    books_logger.debug(f"Fetching book id {book_id} details", extra={'req_num': request_counter})
    return make_response(result=returned_book.to_dict(), status_code=200)

@app.route('/book', methods=['PUT'])
def change_price_of_book_by_id():
    book_id = int(request.args.get('id'))
    book_price = int(request.args.get('price'))

    if (book_price <= 0):
        books_logger.error(f"Error: price update for Book [{book_id}] must be a positive integer", extra={'req_num': request_counter})
        return make_response(error_message=f"Error: price update for Book [{book_id}] must be a positive integer", status_code= 409)
    
    changed_book_old_price = library.change_book_price_by_id(book_id, book_price)

    if changed_book_old_price is None:
        books_logger.error(f"Error: no such Book with id {book_id}", extra={'req_num': request_counter})
        return make_response(error_message=f"Error: no such Book with id {book_id}", status_code= 404)
    
    books_logger.info(f"Update Book id [{book_id}] price to {book_price}", extra={'req_num': request_counter})
    books_logger.debug(f"Book [{library.get_book_by_id(book_id).title}] price change: {changed_book_old_price} --> {book_price}", extra={'req_num': request_counter})

    return make_response(result=changed_book_old_price, status_code=200)


@app.route('/book', methods=['DELETE'])
def delete_book_by_id():
    book_id = int(request.args.get('id'))
    result, title = library.delete_book(book_id)

    if result is None or title is None:
        books_logger.error(f"Error: no such book with id {book_id}", extra={'req_num': request_counter})
        return make_response(error_message=f"Error: no such book with id {book_id}", status_code=404)
    
    

    books_logger.info(f"Removing book [{title}]", extra={'req_num': request_counter})
    books_logger.debug(f"After removing book [{title}] id: [{book_id}] there are {len(library.books_db)} books in the system", extra={'req_num': request_counter})

    return make_response(result= result, status_code=200)


@app.route('/logs/level', methods=['GET'])
def get_logs_level():
    logger_name = request.args.get('logger-name')

    if logger_name is None:
        return make_response(error_message="Error: missing query parameter 'logger-name'", status_code=400)

    if logger_name == 'request-logger':
        level = (logging.getLevelName(request_logger.level)).upper()
        return jsonify({"Success": level}), 200
    
    elif logger_name == 'books-logger':
        level = logging.getLevelName(books_logger.level).upper()
        return jsonify({"Success": level}), 200
    else:
        return jsonify({"Failure": f"no such logger with name {logger_name}"}), 400


@app.route('/logs/level', methods=['PUT'])
def change_logs_level():
    logger_name = request.args.get('logger-name')
    new_level = request.args.get('logger-level')

    if logger_name is None or new_level is None:
        return jsonify({"Failure": "Error: missing query parameters 'logger-name' and/or 'logger-level'"}), 400

    if new_level.upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        return jsonify({"Failure": f"Error: invalid log level '{new_level}'. Valid levels are DEBUG, INFO, WARNING, ERROR, CRITICAL."}), 400

    level_value = getattr(logging, new_level.upper())

    if logger_name == 'request-logger':
        request_logger.setLevel(level_value)
        return jsonify({"Success": f"Log level for {logger_name} changed to {new_level.upper()}"}), 200
    
    elif logger_name == 'books-logger':
        books_logger.setLevel(level_value)
        return jsonify({"Success": f"Log level for {logger_name} changed to {new_level.upper()}"}), 200
    
    else:
        return jsonify({"Failure": f"Error: no such logger with name {logger_name}"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8574, debug=False)