# ==========================================
# IMPORTS
# ==========================================

# importing the main fastapi stuff
from fastapi import FastAPI, Depends, HTTPException 
# FastAPI is the core framework
# Depends is for injecting stuff like db sessions or auth checks
# HTTPException is how we throw proper error codes (404, 401, etc.)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# this just tells FastAPI to look for the Bearer token in the request headers

# sqlalchemy stuff for the database ORM
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum
# create_engine connects us to the mysql db
# Column, Integer, String etc define our table columns and types
# ForeignKey links tables together (like property to user)
# Enum restricts a column to specific allowed values

from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
# declarative_base is the base class all our db models inherit from
# sessionmaker creates the db sessions
# Session is just for type hinting
# relationship handles the links between tables in python

# pydantic for data validation
from pydantic import BaseModel, EmailStr
# BaseModel is for our request/response schemas
# EmailStr automatically validates if an email is actually formatted correctly

# typing stuff for type hints
from typing import Optional, Literal, List
# Optional means the field isn't required
# Literal locks a string down to exact choices (like "admin" or "user")
# List means we're expecting an array of items

# security imports
from passlib.context import CryptContext
# using passlib to hash passwords securely

from jose import jwt, JWTError
# jose for creating and decoding JWT tokens
# JWTError is what gets thrown if a token is bad or expired

from datetime import datetime, timedelta
# datetime for current time, timedelta to add time (like token expiry)

import enum
# standard python enum library


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

# db connection string for mysql
DATABASE_URL = "mysql+pymysql://root:root123@localhost:3306/realestate_db"

# setting up the engine to connect to the db
engine = create_engine(DATABASE_URL)

# sessionmaker creates our db sessions
SessionLocal = sessionmaker(bind=engine)

# base class for all our sqlalchemy models
Base = declarative_base()

# dependency to get a db session. 
# fastapi runs this before the route, yields the session, then closes it when done
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # make sure we close the connection so we don't leak it


# ==========================================
# JWT & SECURITY CONFIG
# ==========================================

# jwt config
# TODO: change this secret key before deploying to production!
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # tokens expire after 30 mins

# setting up bearer token auth so swagger ui gets the authorize button
security = HTTPBearer()

# setting up password hashing with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# helper to hash a plain text password
def hash_password(password):
    return pwd_context.hash(password)

# helper to verify a password against the hash
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================
# ENUMS (locking down allowed values)
# ==========================================

# defining enums so we don't get random invalid strings in the db
class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    COMMERCIAL = "commercial"
    LAND = "land"
    OFFICE = "office"

class PropertyStatus(str, enum.Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RENTED = "rented"
    PENDING = "pending"

class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"

class InquiryStatus(str, enum.Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    CLOSED = "closed"


# ==========================================
# DATABASE MODELS (The Tables)
# ==========================================

# --- USERS TABLE ---
class User(Base):
    __tablename__ = "users"

    # columns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False) # 255 to fit the long bcrypt hash
    role = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=True)
    profile_image = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # relationships (these don't create actual columns, just links for sqlalchemy)
    properties = relationship("Property", back_populates="owner")
    favorites = relationship("Favorite", back_populates="user")
    inquiries = relationship("Inquiry", back_populates="user")
    reviews = relationship("Review", back_populates="user")

# --- PROPERTIES TABLE ---
class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True) # Text for long descriptions
    price = Column(Float, nullable=False)
    listing_type = Column(Enum(ListingType), nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    area_sqft = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    is_furnished = Column(Boolean, default=False)
    
    # linking this to the users table
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # relationships
    owner = relationship("User", back_populates="properties")
    
    # cascade means if we delete the property, all its images/reviews get wiped out too automatically
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    amenities = relationship("PropertyAmenity", back_populates="property", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="property", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="property", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="property", cascade="all, delete-orphan")

# --- PROPERTY IMAGES TABLE ---
class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(500), nullable=False) # just storing the url, not the actual image file
    image_order = Column(Integer, default=0) # for sorting the gallery
    is_primary = Column(Boolean, default=False) # marks the main cover photo
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    property = relationship("Property", back_populates="images")

