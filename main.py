from fastapi import FastAPI, HTTPException, Header, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional
import random
import string
import requests
import re


app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class Tasks(BaseModel):
    id: Optional[int] = None
    title: str
    description: str


class Author(BaseModel):
    name: str
    birth_year: int
    nationality: str


class Details(BaseModel):
    genre: str
    publication_year: int
    language: str
    pages: int
    isbn: str


class Books(BaseModel):
    id: Optional[int] = None
    title: str
    author: Author
    details: Details


expected_credentials = {
    "username": "querty",
    "password": "querty123"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


exp_token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

tasks = [
    Tasks(id=1, title="Finish report", description="Complete project report"),
    Tasks(id=2, title="Finish the book",
          description="Finish reading the new novel and start another one"),
    Tasks(id=3, title="Exercise", description="Go to the gym for cardio"),
]


books = [
    Books(
        id=1,
        title="The Great Gatsby",
        author=Author(name="F. Scott Fitzgerald",
                      birth_year=1896, nationality="American"),
        details=Details(genre="Classic", publication_year=1925,
                        language="English", pages=218, isbn="978-0-7432-7356-5")
    ),
    Books(
        id=2,
        title="Pride and Prejudice",
        author=Author(name="Jane Austen", birth_year=1775,
                      nationality="British"),
        details=Details(genre="Classic", publication_year=1813,
                        language="English", pages=279, isbn="978-1-59308-273-5")
    ),
    Books(
        id=3,
        title="To Kill a Mockingbird",
        author=Author(name="Harper Lee", birth_year=1926,
                      nationality="American"),
        details=Details(genre="Classic", publication_year=1960,
                        language="English", pages=281, isbn="978-0-06-112008-4")
    )
]


@app.get('/')
def reset_data():
    global tasks, books
    tasks = [
        Tasks(id=1, title="Finish report", description="Complete project report"),
        Tasks(id=2, title="Finish the book", description="Finish reading the new novel and start another one"),
        Tasks(id=3, title="Exercise", description="Go to the gym for cardio"),
    ]

    books = [
        Books(
            id=1,
            title="The Great Gatsby",
            author=Author(name="F. Scott Fitzgerald", birth_year=1896, nationality="American"),
            details=Details(genre="Classic", publication_year=1925, language="English", pages=218, isbn="978-0-7432-7356-5")
        ), Books(
        id=2,
        title="Pride and Prejudice",
        author=Author(name="Jane Austen", birth_year=1775,
                      nationality="British"),
        details=Details(genre="Classic", publication_year=1813,
                        language="English", pages=279, isbn="978-1-59308-273-5")
    ),
    Books(
        id=3,
        title="To Kill a Mockingbird",
        author=Author(name="Harper Lee", birth_year=1926,
                      nationality="American"),
        details=Details(genre="Classic", publication_year=1960,
                        language="English", pages=281, isbn="978-0-06-112008-4")
    )
    ]

    return {"message": "This is your Task and Books Management API. Proceed to '/tasks' to view the tasks or /books to view the books."}


@app.post('/authenticate')
@limiter.limit("2/minute")
def authenticate_user(credentials: dict, request: Request):
    provided_username = credentials.get('username')
    provided_password = credentials.get('password')
    if provided_username == expected_credentials['username'] and provided_password == expected_credentials['password']:
        return {"message": "Authentication successful", "token": exp_token}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# get all tasks
@app.get('/tasks')
# @limiter.limit("5/minute")
def get_tasks(request: Request):
    return tasks

# get tasks by id
@app.get('/tasks/{task_id}')
@limiter.limit("3/minute")
def get_by_id(task_id: int, request: Request):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

# post tasks
@app.post('/tasks')
@limiter.limit("5/minute")
def add_tasks(task: Tasks, request: Request):
    if task.id is None:
        new_id = len(tasks) + 1  # Generate an id based on the current number of tasks
        task.id = new_id

    if any(taskItem.id == task.id for taskItem in tasks):
        raise HTTPException(
            status_code=400, detail="Task with the same id already exists")

    tasks.append(task)
    return {"message": f"Task '{task.title}' added successfully", "task": task}



# update tasks
@app.put('/tasks/{task_id}')
@limiter.limit("4/minute")
def update_by_id(task_id: int, updated_task: Tasks, request: Request):
    task = next((task for task in tasks if task.id == task_id), None)
    if task:
        for task in tasks:
            if task.id == task_id:
                task.title = updated_task.title
                task.description = updated_task.description
        return {"message": f"Task updated successfully", "task": updated_task}
    raise HTTPException(status_code=404, detail="No task with the provided id")


# delete by id
@app.delete('/tasks/{task_id}')
@limiter.limit("3/minute")
def delete_by_id(task_id: int, request: Request, Authorization: str = Header()):
    if Authorization == "Bearer " + exp_token:
        task = next((task for task in tasks if task.id == task_id), None)
        if task:
            for task in tasks:
                if task.id == task_id:
                    tasks.remove(task)
                    return {"message": f"Authorization successful and task deleted successfully"}
            return {"message": f"Could not find task with the provided Id"}
        else:
            return {"message": f"Invalid task ID"}
    raise HTTPException(status_code=404, detail="Authorization not successful")

# get books
@app.get('/books')
@limiter.limit("5/minute")
def get_tasks(request: Request):
    return books

# get books by id
@app.get('/books/{book_id}')
@limiter.limit("3/minute")
def get_by_id(book_id: int, request: Request):
    for book in books:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")

# post books
@app.post('/books')
@limiter.limit("5/minute")
def add_books(book: Books, request: Request):
    if book.id is None:
        new_id = len(books) + 1  # Generate an id based on the current number of books
        book.id = new_id

    if any(bookItem.id == book.id for bookItem in books):
        raise HTTPException(
            status_code=400, detail="Book with the same id already exists")
    books.append(book)
    return {"message": f"Book '{book.title}' added successfully", "book": book}


# update books
@app.put('/books/{book_id}')
@limiter.limit("4/minute")
def update_by_id(book_id: int, updated_book: Books, request: Request):
    book = next((book for book in books if book.id == book_id), None)
    if book:
        for existing_book in books:
            if existing_book.id == book_id:
                existing_book.title = updated_book.title
                existing_book.author = updated_book.author
                existing_book.details = updated_book.details
        return {"message": f"Book updated successfully", "book": updated_book}
    raise HTTPException(status_code=404, detail="No book with the provided id")


# Delete the book by id
@app.delete('/books/{book_id}')
@limiter.limit("3/minute")
def delete_by_id(book_id: int, request: Request, Authorization: str = Header()):
    if Authorization == "Bearer " + exp_token:
        book = next((book for book in books if book.id == book_id), None)
        if book:
            for book in books:
                if book.id == book_id:
                    books.remove(book)
                    return {"message": f"Authorization succesful and book deleted successfully"}
            return {"message": f"Could not delete book"}
        else:
            return {"message": f"Book not found with the provided Id"}
    raise HTTPException(status_code=404, detail="Authorization not succesful")

# scraper endpoint
@app.post("/scraper")
async def web_scraper(url_and_pattern: dict):
    url = url_and_pattern.get("url")
    regex_pattern = url_and_pattern.get("regex_pattern")

    if not url or not regex_pattern:
        raise HTTPException(status_code=400, detail="Both 'url' and 'regex_pattern' are required.")

    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        matches = re.findall(regex_pattern, content)
        print(matches)
        return {"matches": matches}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
