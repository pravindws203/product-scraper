from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from mysql_db import MySQLDB
from logger_config import setup_logger


logger = setup_logger("DATABASE API", "databse_api.log")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify a list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class IDRequest(BaseModel):
    id: int =  Field(True, description="ID of the product")
    
class BarcodeRequest(BaseModel):
    id: int = Field(True, description="ID of the product")
    barcode: str = Field(True, description="Barcode of the product")


class ProductInfoRequest(BaseModel):
  id: int = Field(..., description="ID of the product")
  brand_name: Optional[str] = Field(None, description="Brand name")
  barcode: Optional[str] = Field(None, description="Barcode of the product")
  ingredients_main_ocr: Optional[str] = Field(None, description="Ingredients of the product")
  nutrients_main_ocr: Optional[str] = Field(None, description="Nutrients of the product")
  allergen_information: Optional[str] = Field(None, description="Allergen information")

class ImageRequest(BaseModel):
  id: int = Field(True, description="ID of the product")
  front_img: str = Field(True, description="Image URL of the product")
  back_img: str = Field(True, description="Image URL of the product")
  nutrients_img: str = Field(True, description="Image URL of the product")
  ingredients_img: str = Field(True, description="Image URL of the product")

@app.post("/insert")
async def insert_data(request: Request):
  """Insert data into the database."""
  try:
    data = await request.json()
    if not data:
      logger.error("No JSON body provided")
      raise HTTPException(status_code=422, detail="JSON body is required")
    
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    inserted_id = db.insert_data("scrapped_data", data)
    if not inserted_id:
      logger.error("Failed to insert data into the database")
      raise HTTPException(status_code=500, detail="Failed to insert data into the database")
    logger.info(f"Data inserted successfully with ID: {inserted_id}")
    return {"id": inserted_id, "message": "Data inserted successfully", "success": True}
  
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=400, detail="Invalid JSON") from e


@app.post("/insert-url")
async def insert_url(request: Request):
  """Insert data into the database."""
  try:
    data = await request.json()
    if not data:
      logger.error("No JSON body provided")
      raise HTTPException(status_code=422, detail="JSON body is required")
    
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    inserted_id = db.insert_data("products_urls", data)
    if not inserted_id:
      logger.error("Failed to insert data into the database")
      raise HTTPException(status_code=500, detail="Failed to insert data into the database")
    logger.info(f"Data inserted successfully with ID: {inserted_id}")
    return {"id": inserted_id, "message": "Data inserted successfully", "success": True}
  
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=400, detail="Invalid JSON") from e


@app.get("/get-urls")
async def products_urls():
  """Truncate a table in the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db._execute_query(
      f"SELECT id,url FROM products_urls ",
      ['id','url']
    )
    urls = []
    
    if not result:
      raise HTTPException(status_code=404, detail="Not found")
    
    logger.info(f"Successfully fetched{len(urls)} URLs")
    return {"urls": result}
  
  except HTTPException:
    raise
  except Exception as e:
    logger.exception(f"Error while truncating table: {e}")
    raise HTTPException(status_code=400, detail="Invalid table name or database error")


@app.get("/get-url")
async def products_url():
  """Truncate a table in the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db._execute_query(
      f"SELECT id, url FROM products_urls limit 1 ",
      ['id', 'url']
    )
    urls = []
    
    if not result:
      raise HTTPException(status_code=404, detail="Not found")
    
    logger.info(f"Successfully fetched{len(urls)} URLs")
    return {"urls": result}
  
  except HTTPException:
    raise
  except Exception as e:
    logger.exception(f"Error while truncating table: {e}")
    raise HTTPException(status_code=400, detail="Invalid table name or database error")
  