# --- AMENITIES TABLE ---
class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    icon_url = Column(String(500), nullable=True)
    
    properties = relationship("PropertyAmenity", back_populates="amenity")

# --- PROPERTY AMENITIES (Junction Table) ---
# properties can have many amenities, and amenities can belong to many properties
# so we need this many-to-many junction table to link them up
class PropertyAmenity(Base):
    __tablename__ = "property_amenities"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    amenity_id = Column(Integer, ForeignKey("amenities.id"), nullable=False)
    
    property = relationship("Property", back_populates="amenities")
    amenity = relationship("Amenity", back_populates="properties")

# --- FAVORITES TABLE ---
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")

# --- INQUIRIES TABLE ---
class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    phone = Column(String(20), nullable=True)
    status = Column(Enum(InquiryStatus), default=InquiryStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="inquiries")
    property = relationship("Property", back_populates="inquiries")

# --- REVIEWS TABLE ---
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    rating = Column(Integer, nullable=False) # 1 to 5 stars
    title = Column(String(200), nullable=True)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reviews")
    property = relationship("Property", back_populates="reviews")

# this actually creates all the tables in the db if they don't already exist
Base.metadata.create_all(bind=engine)


# ==========================================
# FASTAPI APP
# ==========================================

# initializing the fastapi app
app = FastAPI(
    title="Real Estate Management API",
    description="Complete backend API for a real estate platform"
)


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

# pydantic schemas for validating incoming json. 
# if the client sends bad data, fastapi auto-rejects it with a 422 error

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["admin", "user"]
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSelfUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "user"]] = None
    phone: Optional[str] = None

# --- Property Schemas ---
class PropertyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    listing_type: Literal["sale", "rent"]
    property_type: Literal["apartment", "house", "villa", "commercial", "land", "office"]
    address: str
    city: str
    state: str
    country: str
    zip_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    year_built: Optional[int] = None
    parking_spaces: Optional[int] = None
    is_furnished: Optional[bool] = False
    amenity_ids: Optional[List[int]] = [] # expecting a list of ids like [1, 3, 5]

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    listing_type: Optional[Literal["sale", "rent"]] = None
    property_type: Optional[Literal["apartment", "house", "villa", "commercial", "land", "office"]] = None
    status: Optional[Literal["available", "sold", "rented", "pending"]] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    year_built: Optional[int] = None
    parking_spaces: Optional[int] = None
    is_furnished: Optional[bool] = None
    amenity_ids: Optional[List[int]] = None

class PropertyImageCreate(BaseModel):
    image_url: str
    image_order: Optional[int] = 0
    is_primary: Optional[bool] = False

class AmenityCreate(BaseModel):
    name: str
    icon_url: Optional[str] = None

class InquiryCreate(BaseModel):
    property_id: int
    subject: Optional[str] = None
    message: str
    phone: Optional[str] = None

class InquiryUpdate(BaseModel):
    status: Optional[Literal["pending", "responded", "closed"]] = None

class ReviewCreate(BaseModel):
    property_id: int
    rating: int
    title: Optional[str] = None
    comment: str


# ==========================================
# HELPER FUNCTIONS (JWT & Auth)
# ==========================================

# creates the jwt token when a user logs in
def create_access_token(data: dict):
    payload = data.copy()

    # setting the expiry time (now + 30 mins)
    payload["exp"] = (
        datetime.utcnow() +
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # encoding the payload into the actual token string
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

# dependency to check if user is logged in. runs before protected routes
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security) # fastapi grabs the bearer token automatically
):
    token = credentials.credentials
    try:
        # decoding the token to get the user data back
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        # if token is bad or expired, kick them out with 401
        raise HTTPException(
            status_code=401,
            detail="Invalid or Expired Token"
        )

# dependency to make sure the logged in user is actually an admin
def admin_required(
    current_user: dict = Depends(get_current_user) # relies on the get_current_user dependency above
):
    if current_user["role"] != "admin":
        # 403 means they are logged in but don't have permission
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


# ==========================================
# AUTH ROUTES
# ==========================================

