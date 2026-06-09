from fastapi import FastAPI, Request
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Database connection string
DATABASE_URL = "mysql+pymysql://root:@localhost/usersdatabase"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------- USERS TABLE ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    mobile = Column(String(15))

# ---------------- REGISTERED USERS TABLE ----------------
class RegisteredUser(Base):
    __tablename__ = "registered_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(100))
    password = Column(String(100))

# Try to create tables, but don't fail if database is not accessible
try:
    Base.metadata.create_all(engine)
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"⚠ Warning: Could not create database tables: {e}")
    print("Make sure MySQL is running and credentials are correct.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------- REGISTER ----------------
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    session = Session()

    check = session.query(RegisteredUser).filter_by(username=data["username"]).first()
    if check:
        session.close()
        return JSONResponse(content={"msg": "User already exists"}, status_code=400)

    obj = RegisteredUser(
        username=data["username"],
        email=data["email"],
        password=data["password"]
    )
    session.add(obj)
    session.commit()
    session.close()

    return JSONResponse(content={"msg": "Registered Successfully"}, status_code=200)

# ---------------- LOGIN ----------------
@app.post("/login")
async def login(request: Request):
    data = await request.json()
    # Here sqlalchemy session starts
    session = Session() 

    user = session.query(RegisteredUser).filter_by(
        username=data["username"],
        password=data["password"]
    ).first()
    # Here sqlalchemy session stops
    session.close()

    if user:
        return JSONResponse(content={"msg": "Login Successful"}, status_code=200)
    else:
        return JSONResponse(content={"msg": "Invalid Username or Password"}, status_code=401)

# ---------------- CREATE ----------------
@app.post("/add_users")
async def add(request: Request):
    data = await request.json()
    session = Session()
    obj = User(name=data["name"], mobile=data["mobile"])
    session.add(obj)
    session.commit()
    session.close()
    return JSONResponse(content={"msg": "added"})

# ---------------- READ ----------------
@app.get("/all")
def get_all():
    session = Session()
    rows = session.query(User).all()
    session.close()
    return [{"id": r.id, "name": r.name, "mobile": r.mobile} for r in rows]

# ---------------- UPDATE ----------------
@app.put("/update/{id}")
async def update(id: int, request: Request):
    data = await request.json()
    session = Session()
    obj = session.query(User).filter_by(id=id).first()

    obj.name = data.get("name", obj.name)
    obj.mobile = data.get("mobile", obj.mobile)

    session.commit()
    session.close()
    return JSONResponse(content={"msg": "updated"})

# ---------------- DELETE ----------------
@app.delete("/delete/{id}")
def delete(id: int):
    session = Session()
    obj = session.query(User).filter_by(id=id).first()
    session.delete(obj)
    session.commit()
    session.close()
    return JSONResponse(content={"msg": "deleted"})

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"msg": "FastAPI CRUD is running successfully"}
