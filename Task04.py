from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ---------------- 1. DATABASE SETUP ----------------
# Update with your actual MySQL credentials if different
DATABASE_URL = "mysql+pymysql://root:root@123/realestate_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Dependency to get DB session safely (Prevents connection leaks!)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- 2. DATABASE MODELS ----------------
class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    agency_name = Column(String(100))

    # Relationship: One agent has many properties
    properties = relationship("Property", back_populates="agent", cascade="all, delete-orphan")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    address = Column(String(255), nullable=False)
    property_type = Column(String(50)) # e.g., "Apartment", "House", "Commercial"
    price = Column(Float, nullable=False)
    bedrooms = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    
    # Foreign Key linking to Agent
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    
    # Relationship: This property belongs to one agent
    agent = relationship("Agent", back_populates="properties")

# Create tables in MySQL
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Real Estate Database tables created successfully!")
except Exception as e:
    print(f"⚠ Warning: Could not create database tables: {e}")

# ---------------- 3. FASTAPI APP ----------------
app = FastAPI(title="Real Estate Management API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to ["http://localhost:3000"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- 4. PYDANTIC SCHEMAS (Validation) ----------------
class AgentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    agency_name: Optional[str] = None

class PropertyCreate(BaseModel):
    title: str
    address: str
    property_type: str
    price: float
    bedrooms: int = 0
    agent_id: int

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    is_available: Optional[bool] = None

# ---------------- 5. ENDPOINTS ----------------

# --- AGENT ROUTES ---
@app.post("/agents", status_code=201)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = Agent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return {"msg": "Agent added successfully", "data": db_agent}

@app.get("/agents")
def get_all_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()


# --- PROPERTY ROUTES ---
@app.post("/properties", status_code=201)
def create_property(property: PropertyCreate, db: Session = Depends(get_db)):
    # 1. Verify agent exists before creating property
    agent = db.query(Agent).filter(Agent.id == property.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 2. Create property
    db_property = Property(**property.model_dump())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return {"msg": "Property listed successfully", "data": db_property}

@app.get("/properties")
def get_properties(
    is_available: Optional[bool] = Query(None, description="Filter by availability (true/false)"),
    property_type: Optional[str] = Query(None, description="Filter by type (e.g., Apartment)"),
    max_price: Optional[float] = Query(None, description="Maximum budget"),
    db: Session = Depends(get_db)
):
    """
    Advanced Filtering Endpoint! 
    Example: /properties?is_available=true&property_type=House&max_price=500000
    """
    query = db.query(Property)
    
    if is_available is not None:
        query = query.filter(Property.is_available == is_available)
    if property_type:
        query = query.filter(Property.property_type.ilike(f"%{property_type}%"))
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
        
    return query.all()

@app.get("/properties/{property_id}")
def get_property_details(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj

@app.put("/properties/{property_id}")
def update_property(property_id: int, updates: PropertyUpdate, db: Session = Depends(get_db)):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Update only the fields that were provided in the request
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(property_obj, key, value)
        
    db.commit()
    db.refresh(property_obj)
    return {"msg": "Property updated successfully", "data": property_obj}

@app.patch("/properties/{property_id}/toggle-availability")
def toggle_availability(property_id: int, db: Session = Depends(get_db)):
    """Business Logic: Quickly mark a property as sold/rented or available again"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    property_obj.is_available = not property_obj.is_available
    db.commit()
    db.refresh(property_obj)
    
    status = "Available" if property_obj.is_available else "Unavailable (Sold/Rented)"
    return {"msg": f"Property is now {status}", "data": property_obj}

@app.delete("/properties/{property_id}")
def delete_property(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    db.delete(property_obj)
    db.commit()
    return {"msg": "Property listing removed successfully"}

@app.get("/")
def home():
    return {"msg": "Real Estate API is running! Visit /docs to test endpoints."}