@app.post("/register", tags=["Auth"])
def register(
    user: UserRegister, # fastapi validates the incoming json against this schema
    db: Session = Depends(get_db) # injecting the db session
):
    # checking if email is already taken
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # creating the user object. hashing the password before saving!
    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
        phone=user.phone
    )
    db.add(new_user)      # staging it
    db.commit()           # actually saving to mysql
    db.refresh(new_user)  # refreshing to get the auto-generated id
    
    return {"message": "User Registered Successfully"}

@app.post("/login", tags=["Auth"])
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    # finding the user by email
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid Email")

    # checking if the password matches the hash
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid Password")

    # all good, generating the token
    token = create_access_token({
        "user_id": db_user.id,
        "email": db_user.email,
        "role": db_user.role
    })
    
    return {
        "message": "Login Successful",
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role
    }


# ==========================================
# ADMIN ROUTES
# ==========================================

@app.get("/users", tags=["Admin"])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required) # only admins can hit this
):
    return db.query(User).all()

@app.put("/admin/users/{user_id}", tags=["Admin"])
def admin_update_user(
    user_id: int, # grabbed from the url path
    updates: AdminUserUpdate, # the json body with fields to update
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    # fetching the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    # safety check so admins can't mess with other admins
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot update another admin")

    # only updating fields that were actually sent in the request
    if updates.name: user.name = updates.name
    if updates.email: user.email = updates.email
    if updates.role: user.role = updates.role
    if updates.phone is not None: user.phone = updates.phone

    db.commit()
    db.refresh(user)
    return {"message": "User Updated Successfully", "data": user}

@app.delete("/users/{user_id}", tags=["Admin"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot delete another admin")

    db.delete(user)
    db.commit()
    return {"message": "User Deleted Successfully"}


# ==========================================
# AMENITY ROUTES
# ==========================================

@app.post("/amenities", tags=["Amenities"])
def create_amenity(
    amenity: AmenityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required) # only admins can add amenities
):
    existing = db.query(Amenity).filter(Amenity.name == amenity.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Amenity already exists")
    
    new_amenity = Amenity(name=amenity.name, icon_url=amenity.icon_url)
    db.add(new_amenity)
    db.commit()
    db.refresh(new_amenity)
    return {"message": "Amenity Created Successfully", "data": new_amenity}

@app.get("/amenities", tags=["Amenities"])
def get_all_amenities(db: Session = Depends(get_db)):
    # anyone can view the amenities list, no auth required
    return db.query(Amenity).all()

@app.delete("/amenities/{amenity_id}", tags=["Amenities"])
def delete_amenity(
    amenity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    amenity = db.query(Amenity).filter(Amenity.id == amenity_id).first()
    if not amenity:
        raise HTTPException(status_code=404, detail="Amenity Not Found")
    
    db.delete(amenity)
    db.commit()
    return {"message": "Amenity Deleted Successfully"}


# ==========================================
# PROPERTY ROUTES
# ==========================================

@app.post("/properties", tags=["Properties"])
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # must be logged in to list a place
):
    # creating the property. auto-assigning the logged in user as the owner
    new_property = Property(
        title=property_data.title,
        description=property_data.description,
        price=property_data.price,
        listing_type=property_data.listing_type,
        property_type=property_data.property_type,
        address=property_data.address,
        city=property_data.city,
        state=property_data.state,
        country=property_data.country,
        zip_code=property_data.zip_code,
        bedrooms=property_data.bedrooms,
        bathrooms=property_data.bathrooms,
        area_sqft=property_data.area_sqft,
        year_built=property_data.year_built,
        parking_spaces=property_data.parking_spaces,
        is_furnished=property_data.is_furnished,
        owner_id=current_user["user_id"] 
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    # if they selected amenities, link them in the junction table
    if property_data.amenity_ids:
        for amenity_id in property_data.amenity_ids:
            property_amenity = PropertyAmenity(
                property_id=new_property.id,
                amenity_id=amenity_id
            )
            db.add(property_amenity)
        db.commit()
    
    return {"message": "Property Created Successfully", "data": new_property}

@app.get("/properties", tags=["Properties"])
def get_all_properties(
    db: Session = Depends(get_db),
    # these are query params for filtering (e.g. /properties?city=NewYork&min_price=100000)
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    listing_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None
):
    query = db.query(Property)
    
    # dynamically adding filters if the user provided query params
    if city:
        # ilike makes it case-insensitive, % means "contains"
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if listing_type:
        query = query.filter(Property.listing_type == listing_type)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bedrooms is not None:
        query = query.filter(Property.bedrooms >= bedrooms)
        
    return query.all()

@app.get("/properties/{property_id}", tags=["Properties"])
def get_property(property_id: int, db: Session = Depends(get_db)):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    return property

@app.put("/properties/{property_id}", tags=["Properties"])
def update_property(
    property_id: int,
    updates: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    # auth check: only the owner or an admin can update
    if property.owner_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    # updating fields if they were sent in the request
    if updates.title: property.title = updates.title
    if updates.description is not None: property.description = updates.description
    if updates.price is not None: property.price = updates.price
    if updates.listing_type: property.listing_type = updates.listing_type
    if updates.property_type: property.property_type = updates.property_type
    if updates.status: property.status = updates.status
    if updates.address: property.address = updates.address
    if updates.city: property.city = updates.city
    if updates.state: property.state = updates.state
    if updates.country: property.country = updates.country
    if updates.zip_code is not None: property.zip_code = updates.zip_code
    if updates.bedrooms is not None: property.bedrooms = updates.bedrooms
    if updates.bathrooms is not None: property.bathrooms = updates.bathrooms
    if updates.area_sqft is not None: property.area_sqft = updates.area_sqft
    if updates.year_built is not None: property.year_built = updates.year_built
    if updates.parking_spaces is not None: property.parking_spaces = updates.parking_spaces
    if updates.is_furnished is not None: property.is_furnished = updates.is_furnished
    
    # if they sent new amenity ids, we need to update the junction table
    if updates.amenity_ids is not None:
        # wipe out the old links first
        db.query(PropertyAmenity).filter(PropertyAmenity.property_id == property_id).delete()
        # then add the new ones
        for amenity_id in updates.amenity_ids:
            property_amenity = PropertyAmenity(property_id=property_id, amenity_id=amenity_id)
            db.add(property_amenity)
    
    db.commit()
    db.refresh(property)
    return {"message": "Property Updated Successfully", "data": property}

@app.delete("/properties/{property_id}", tags=["Properties"])
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    # auth check: only owner or admin can delete
    if property.owner_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")
    
    db.delete(property) # cascade will auto-delete images/reviews
    db.commit()
    return {"message": "Property Deleted Successfully"}


# ==========================================
# PROPERTY IMAGE ROUTES
# ==========================================

@app.post("/properties/{property_id}/images", tags=["Property Images"])
def add_property_image(
    property_id: int,
    image_data: PropertyImageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    if property.owner_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to add images to this property")
    
    new_image = PropertyImage(
        image_url=image_data.image_url,
        image_order=image_data.image_order,
        is_primary=image_data.is_primary,
        property_id=property_id
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return {"message": "Image Added Successfully", "data": new_image}

@app.get("/properties/{property_id}/images", tags=["Property Images"])
def get_property_images(property_id: int, db: Session = Depends(get_db)):
    # fetching images and sorting them by the order column
    images = db.query(PropertyImage).filter(PropertyImage.property_id == property_id).order_by(PropertyImage.image_order).all()
    return images

@app.delete("/properties/{property_id}/images/{image_id}", tags=["Property Images"])
def delete_property_image(
    property_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image Not Found")
    
    property = db.query(Property).filter(Property.id == property_id).first()
    if property.owner_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete images from this property")
    
    db.delete(image)
    db.commit()
    return {"message": "Image Deleted Successfully"}


# ==========================================
# FAVORITE ROUTES
# ==========================================

@app.post("/favorites/{property_id}", tags=["Favorites"])
def add_favorite(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    # making sure they don't favorite the same property twice
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user["user_id"],
        Favorite.property_id == property_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Property already in favorites")
    
    new_favorite = Favorite(
        user_id=current_user["user_id"],
        property_id=property_id
    )
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return {"message": "Property Added to Favorites", "data": new_favorite}

@app.get("/favorites", tags=["Favorites"])
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # getting all favorite records for the logged in user
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user["user_id"]).all()
    # returning just the property objects, not the junction table records
    return [fav.property for fav in favorites]

@app.delete("/favorites/{property_id}", tags=["Favorites"])
def remove_favorite(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user["user_id"],
        Favorite.property_id == property_id
    ).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite Not Found")
    
    db.delete(favorite)
    db.commit()
    return {"message": "Property Removed from Favorites"}


# ==========================================
# INQUIRY ROUTES
# ==========================================

@app.post("/inquiries", tags=["Inquiries"])
def create_inquiry(
    inquiry: InquiryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == inquiry.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    new_inquiry = Inquiry(
        user_id=current_user["user_id"],
        property_id=inquiry.property_id,
        subject=inquiry.subject,
        message=inquiry.message,
        phone=inquiry.phone
    )
    db.add(new_inquiry)
    db.commit()
    db.refresh(new_inquiry)
    return {"message": "Inquiry Sent Successfully", "data": new_inquiry}

@app.get("/inquiries", tags=["Inquiries"])
def get_my_inquiries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # if admin, they see everything. otherwise just inquiries for properties they own
    if current_user["role"] == "admin":
        return db.query(Inquiry).all()
    else:
        inquiries = db.query(Inquiry).join(Property).filter(Property.owner_id == current_user["user_id"]).all()
        return inquiries

@app.get("/inquiries/sent", tags=["Inquiries"])
def get_sent_inquiries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # returns inquiries that the logged-in user SENT to other property owners
    inquiries = db.query(Inquiry).filter(Inquiry.user_id == current_user["user_id"]).all()
    return inquiries

@app.put("/inquiries/{inquiry_id}", tags=["Inquiries"])
def update_inquiry_status(
    inquiry_id: int,
    updates: InquiryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry Not Found")
    
    # only the property owner or an admin can change the status (like marking it responded)
    property = db.query(Property).filter(Property.id == inquiry.property_id).first()
    if current_user["role"] != "admin" and property.owner_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this inquiry")
    
    if updates.status:
        inquiry.status = updates.status
    
    db.commit()
    db.refresh(inquiry)
    return {"message": "Inquiry Updated Successfully", "data": inquiry}


# ==========================================
# REVIEW ROUTES
# ==========================================

@app.post("/reviews", tags=["Reviews"])
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    property = db.query(Property).filter(Property.id == review.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property Not Found")
    
    # gotta make sure rating is 1-5
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # preventing users from spamming reviews on the same property
    existing = db.query(Review).filter(
        Review.user_id == current_user["user_id"],
        Review.property_id == review.property_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this property")
    
    new_review = Review(
        user_id=current_user["user_id"],
        property_id=review.property_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return {"message": "Review Posted Successfully", "data": new_review}

@app.get("/properties/{property_id}/reviews", tags=["Reviews"])
def get_property_reviews(property_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.property_id == property_id).all()
    return reviews

@app.delete("/reviews/{review_id}", tags=["Reviews"])
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review Not Found")
    
    # only the person who wrote it (or an admin) can delete it
    if review.user_id != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    
    db.delete(review)
    db.commit()
    return {"message": "Review Deleted Successfully"}


# ==========================================
# USER ROUTES
# ==========================================

@app.get("/users/{user_id}", tags=["User"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # auth check: you can only view your own profile unless you're an admin
    if (
        current_user["role"] != "admin"
        and current_user["user_id"] != user_id
    ):
        raise HTTPException(status_code=403, detail="Access Denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    return user

@app.put("/users/me", tags=["User"])
def update_my_profile(
    updates: UserSelfUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # fetching the logged in user's db record
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    # updating fields. notice they CANNOT update their own role here!
    if updates.name: user.name = updates.name
    if updates.email: user.email = updates.email
    if updates.phone is not None: user.phone = updates.phone
    if updates.profile_image is not None: user.profile_image = updates.profile_image

    db.commit()
    db.refresh(user)
    return {"message": "Profile Updated Successfully", "data": user}


# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():
    # just a simple health check route to make sure the server is alive
    return {
        "message": "Real Estate Management API Running Successfully",
        "version": "1.0.0",
        "tables": [
            "users", "properties", "property_images", "amenities", 
            "property_amenities", "favorites", "inquiries", "reviews"
        ]
    }