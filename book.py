class Book:
    def __init__(self, id: int, title: str, author: str, year: int, price: int, genres: list):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.price = price
        self.genres = genres

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "price": self.price,
            "genres": self.genres
        }


class Books:
    def __init__(self):
        self.books_db = {}
        self.next_id = 1
        self.allowed_genres = {"SCI_FI", "NOVEL", "HISTORY", "MANGA", "ROMANCE", "PROFESSIONAL"}

    def add_book(self, title: str, author: str, year: int, price: int, genres: list):
        # 1. Duplicate check (case-insensitive)
        for book in self.books_db.values():
            if book.title.lower() == title.lower():
                return {"error": f"Error: Book with the title [{title}] already exists in the system", "status": 409}

        # 2. Year boundaries check
        if not (1940 <= year <= 2100):
            return {"error": f"Error: Can't create new Book that its year [{year}] is not in the accepted range [1940 -> 2100]", "status": 409}

        # 3. Price validation check
        if price <= 0:
            return {"error": "Error: Can't create new Book with negative price", "status": 409}

        # 4. genres validation
        for g in genres:
            if g not in self.allowed_genres:
                return {"error": "Error: Invalid genre options", "status": 400}

        # If validations pass, construct the individual Book object
        assigned_id = self.next_id
        new_book_obj = Book(assigned_id, title, author, year, price, genres)
        

        self.books_db[assigned_id] = new_book_obj
        
        self.next_id += 1
        
        return {"id": assigned_id, "status": 200}
    

    def get_filtered_books(self, author=None, price_bigger_than=None, price_less_than=None, 
                           year_bigger_than=None, year_less_than=None, genres_csv=None):
        
        # --- 1. VALIDATION CHECKS ---
        try:
            p_bigger = int(price_bigger_than) if price_bigger_than is not None else None
            p_less = int(price_less_than) if price_less_than is not None else None
            y_bigger = int(year_bigger_than) if year_bigger_than is not None else None
            y_less = int(year_less_than) if year_less_than is not None else None
        except ValueError:
            # If casting to an int fails (e.g., someone passed "abc"), return status 400
            return {"error": "Error: Invalid numeric parameters", "status": 400}

        # Validate genres parameter
        target_genres = []
        if genres_csv is not None and genres_csv != "":
            # Split the CSV string by commas into a list of individual genres
            target_genres = genres_csv.split(',')
            
            for g in target_genres:
                if g not in self.allowed_genres:
                    # Case-sensitive check failed or genre doesn't exist
                    return {"error": "Error: Invalid genre options", "status": 400}

        
        filtered_results = list(self.books_db.values())

        # Filter by Author 
        if author is not None:
            filtered_results = [b for b in filtered_results if b.author.lower() == author.lower()]

        # Filter by Price 
        if p_bigger is not None:
            filtered_results = [b for b in filtered_results if b.price >= p_bigger]

        # Filter by Price 
        if p_less is not None:
            filtered_results = [b for b in filtered_results if b.price <= p_less]

        # Filter by Year 
        if y_bigger is not None:
            filtered_results = [b for b in filtered_results if b.year >= y_bigger]

        # Filter by Year 
        if y_less is not None:
            filtered_results = [b for b in filtered_results if b.year <= y_less]

        # Filter by Genres
        if target_genres:
            final_books = []
            for b in filtered_results:
                if set(b.genres).intersection(set(target_genres)):
                    final_books.append(b)
            filtered_results = final_books

        return {"books": filtered_results, "status": 200}
    

    def get_book_by_id (self, book_id):
        book = self.books_db.get(book_id)

        if book is not None:
            return book

        return None
    
    def change_book_price_by_id (self, book_id, price):
        book = self.get_book_by_id(book_id)

        if book is not None and price > 0:
            old_price = book.price
            book.price = price
            return old_price
        
        return None
    

    def delete_book(self, book_id):
        book = self.get_book_by_id(book_id)

        if book is None:
            return None, None
        
        title = book.title
        self.books_db.pop(book_id)
        return len(self.books_db), title