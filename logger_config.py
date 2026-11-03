import os
import logging
from datetime import datetime

# 1. Ensure the logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# 2. Custom Formatter that references app.py's global request counter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Format date-time with milliseconds as dd-mm-yyyy hh:mm:ss.sss
        dt = datetime.fromtimestamp(record.created)
        date_time_str = dt.strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        
        # Import the counter directly from app to get its live value
        req_num = getattr(record, 'req_num', 0)
        
        # Build the exact string format required by the tester
        return f"{date_time_str} {record.levelname}: {record.getMessage()} | request #{req_num}"

def setup_loggers():
    # --- SETUP REQUEST-LOGGER ---
    request_logger = logging.getLogger('request-logger')
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False

    req_file_handler = logging.FileHandler('logs/requests.log')
    req_file_handler.setFormatter(CustomFormatter())
    request_logger.addHandler(req_file_handler)

    #req_stream_handler = logging.StreamHandler()
    #req_stream_handler.setFormatter(CustomFormatter())
    #request_logger.addHandler(req_stream_handler)

    # --- SETUP BOOKS-LOGGER ---
    books_logger = logging.getLogger('books-logger')
    books_logger.setLevel(logging.INFO)
    books_logger.propagate = False

    books_file_handler = logging.FileHandler('logs/books.log')
    books_file_handler.setFormatter(CustomFormatter())
    books_logger.addHandler(books_file_handler)
    
    return request_logger, books_logger