@app.get("/truncate-table/{table_name}")
async def truncate_table(table_name: str):
  """Truncate a table in the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    
    success = db._execute_non_select_query(f"TRUNCATE TABLE {table_name}")
    if not success:
      logger.error(f"Failed to truncate table: {table_name}")
      raise HTTPException(status_code=500, detail="Failed to truncate table")
    
    logger.info(f"Table '{table_name}' truncated successfully")
    return {"message": f"Table '{table_name}' truncated successfully", "success": True}
  
  except HTTPException:
    raise
  except Exception as e:
    logger.exception(f"Error while truncating table: {e}")
    raise HTTPException(status_code=400, detail="Invalid table name or database error")
  
@app.get("/delete-url")
async def delete_url_by_id(request: IDRequest):
  """Truncate a table in the database."""
  try:
    id = request.id
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    
    success = db._execute_non_select_query(f"DELETE FROM products_urls WHERE id = {id}")
    if not success:
      logger.error(f"Failed to truncate table: {id}")
      raise HTTPException(status_code=500, detail="Failed to truncate table")
    
    logger.info(f"Delete '{id}' Data successfully")
    return {"message": f"Delete '{id}' Data successfully", "success": True}
  
  except HTTPException:
    raise
  except Exception as e:
    logger.exception(f"Error while delete Data table: {e}")
    raise HTTPException(status_code=400, detail="Invalid table name or database error")
    
@app.post("/images")
async def get_all_images(request: IDRequest):
    """Insert data into the database."""
    try:
        id = request.id
        db = MySQLDB(
            host="localhost",
            user="root",
            password="Admin@123",
            database="Product_Webscrapping"
        )
        result = db._execute_query(
            f"SELECT images, other_images FROM scrapped_data WHERE id = {id}",
            ['images', 'other_images']
        )
        main_images = []
        other_images = []
        
        if not result:
            raise HTTPException(status_code=404, detail="ID not found")
        
        
        for item in result:
            if item.get('images') != "" and item.get('images') is not None:
              images = json.loads(item.get('images'))
              main_images = images.get("image_urls", [])
            
            if item.get('other_images') != "" and item.get('other_images') is not None:
              other = json.loads(item.get('other_images'))
              images = other.get("image_urls", {}).get("images", {})
              other_images = images.get("image_urls", [])
        
        logger.info(f"Successfully fetched images for ID: {id}")
        return {"main_images": main_images, "other_images": other_images}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON") from e


@app.post("/data")
async def get_all_data(request: IDRequest):
  """Insert data into the database."""
  try:
    id = request.id
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db._execute_query(
      f"SELECT barcode, variant_id, name, product_url, brand_name, diet, mass_measurement_unit, net_weight, source, mrp, ingredients_main_ocr, nutrients_main_ocr, allergen_information, images, other_images , front_img, back_img, nutrients_img, ingredients_img, status FROM scrapped_data WHERE id = {id}",
      ['barcode', 'variant_id', 'name', 'product_url', 'brand_name', 'diet', 'mass_measurement_unit', 'net_weight', 'source', '	mrp', 'ingredients_main_ocr', 'nutrients_main_ocr', 'allergen_information', 'images', 'other_images', 'front_img', 'back_img', 'nutrients_img', 'ingredients_img', 'status']
    )
    main_images = []
    other_images = []
    
    if not result:
      raise HTTPException(status_code=404, detail="ID not found")
    
    for item in result:
      if item.get('images') != "" and item.get('images') is not None:
        images = json.loads(item.get('images'))
        item['images'] = images.get("image_urls", [])
      
      if item.get('other_images') != "" and item.get('other_images') is not None:
        other = json.loads(item.get('other_images'))
        images = other.get("image_urls", {}).get("images", {})
        item['other_images'] = images.get("image_urls", [])
        
      return item
  
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=400, detail="Invalid JSON") from e


@app.post("/barcode")
async def update_barcode(request: BarcodeRequest):
    """Insert data into the database."""
    try:
      id = request.id
      barcode = request.barcode
      db = MySQLDB(
          host="localhost",
          user="root",
          password="Admin@123",
          database="Product_Webscrapping"
      )
      result = db.update_data("scrapped_data", {"barcode": barcode, "barcode_exists": 1}, f"id = {id}")
      
      if result == 0:
        raise HTTPException(status_code=404, detail="ID not found")
      
      logger.info(f"Successfully updated barcode for ID: {id}")
      return {"message": "Barcode updated successfully", "id": id, "barcode": barcode}
    
    except HTTPException:
      logger.error("Failed to update barcode")
      raise
    except Exception as e:
      logger.error("Failed to update barcode")
      raise HTTPException(status_code=400, detail="Invalid JSON") from e
    
@app.get("/barcodeids")
async def get_all_ids():
  """Retrieve all IDs with 'raw' status from the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db._execute_query(
      "SELECT id FROM scrapped_data WHERE barcode_exists = 0 and is_uploaded = 0 and id > 7000",
      ['id']
    )
    id_list = [item['id'] for item in result]
    return {"id": id_list}
  
  except Exception as e:
    raise HTTPException(status_code=400, detail="Database error") from e

@app.get("/rawids")
async def get_all_raw_ids():
  """Retrieve all IDs with 'raw' status from the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
  
    result = db._execute_query(
      "SELECT id FROM scrapped_data WHERE status = 'raw' and is_uploaded = 0 and id > 7000",
      ['id']
    )
    if not result:
      raise HTTPException(status_code=404, detail="No IDs found")
    
    logger.info("Fetching all status: raw IDs")
    id_list = [item['id'] for item in result]
    return {"id": id_list}
  
  except Exception as e:
    logger.error(f"Error occurred while fetching IDs: {e}")
    raise HTTPException(status_code=400, detail="Database error") from e


@app.get("/imageprocessedids")
async def get_all_imageprocessed_ids():
  """Retrieve all IDs with 'imageprocessed' status from the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    
    result = db._execute_query(
      "SELECT id FROM scrapped_data WHERE status = 'imageprocessed' and is_uploaded = 0 and id > 3000",
      ['id']
    )
    if not result:
      raise HTTPException(status_code=404, detail="No IDs found")
    
    logger.info("Fetching all status: imageprocessed IDs")
    id_list = [item['id'] for item in result]
    return {"id": id_list}
  
  except Exception as e:
    logger.error(f"Error occurred while fetching IDs: {e}")
    raise HTTPException(status_code=400, detail="Database error") from e


