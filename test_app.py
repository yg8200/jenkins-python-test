import pytest
import json
from app import app
from book import Books, Book


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def fresh_library():
    """Reset the library before each test."""
    from app import library
    library.books_db = {}
    library.next_id = 1
    return library


class TestHealthEndpoint:
    def test_health_check(self, client):
        """Test the health endpoint returns OK."""
        response = client.get('/books/health')
        assert response.status_code == 200
        assert response.data == b'OK'


class TestCreateBook:
    def test_create_book_success(self, client, fresh_library):
        """Test creating a book successfully."""
        payload = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'year': 1945,
            'price': 10,
            'genres': ['NOVEL']
        }
        response = client.post('/book', json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result' in data
        assert data['result'] == 1  # First book gets ID 1

    def test_create_book_duplicate_title(self, client, fresh_library):
        """Test that duplicate titles are rejected."""
        payload = {
            'title': 'The Great Gatsby',
            'author': 'Author 1',
            'year': 2000,
            'price': 15,
            'genres': ['NOVEL']
        }
        client.post('/book', json=payload)
        response = client.post('/book', json=payload)
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'errorMessage' in data

    def test_create_book_year_out_of_range(self, client, fresh_library):
        """Test year validation (1940-2100)."""
        payload = {
            'title': 'Old Book',
            'author': 'Ancient Author',
            'year': 1900,
            'price': 5,
            'genres': ['HISTORY']
        }
        response = client.post('/book', json=payload)
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'errorMessage' in data

    def test_create_book_negative_price(self, client, fresh_library):
        """Test that negative prices are rejected."""
        payload = {
            'title': 'Book',
            'author': 'Author',
            'year': 2000,
            'price': -10,
            'genres': ['NOVEL']
        }
        response = client.post('/book', json=payload)
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'errorMessage' in data

    def test_create_book_invalid_genre(self, client, fresh_library):
        """Test invalid genre rejection."""
        payload = {
            'title': 'Book',
            'author': 'Author',
            'year': 2000,
            'price': 10,
            'genres': ['INVALID_GENRE']
        }
        response = client.post('/book', json=payload)
        assert response.status_code == 400

    


class TestGetBookById:
    def test_get_book_by_id_success(self, client, fresh_library):
        """Test retrieving a book by ID."""
        payload = {
            'title': 'Test Book',
            'author': 'Test Author',
            'year': 2000,
            'price': 20,
            'genres': ['NOVEL', 'ROMANCE']
        }
        create_response = client.post('/book', json=payload)
        book_id = json.loads(create_response.data)['result']
        
        response = client.get(f'/book?id={book_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result']['title'] == 'Test Book'
        assert data['result']['id'] == book_id

    def test_get_book_by_id_not_found(self, client, fresh_library):
        """Test retrieving a non-existent book."""
        response = client.get('/book?id=999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'errorMessage' in data


class TestUpdateBookPrice:
    def test_change_price_success(self, client, fresh_library):
        """Test updating a book's price."""
        payload = {
            'title': 'Expensive Book',
            'author': 'Rich Author',
            'year': 2020,
            'price': 50,
            'genres': ['PROFESSIONAL']
        }
        create_response = client.post('/book', json=payload)
        book_id = json.loads(create_response.data)['result']
        
        response = client.put(f'/book?id={book_id}&price=30')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 50  # Old price returned

    def test_change_price_negative(self, client, fresh_library):
        """Test that negative prices are rejected on update."""
        payload = {
            'title': 'Book',
            'author': 'Author',
            'year': 2000,
            'price': 10,
            'genres': ['NOVEL']
        }
        create_response = client.post('/book', json=payload)
        book_id = json.loads(create_response.data)['result']
        
        response = client.put(f'/book?id={book_id}&price=-5')
        assert response.status_code == 409

    def test_change_price_not_found(self, client, fresh_library):
        """Test updating price on non-existent book."""
        response = client.put('/book?id=999&price=25')
        assert response.status_code == 404


class TestDeleteBook:
    def test_delete_book_success(self, client, fresh_library):
        """Test deleting a book."""
        payload = {
            'title': 'Deletable Book',
            'author': 'Anonymous',
            'year': 2010,
            'price': 8,
            'genres': ['MANGA']
        }
        create_response = client.post('/book', json=payload)
        book_id = json.loads(create_response.data)['result']
        
        response = client.delete(f'/book?id={book_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 0  # No books left

    def test_delete_book_not_found(self, client, fresh_library):
        """Test deleting a non-existent book."""
        response = client.delete('/book?id=999')
        assert response.status_code == 404 # Current code always returns 200


class TestTotalBooks:
    def test_total_books_no_filter(self, client, fresh_library):
        """Test getting total count of all books."""
        # Add multiple books
        for i in range(3):
            payload = {
                'title': f'Book {i}',
                'author': 'Author',
                'year': 2000 + i,
                'price': 10 + i,
                'genres': ['NOVEL']
            }
            client.post('/book', json=payload)
        
        response = client.get('/books/total')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 3

    def test_total_books_filter_by_author(self, client, fresh_library):
        """Test filtering total count by author."""
        for i in range(2):
            payload = {
                'title': f'Book by Alice {i}',
                'author': 'Alice',
                'year': 2000,
                'price': 10,
                'genres': ['NOVEL']
            }
            client.post('/book', json=payload)
        
        payload = {
            'title': 'Book by Bob',
            'author': 'Bob',
            'year': 2000,
            'price': 10,
            'genres': ['NOVEL']
        }
        client.post('/book', json=payload)
        
        response = client.get('/books/total?author=Alice')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 2

    def test_total_books_filter_by_price(self, client, fresh_library):
        """Test filtering total count by price range."""
        for price in [5, 15, 25, 35]:
            payload = {
                'title': f'Book Price {price}',
                'author': 'Author',
                'year': 2000,
                'price': price,
                'genres': ['NOVEL']
            }
            client.post('/book', json=payload)
        
        response = client.get('/books/total?price-bigger-than=10&price-less-than=30')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result'] == 2  # Books with price 15 and 25

    def test_total_books_invalid_filter(self, client, fresh_library):
        """Test invalid numeric filter."""
        response = client.get('/books/total?price-bigger-than=abc')
        assert response.status_code == 400


class TestGetBooks:
    def test_get_books_all(self, client, fresh_library):
        """Test retrieving all books."""
        for i in range(2):
            payload = {
                'title': f'Sorted Book {i}',
                'author': 'Author',
                'year': 2000,
                'price': 10,
                'genres': ['NOVEL']
            }
            client.post('/book', json=payload)
        
        response = client.get('/books')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['result']) == 2

    def test_get_books_sorted_by_title(self, client, fresh_library):
        """Test that books are sorted by title."""
        titles = ['Zebra', 'Apple', 'Mango']
        for title in titles:
            payload = {
                'title': title,
                'author': 'Author',
                'year': 2000,
                'price': 10,
                'genres': ['NOVEL']
            }
            client.post('/book', json=payload)
        
        response = client.get('/books')
        data = json.loads(response.data)
        result_titles = [book['title'] for book in data['result']]
        assert result_titles == ['Apple', 'Mango', 'Zebra']

    def test_get_books_filter_by_genres(self, client, fresh_library):
        """Test filtering books by genres."""
        payload1 = {
            'title': 'SciFi Book',
            'author': 'Author',
            'year': 2000,
            'price': 10,
            'genres': ['SCI_FI']
        }
        payload2 = {
            'title': 'Novel Book',
            'author': 'Author',
            'year': 2000,
            'price': 10,
            'genres': ['NOVEL']
        }
        client.post('/book', json=payload1)
        client.post('/book', json=payload2)
        
        response = client.get('/books?genres=SCI_FI')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['result']) == 1
        assert data['result'][0]['title'] == 'SciFi Book'


class TestBookClass:
    def test_book_to_dict(self):
        """Test Book.to_dict() method."""
        book = Book(1, 'Test', 'Author', 2000, 15, ['NOVEL'])
        book_dict = book.to_dict()
        assert book_dict['id'] == 1
        assert book_dict['title'] == 'Test'
        assert book_dict['price'] == 15


class TestBooksClass:
    def test_books_initialization(self):
        """Test Books class initialization."""
        books = Books()
        assert len(books.books_db) == 0
        assert books.next_id == 1
        assert len(books.allowed_genres) == 6

    def test_add_book_basic(self):
        """Test adding a book to Books class."""
        books = Books()
        result = books.add_book('Title', 'Author', 2000, 20, ['NOVEL'])
        assert 'id' in result
        assert result['id'] == 1
        assert len(books.books_db) == 1

    def test_get_book_by_id(self):
        """Test retrieving book from Books class."""
        books = Books()
        books.add_book('Title', 'Author', 2000, 20, ['NOVEL'])
        book = books.get_book_by_id(1)
        assert book is not None
        assert book.title == 'Title'

    def test_change_book_price(self):
        """Test changing book price."""
        books = Books()
        books.add_book('Title', 'Author', 2000, 20, ['NOVEL'])
        old_price = books.change_book_price_by_id(1, 25)
        assert old_price == 20
        book = books.get_book_by_id(1)
        assert book.price == 25

    def test_delete_book(self):
        """Test deleting a book."""
        books = Books()
        books.add_book('Title', 'Author', 2000, 20, ['NOVEL'])
        result = books.delete_book(1)
        assert result == (0, 'Title')  # No books left, title of deleted book returned
        assert books.get_book_by_id(1) is None

    # adding a failed test to see it in jenkins
    def test_add_book_invalid_genre(self):
        books = Books()
        with pytest.raises(ValueError):
            books.add_book('Title', 'Author', 2000, 20, ['INVALID_GENRE'])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