@app.get("/added")
async def get_all_is_uploaded_id(request: IDRequest):
  """Retrieve all IDs with 'imageprocessed' status from the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    
    update_fields = {'is_uploaded': True}
    
    result = db.update_data("scrapped_data", update_fields, f"id = {request.id}")
    
    if result == 0:
      return {"message": "Failed to update product info", "id": request.id, "success": False}
    
    logger.info(f"Successfully updated product info for ID: {request.id}")
    return {"message": "Product info updated successfully", "id": request.id, "success": True}
  
  except Exception as e:
    logger.error(f"Error occurred while fetching IDs: {e}")
    raise HTTPException(status_code=400, detail="Database error") from e
  
@app.get("/producturl")
async def get_product_urls():
  """Insert data into the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db._execute_query(
      f"SELECT product_url FROM `scrapped_data` WHERE `name` IS NULL ORDER BY `id` ASC",
      ['product_url']
    )
    if not result:
      return {"message": "ID not found", "success": False}
    
    product_urls = [item['product_url'] for item in result]
    return product_urls
  except HTTPException as http_exc:
    logger.error(f"HTTP error occurred: {http_exc.detail}")
    raise
  except Exception as e:
    logger.error(f"Failed to fetch product info: {str(e)}")
    raise HTTPException(status_code=400, detail="Invalid JSON") from e

@app.post("/productinfo/update")
async def update_product_info(request: ProductInfoRequest):
    """Insert data into the database."""
    try:
        db = MySQLDB(
            host="localhost",
            user="root",
            password="Admin@123",
            database="Product_Webscrapping"
        )

        update_fields = {}

        if request.brand_name:
          update_fields["brand_name"] = request.brand_name
        if request.barcode:
          update_fields["barcode"] = request.barcode
          update_fields["barcode_exists"] = 1
        if request.ingredients_main_ocr:
          update_fields["ingredients_main_ocr"] = request.ingredients_main_ocr
        if request.nutrients_main_ocr:
          update_fields["nutrients_main_ocr"] = request.nutrients_main_ocr
        if request.allergen_information:
          update_fields["allergen_information"] = request.allergen_information

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        result = db.update_data("scrapped_data", update_fields, f"id = {request.id}")

        if result == 0:
            return {"message": "Failed to update product info", "id": request.id, "success": False}

        logger.info(f"Successfully updated product info for ID: {request.id}")
        return {"message": "Product info updated successfully", "id": request.id, "success": True}
    except HTTPException as http_exc:
        logger.error(f"HTTP error occurred: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Failed to update product info: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON") from e


@app.get("/delete")
async def delete_product(id: int = Query(..., description="ID of the product to delete")):
  """Delete product data from the database by ID."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    result = db.delete_data(id)
    
    if not result:
      raise HTTPException(status_code=404, detail="ID not found")
    
    logger.info(f"Successfully deleted product for ID: {id}")
    return {
      "message": f"Successfully deleted product for ID: {id}",
      "status": "success"
    }
  
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=400, detail=f"Error occurred: {e}") from e
    
    
@app.post("/image/update")
async def update_images(request: ImageRequest):
  """Insert data into the database."""
  try:
    db = MySQLDB(
      host="localhost",
      user="root",
      password="Admin@123",
      database="Product_Webscrapping"
    )
    
    id = request.id
    front_img = request.front_img
    back_img = request.back_img
    nutrients_img = request.nutrients_img
    ingredients_img = request.ingredients_img
    result = db.update_data(
      "scrapped_data", {
        "front_img": front_img,
        "back_img": back_img,
        "nutrients_img": nutrients_img,
        "ingredients_img": ingredients_img,
        "status": "imageprocessed"
      }, f"id = {id}"
    )
    
    if result == 0:
      return {"message": "Failed to update images", "id": id, "success": False}
    
    logger.info(f"Successfully updated images for ID: {id}")
    return {"message": "Images updated successfully", "id": id, "success": True}
  
  except HTTPException as http_exc:
    logger.error(f"HTTP error occurred: {http_exc.detail}")
    raise
  except Exception as e:
    logger.error(f"Failed to update images: {str(e)}")
    raise HTTPException(status_code=400, detail="Invalid JSON") from e
  
@app.get("/")
async def root():
  """Root endpoint"""
  return {
    "message": "Welcome to the Database API",
    "status": "running",
    "version": "1.0.0",
    "description": "This API provides endpoints to interact with the database.",
    "endpoints": {
      "/insert": "Insert data into the database",
      "/images": "Get images for a given ID",
      "/barcode": "Update barcode for a given ID",
      "/barcodeids": "Get all IDs with 'raw' status",
      "/rawids": "Get all IDs with 'raw' status",
      "/image/update": "Update images for a given ID",
      "/producturl": "Get product info for a given ID",
      "/productinfo/update": "Update product info for a given ID",
    }
  }
@app.get("/health")
async def health_check():
  """Health check endpoint"""
  return {
    "status": "healthy",
    "message": "The API is running smoothly."
  }

@app.get("/docs")
async def get_docs():
  """API documentation"""
  return {
    "message": "API documentation",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
  }


if __name__ == "__main__":
  uvicorn.run(app, host="10.0.101.153", port=10000)